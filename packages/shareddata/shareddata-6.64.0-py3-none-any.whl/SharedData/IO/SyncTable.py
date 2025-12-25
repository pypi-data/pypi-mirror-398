import time
import sys
import socket
import numpy as np
import pandas as pd
import json
import os
from cryptography.fernet import Fernet
import lz4.frame as lz4f
import asyncio
import struct
from aiohttp import web

from SharedData.Logger import Logger


class SyncTable():

    """
    Class SyncTable provides methods to synchronize tabular data between clients and servers using socket or websocket connections. It supports publishing and subscribing to updates of shared tables with efficient data transfer, compression, and rate limiting.
    
    Key functionalities include:
    - Initializing client state for synchronization with metadata and lookback parameters.
    - Determining which record IDs need to be sent based on updates and snapshots.
    - Creating publish and subscribe messages with authentication tokens and synchronization parameters.
    - Running continuous loops to publish updates or receive subscriptions over sockets or websockets, handling compression, decompression, and flow control.
    - Utility method to reliably receive a specified number of bytes from a socket.
    
    This class is designed to work with shared data tables that expose record arrays with timestamps and indexing, enabling incremental synchronization of data changes in real-time or near real-time environments.
    """
    shdata = None

    BUFF_SIZE = int(128 * 1024)

    @staticmethod
    def recvall(sock, n):
        # Helper function to recv n bytes or return None if EOF is hit
        """
        Receive exactly n bytes from the given socket.
        
        This static method attempts to read n bytes from the socket `sock`. It repeatedly calls `recv` until either
        n bytes have been received or the connection is closed (EOF). If the connection is closed before n bytes
        are received, it returns None.
        
        Args:
            sock (socket.socket): The socket object to receive data from.
            n (int): The exact number of bytes to receive.
        
        Returns:
            bytearray or None: A bytearray containing the received bytes if successful, or None if EOF is reached before n bytes are received.
        """
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data
    
    @staticmethod
    def init_client(client,table=None):

        """
        Initializes and configures the given client dictionary with synchronization table data and related metadata.
        
        Parameters:
            client (dict): A dictionary representing the client state and configuration.
            table (optional): An optional SyncTable object to use instead of creating a new one.
        
        Returns:
            dict: The updated client dictionary with initialized synchronization attributes.
        
        This method sets up the client's table and records references, initializes upload/download counters,
        handles snapshot state, and configures lookback indices and timestamps based on the client's metadata.
        It also calculates the maximum number of rows for buffering and records the last message time.
        """
        if table is None:
            client['records'] = SyncTable.shdata.table(client['database'], client['period'],
                                                    client['source'], client['tablename'])        
            client['table'] = client['records'].table
        else:
            client['table'] = table
            client['records'] = table.records
            
        client['hasindex'] = client['table'].hasindex
        client['upload'] = 0
        client['download'] = 0
        if not 'snapshot' in client:
            client['snapshot'] = False

        count = client['records'].count.copy()
        if client['hasindex']:
            # mtime update check
            if isinstance(client['mtime'], float):
                client['mtime'] = pd.Timestamp.utcfromtimestamp(float(client['mtime'])).tz_localize(None)

            # loockback from line or date
            client['lookbackfromid'] = None
            if 'lookbackdate' in client:
                loc = client['records'].get_date_loc_gte(pd.Timestamp(client['lookbackdate']))
                if len(loc) > 0:
                    client['lookbackfromid'] = min(loc)
                else:
                    client['lookbackfromid'] = count

            if client['lookbackfromid'] is not None:
                client['lookbackid'] = client['lookbackfromid']
            else:
                client['lookbackid'] = count - int(client['lookbacklines'])
            
            if client['lookbackid'] < 0:
                client['lookbackid'] = 0
            
            client['lastsenttimesize'] = client['records'].size - client['lookbackid']
            client['lastsentimestartrow'] = client['lookbackid']
            client['lastsenttime'] = np.full((client['lastsenttimesize'],),
                                   fill_value=client['mtime'], dtype='datetime64[ns]')
                    
        client['maxrows'] = int(
                np.floor(SyncTable.BUFF_SIZE/client['records'].itemsize))
                        
        client['lastmsgtime'] = time.time()

        return client
    
    # PUBLISH
    @staticmethod
    def get_ids2send(client):
        """
        '''
        Determine which record IDs need to be sent based on updates and new entries in the client's records.
        
        This method checks for updated records by comparing modification times (mtime) within a specified lookback window,
        and also identifies any new records added since the last known count. It updates the client's state accordingly,
        including timestamps and counts, and handles snapshot update flags.
        
        Parameters:
            client (dict): A dictionary representing the client's state and records, containing keys:
                - 'count' (int): The last known count of records sent.
                - 'hasindex' (bool): Whether the client has an index for update checks.
                - 'lookbackfromid' (int or None): Optional starting ID for lookback updates.
                - 'records' (object): An object with a 'count' attribute and indexable records containing 'mtime' timestamps.
                - 'lookbacklines' (int): Number of lines to look back for updates.
                - 'lastsentimestartrow' (int): Offset for last sent time tracking.
                - 'lastsenttime' (array-like): Array of timestamps for last sent messages.
                - 'snapshot' (bool): Flag indicating if a snapshot update is required.
                - 'lastmsgtime' (float):
        """
        ids2send = []
                
        lastcount = client['count']

        if client['hasindex']:
            # mtime update check                    
            if client['lookbackfromid'] is not None:
                lookbackid = client['lookbackfromid']
            else:
                lookbackid = client['records'].count- client['lookbacklines']                
            if lookbackid < 0:
                lookbackid = 0

            tblcount = client['records'].count.copy()
            if tblcount>lookbackid:    
                client['lookbackid'] = lookbackid
            else:
                client['lookbackid'] = 0
                        
            lastsenttimestartid = lookbackid - client['lastsentimestartrow']
            lastsenttimeendid = tblcount - client['lastsentimestartrow']

            currmtime = client['records'][lookbackid:tblcount]['mtime'].copy()
            updtidx = currmtime > client['lastsenttime'][lastsenttimestartid:lastsenttimeendid]
            if updtidx.any():
                updtids = np.where(updtidx)
                if len(updtids) > 0:
                    ids2send.extend(updtids[0]+lookbackid)
                    client['lastsenttime'][lastsenttimestartid:lastsenttimeendid] = currmtime
                                    
            if client['snapshot']:
                client['snapshot'] = False
                lastcount = lookbackid

        # count update check
        curcount = client['records'].count.copy()
        if curcount > lastcount:
            newids = np.arange(lastcount, curcount)
            ids2send.extend(newids)
            client['count'] = curcount

        if len(ids2send) > 0:
            client['lastmsgtime'] = time.time() # reset lastmsgtime
            ids2send = np.unique(ids2send)
            ids2send = np.sort(ids2send)
        
        return client, ids2send

    @staticmethod
    def publish_table_message(table, lookbacklines, lookbackdate, snapshot, bandwidth):
        """
        Generate a JSON-formatted message for publishing table data with authentication and metadata.
        
        Parameters:
        - table: An object representing the table, containing attributes such as user, database, period, source, tablename, and records (with count and mtime).
        - lookbacklines: Integer specifying the number of lines to look back in the data.
        - lookbackdate: A pandas Timestamp object indicating the date to look back to; if provided, it is formatted as 'YYYY-MM-DD' in the message.
        - snapshot: Boolean flag indicating whether the message is for a snapshot.
        - bandwidth: Bandwidth information to include in the message.
        
        Returns:
        - A JSON string containing the user token, action type, table metadata, record counts, timestamps, and additional parameters for publishing.
        """
        shnumpy = table.records        
                        
        msg = {
            'user':table.user,
            'token': os.environ['SHAREDDATA_TOKEN'],
            'action': 'publish',
            'database': table.database,
            'period': table.period,
            'source': table.source,
            'container': 'table',
            'tablename': table.tablename,
            'count': int(shnumpy.count),
            'mtime': float(shnumpy.mtime),
            'lookbacklines': lookbacklines,
            'bandwidth': bandwidth
        }
        if isinstance(lookbackdate, pd.Timestamp):            
            msg['lookbackdate'] = lookbackdate.strftime('%Y-%m-%d')
        if snapshot:
            msg['snapshot'] = True
        msg = json.dumps(msg)
        return msg
    
    @staticmethod
    def socket_publish_loop(client):
        
        """
        Continuously publishes updates from a client's records over a socket connection.
        
        This static method manages the sending of data updates for a given client by:
        - Retrieving the IDs of records to send.
        - Compressing and sending the records in chunks, respecting bandwidth limits.
        - Sending periodic heartbeat messages to keep the connection alive.
        - Updating transfer statistics such as transfer rate and total bytes uploaded.
        - Handling disconnections and errors gracefully by logging and retrying.
        
        Parameters:
            client (dict): A dictionary containing client-specific information including:
                - 'database', 'period', 'source', 'tablename': identifiers for the data source.
                - 'addr': client address tuple.
                - 'conn': socket connection object.
                - 'records': data records to send.
                - 'maxrows': maximum number of rows to send per message.
                - 'bandwidth': bandwidth limit in bytes per second.
                - 'lastmsgtime': timestamp of the last sent message.
                - 'watchdog': timestamp for monitoring activity.
                - 'transfer_rate': current transfer rate in MB/s (updated).
                - 'upload': total bytes uploaded (updated).
        
        The method runs indefinitely until an exception occurs, at which point it logs the error and exits.
        """
        Logger.log.info('Publishing updates of %s/%s/%s/%s -> %s' %
                        (client['database'], client['period'],
                         client['source'], client['tablename'], client['addr'][0]))
        
        conn = client['conn']
        records = client['records']        
        while True:
            try:
                client, ids2send = SyncTable.get_ids2send(client)
                
                if len(ids2send) > 0:
                    rows2send = len(ids2send)
                    sentrows = 0         
                    msgsize = min(client['maxrows'], rows2send)
                    bandwidth = client['bandwidth']
                    tini = time.time_ns()
                    bytessent = 0
                    while sentrows < rows2send:
                        t = time.time_ns()
                        message = records[ids2send[sentrows:sentrows + msgsize]].tobytes()
                        compressed = lz4f.compress(message)
                        msgbytes = len(compressed)
                        bytessent+=msgbytes+4                        
                        msgmintime = msgbytes/bandwidth
                        length = struct.pack('!I', len(compressed))
                        conn.sendall(length+compressed)
                        sentrows += msgsize
                        msgtime = (time.time_ns()-t)*1e-9
                        ratelimtime = max(msgmintime-msgtime,0)
                        if ratelimtime > 0:
                            time.sleep(ratelimtime)

                    totalsize = (sentrows*records.itemsize)/1e6
                    totaltime = (time.time_ns()-tini)*1e-9
                    transfer_rate = totalsize/totaltime                                            
                    client['transfer_rate'] = transfer_rate
                    client['upload'] += bytessent

                if time.time()-client['lastmsgtime'] > 15:
                    # send heartbeat
                    conn.sendall(b'ping')
                    client['lastmsgtime'] = time.time()

                # clear watchdog
                client['watchdog'] = time.time_ns()
                time.sleep(0.001)
            except Exception as e:
                Logger.log.error(
                    'Client %s disconnected with error:%s' % (client['addr'], e))
                time.sleep(5)
                break
    
    @staticmethod
    async def websocket_publish_loop(client):
        """
        Asynchronously publishes updates from a client's data records over an aiohttp websocket connection in a continuous loop.
        
        This coroutine continuously checks for new data record IDs to send to the client, compresses the data using LZ4,
        and sends it in chunks over the websocket connection while respecting the client's bandwidth limitations.
        It updates the client's transfer statistics and handles disconnections or errors gracefully by logging and retrying.
        
        Args:
            client (dict): A dictionary containing client-specific information including:
                - 'conn': The aiohttp websocket connection object.
                - 'records': The data records to be sent.
                - 'database', 'period', 'source', 'tablename': Metadata for logging.
                - 'addr': Client address tuple.
                - 'maxrows': Maximum number of rows to send per message.
                - 'bandwidth': Bandwidth limit in bytes per second.
                - 'upload': Total bytes uploaded.
                - 'transfer_rate': Current transfer rate in MB/s.
                - 'watchdog': Timestamp of last successful send.
        
        Raises:
            None explicitly; exceptions are caught and logged, causing the loop to break on errors.
        """
        Logger.log.info('Publishing updates of %s/%s/%s/%s -> %s' %
                        (client['database'], client['period'],
                        client['source'], client['tablename'], client['addr'][0]))

        conn = client['conn']
        records = client['records']
        while True:
            try:
                client, ids2send = SyncTable.get_ids2send(client)

                if len(ids2send) > 0:
                    rows2send = len(ids2send)
                    sentrows = 0
                    msgsize = min(client['maxrows'], rows2send)
                    bandwidth = client['bandwidth']
                    tini = time.time_ns()
                    bytessent = 0
                    while sentrows < rows2send:
                        t = time.time_ns()
                        message = records[ids2send[sentrows:sentrows + msgsize]].tobytes()
                        compressed = lz4f.compress(message)
                        msgbytes = len(compressed)
                        bytessent += msgbytes
                        msgmintime = msgbytes / bandwidth

                        await conn.send_bytes(compressed)   # <---- aiohttp send

                        sentrows += msgsize
                        msgtime = (time.time_ns() - t) * 1e-9
                        ratelimtime = max(msgmintime - msgtime, 0)
                        if ratelimtime > 0:
                            await asyncio.sleep(ratelimtime)

                    totalsize = (sentrows * records.itemsize) / 1e6
                    totaltime = (time.time_ns() - tini) * 1e-9
                    if totaltime > 0:
                        transfer_rate = totalsize / totaltime
                    else:
                        transfer_rate = 0
                    client['transfer_rate'] = transfer_rate
                    client['upload'] += bytessent

                client['watchdog'] = time.time_ns()
                await asyncio.sleep(0.001)
            except Exception as e:
                Logger.log.error(
                    'Client %s disconnected with error:%s' % (client['addr'], e))
                await asyncio.sleep(5)
                break
        
    # SUBSCRIBE    
    @staticmethod
    def subscribe_table_message(table, lookbacklines, lookbackdate, snapshot, bandwidth):
        """
        Generate a JSON-formatted subscription message for a data table.
        
        This static method constructs a subscription message containing metadata about the specified data table,
        including user credentials, table details, and subscription parameters such as lookback lines, lookback date,
        snapshot request, and bandwidth. The message is serialized as a JSON string suitable for sending to a data service.
        
        Parameters:
            table (object): An object representing the data table, expected to have attributes:
                            'records' (with 'count' and 'mtime'), 'user', 'database', 'period', 'source', and 'tablename'.
            lookbacklines (int): Number of previous lines of data to include in the subscription.
            lookbackdate (pd.Timestamp or other): Optional date to specify the starting point for data lookback.
            snapshot (bool): Flag indicating whether to request a snapshot of the current data.
            bandwidth (int): Bandwidth parameter for the subscription.
        
        Returns:
            str: A JSON string containing the subscription message with user token and relevant metadata.
        """
        shnumpy = table.records        
                        
        msg = {
            'user':table.user,
            'token': os.environ['SHAREDDATA_TOKEN'],
            'action': 'subscribe',
            'database': table.database,
            'period': table.period,
            'source': table.source,
            'container': 'table',
            'tablename': table.tablename,            
            'count': int(shnumpy.count),
            'mtime': float(shnumpy.mtime),
            'lookbacklines': lookbacklines,
            'bandwidth': bandwidth
        }
        if isinstance(lookbackdate, pd.Timestamp):            
            msg['lookbackdate'] = lookbackdate.strftime('%Y-%m-%d')
        if snapshot:
            msg['snapshot'] = True
        msg = json.dumps(msg)
        return msg
    
    @staticmethod
    def socket_subscription_loop(client):

        """
        Continuously receives and processes data from a client's socket subscription.
        
        This static method listens for incoming messages on the client's socket connection associated with a data table subscription. It handles ping messages to update a watchdog timer, receives and decompresses data packets, and feeds the decompressed data into the table's record stream for processing. The method also manages connection closures and logs warnings or errors accordingly.
        
        Args:
            client (dict): A dictionary containing the subscription context, including:
                - 'table': The data table object with attributes like database, period, source, tablename, and a records handler.
                - 'conn': The socket connection object.
                - 'watchdog': Timestamp for the last ping received (updated on 'ping' messages).
                - 'download': Counter for the total bytes downloaded.
        
        Raises:
            Exception: If the connection is closed unexpectedly or data reception fails, the exception is logged and the loop terminates.
        """
        table = client['table']
        records = table.records
        client_socket = client['conn']

        bytes_buffer = bytearray()
        
        while True:
            try:
                # Receive data from the server
                data = SyncTable.recvall(client_socket, 4)                
                if (data == b'') | (data is None):
                    msg = 'Subscription %s,%s,%s,table,%s closed !' % \
                        (table.database, table.period,
                            table.source, table.tablename)
                    Logger.log.warning(msg)
                    client_socket.close()
                elif data==b'ping':
                    client['watchdog'] = time.time_ns()
                else:  
                    length = struct.unpack('!I', data)[0]       
                    client['download'] += length+4
                    compressed = SyncTable.recvall(client_socket, length)
                    if not compressed:
                        msg = 'Subscription %s,%s,%s,table,%s closed !' % \
                        (table.database, table.period,
                            table.source, table.tablename)
                        Logger.log.warning(msg)
                        client_socket.close()
                        raise Exception(msg)

                    data = lz4f.decompress(compressed)
                    bytes_buffer.extend(data)
                    bytes_buffer = records.read_stream(bytes_buffer)

            except Exception as e:
                msg = 'Subscription %s,%s,%s,table,%s error!\n%s' % \
                    (table.database, table.period,
                        table.source, table.tablename, str(e))
                Logger.log.error(msg)
                client_socket.close()                
                break
    
    @staticmethod
    async def websocket_subscription_loop(client):
        """
        Asynchronously manages a continuous WebSocket subscription loop to receive, decompress, and process streaming binary data.
        
        The function listens for incoming WebSocket messages, handles decompression using lz4f, and feeds the decompressed data into a structured numpy-like table for further processing. It also tracks the total amount of downloaded data and handles connection closure and errors gracefully by logging appropriate messages and closing the WebSocket connection.
        
        Parameters:
            client (dict): A dictionary containing:
                - 'conn': The active WebSocket connection object.
                - 'table': An object representing the data table with attributes for database, period, source, tablename, and a 'records' attribute supporting a read_stream method.
                - 'download': An integer counter tracking the total number of bytes downloaded.
        
        The loop continues indefinitely until the WebSocket connection is closed by the server, encounters an error, or an exception occurs.
        """
        
        table = client['table']
        websocket = client['conn']
        shnumpy = table.records
        bytes_buffer = bytearray()

        while True:
            try:
                # Receive data from the server
                msg = await websocket.receive()
                if msg.type == web.WSMsgType.BINARY:
                    data = msg.data
                    if not data:
                        msgstr = f'Subscription {table.database},{table.period},{table.source},table,{table.tablename} closed!'
                        Logger.log.warning(msgstr)
                        await websocket.close()
                        break
                    else:
                        client['download'] += len(data)
                        data = lz4f.decompress(data)
                        bytes_buffer.extend(data)
                        bytes_buffer = shnumpy.read_stream(bytes_buffer)
                elif msg.type in (web.WSMsgType.CLOSE, web.WSMsgType.CLOSING, web.WSMsgType.CLOSED):
                    msgstr = f'Subscription {table.database},{table.period},{table.source},table,{table.tablename} closed by peer!'
                    Logger.log.warning(msgstr)
                    await websocket.close()
                    break
                elif msg.type == web.WSMsgType.ERROR:
                    msgstr = f'Subscription {table.database},{table.period},{table.source},table,{table.tablename} error!\n{websocket.exception()}'
                    Logger.log.error(msgstr)
                    await websocket.close()
                    break
            except Exception as e:
                msgstr = f'Subscription {table.database},{table.period},{table.source},table,{table.tablename} error!\n{str(e)}'
                Logger.log.error(msgstr)
                await websocket.close()
                break


    