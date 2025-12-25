import os
import ssl
import time
import bson
import numpy as np
import pandas as pd
import lz4.frame as lz4f
import asyncio
import struct
import json
import aiohttp
from aiohttp import ClientSession, ClientWebSocketResponse
import asyncio
from typing import Optional, Tuple, AsyncGenerator



from SharedData.Logger import Logger
from SharedData.IO.SyncTable import SyncTable


class ClientWebSocket():

    """
    ClientWebSocket provides asynchronous static methods to manage WebSocket connections for subscribing to and publishing data tables and streams.
    
    Methods:
        get_websocket(endpoint: str) -> tuple[aiohttp.ClientSession, aiohttp.ClientWebSocketResponse]:
            Establishes an aiohttp ClientSession and WebSocket connection using environment proxy and SSL settings.
            The caller is responsible for closing both the session and the websocket connection.
    
        subscribe_table_thread(table, host, port=None, lookbacklines=1000, lookbackdate=None, snapshot=False, bandwidth=1e6, protocol='ws'):
            Continuously attempts to connect to a WebSocket server to subscribe to updates for a specified data table.
            Sends a subscription message and maintains the subscription loop, handling reconnections on errors with a delay.
    
        publish_table_thread(table, host, port=None, lookbacklines=1000, lookbackdate=None, snapshot=False, bandwidth=1e6, protocol='ws'):
            Continuously attempts to connect to a WebSocket server to publish updates from a specified data table.
            Sends a publish message, processes the initial response, and maintains the publishing loop, handling reconnections on errors with a delay.
    
        subscribe_stream(database, period, source, tablename, user='master
    """

    @staticmethod
    async def get_websocket(endpoint: str) -> tuple[aiohttp.ClientSession, ClientWebSocketResponse]:
        """
        Establish an aiohttp ClientSession and WebSocket connection to the specified endpoint, applying SSL and proxy settings from environment variables.
        
        Environment Variables:
        - SHAREDDATA_CAFILE: Path to a CA certificate file for SSL verification.
        - PROXY_ENDPOINT: Proxy server URI.
        - PROXY_USER: Username for proxy authentication.
        - PROXY_PWD: Password for proxy authentication.
        
        Args:
            endpoint (str): The WebSocket URI to connect to.
        
        Returns:
            tuple[aiohttp.ClientSession, aiohttp.ClientWebSocketResponse]: A tuple containing the aiohttp ClientSession and the WebSocket connection.
        
        Note:
            The caller is responsible for closing both the ClientSession and the WebSocket connection.
        """
        ws_kwargs = {}
        cafile = os.getenv('SHAREDDATA_CAFILE')
        if cafile:
            ws_kwargs['ssl'] = ssl.create_default_context(cafile=cafile)
        proxy_endpoint = os.getenv('PROXY_ENDPOINT')
        proxy_user = os.getenv('PROXY_USER')
        proxy_pwd = os.getenv('PROXY_PWD')
        if proxy_user and proxy_pwd and proxy_endpoint:
            proxy_method, proxy_host = proxy_endpoint.split('://')[0], proxy_endpoint.split('://')[1]
            ws_kwargs['proxy'] = f"{proxy_method}://{proxy_user}:{proxy_pwd}@{proxy_host}"
        elif proxy_endpoint:
            ws_kwargs['proxy'] = proxy_endpoint

        session = aiohttp.ClientSession()
        websocket = await session.ws_connect(endpoint, **ws_kwargs)
        return session, websocket

    @staticmethod
    async def subscribe_table_thread(table, host, port=None,
            lookbacklines=1000, lookbackdate=None, snapshot=False, 
            bandwidth=1e6, protocol='ws'):
        """
        '''
        Asynchronously subscribes to a specified data table via a WebSocket connection, managing reconnections and continuous data streaming.
        
        This method establishes a WebSocket connection to the given host and port (if specified) using the specified protocol (default 'ws'). It sends a subscription message to receive updates from the specified table, handling lookback parameters and snapshot options. The method continuously attempts to maintain the subscription, automatically reconnecting and resubscribing in case of connection failures or exceptions.
        
        Parameters:
            table: The data table object to subscribe to, containing attributes like database, period, source, and tablename.
            host (str): The hostname or IP address of the WebSocket server.
            port (int, optional): The port number of the WebSocket server. Defaults to None.
            lookbacklines (int, optional): Number of historical lines to retrieve upon subscription. Defaults to 1000.
            lookbackdate (optional): Date from which to start retrieving historical data. Defaults to None.
            snapshot (bool, optional): Whether to request a snapshot of the current table state. Defaults to False.
            bandwidth (float, optional): Bandwidth limit or parameter for the subscription. Defaults to 1e6.
            protocol (str, optional): Protocol to use
        """
        if port is None:
            websocket_url = f"{protocol}://{host}"
        else:
            websocket_url = f"{protocol}://{host}:{port}"

        while True:
            try:
                session, websocket = await ClientWebSocket.get_websocket(websocket_url)                
                # Send the subscription message as text
                
                msg = SyncTable.subscribe_table_message(
                    table, lookbacklines, lookbackdate, snapshot, bandwidth)
                await websocket.send_str(msg)  # or send_bytes if needed

                # Initialize client for the subscription loop
                client = json.loads(msg)
                client['conn'] = websocket
                client['addr'] = (host, port)
                client = SyncTable.init_client(client, table)

                await SyncTable.websocket_subscription_loop(client)
                # Sleep after normal termination (very rare)
                await asyncio.sleep(15)

            except Exception as e:
                msg = 'Retrying subscription %s,%s,%s,table,%s!\n%s' % \
                    (table.database, table.period,
                    table.source, table.tablename, str(e))
                Logger.log.warning(msg)
            finally:
                if websocket is not None:
                    await websocket.close()
                if session is not None:
                    await session.close()
                Logger.log.info('Websocket closed')
                await asyncio.sleep(15)
    
    @staticmethod
    async def publish_table_thread(table, host, port=None,
            lookbacklines=1000, lookbackdate=None, snapshot=False,
            bandwidth=1e6, protocol='ws'):

        """
        '''
        Asynchronously maintains a persistent WebSocket connection to publish updates from a specified table.
        
        This coroutine continuously attempts to connect to a WebSocket server at the given host and port,
        subscribes to updates for the specified table with optional parameters such as lookback lines,
        lookback date, snapshot mode, and bandwidth limit. Upon successful subscription, it listens for
        incoming messages and processes them in a publish loop. If the connection is lost or an error
        occurs, it logs the issue and retries the subscription after a delay.
        
        Parameters:
            table (Table): The table object containing database, period, source, and tablename attributes.
            host (str): The hostname or IP address of the WebSocket server.
            port (int, optional): The port number of the WebSocket server. Defaults to None.
            lookbacklines (int, optional): Number of historical lines to retrieve on subscription. Default is 1000.
            lookbackdate (str or None, optional): Date string to specify the starting point for historical data. Default is None.
            snapshot (bool, optional): Whether to request a snapshot of the current table state. Default is False.
            bandwidth (float, optional): Bandwidth limit for the subscription in bits per second. Default is
        """
        while True:
            try:                
                
                if port is None:
                    websocket_url = f"{protocol}://{host}"
                else:
                    websocket_url = f"{protocol}://{host}:{port}"
                
                session, websocket = await ClientWebSocket.get_websocket(websocket_url)
                # Send the subscription message
                msg = SyncTable.publish_table_message(
                    table, lookbacklines, lookbackdate, snapshot, bandwidth)                
                await websocket.send_str(msg)
                response = await websocket.receive_json()
                
                # Subscription loop
                client = json.loads(msg)
                client['conn'] = websocket
                client['table'] = table
                client['addr'] = (host, port)
                client.update(response)
                client = SyncTable.init_client(client,table)
                
                await SyncTable.websocket_publish_loop(client)
                await asyncio.sleep(15)

            except Exception as e:
                msg = 'Retrying subscription %s,%s,%s,table,%s!\n%s' % \
                    (table.database, table.period,
                     table.source, table.tablename, str(e))
                Logger.log.warning(msg)
            finally:
                if websocket is not None:
                    await websocket.close()
                if session is not None:
                    await session.close()
                Logger.log.info('Websocket closed')
                await asyncio.sleep(15)
        
    @staticmethod
    async def subscribe_stream(
        database: str,
        period: str,
        source: str,
        tablename: str,
        user: str = 'master',
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
        groupid: Optional[str] = None,
        offset: str = 'latest'
    ) -> AsyncGenerator[dict, None]:
        """
        '''
        Asynchronously subscribes to a streaming data source via a WebSocket connection and yields decoded messages.
        
        This method continuously attempts to connect to the specified WebSocket endpoint, sends a subscription request with the given parameters, and listens for incoming compressed BSON messages. It decompresses and decodes each message, yielding individual data entries as dictionaries. In case of connection errors or exceptions, it logs the error, closes the connection gracefully, waits for 5 seconds, and then retries.
        
        Parameters:
            database (str): The name of the database to subscribe to.
            period (str): The period or timeframe of the data stream.
            source (str): The source identifier of the data stream.
            tablename (str): The table name within the database to subscribe to.
            user (str, optional): The username for authentication. Defaults to 'master'.
            endpoint (Optional[str], optional): The WebSocket endpoint URL. If None, uses the 'SHAREDDATA_WS_ENDPOINT' environment variable.
            token (Optional[str], optional): Authentication token. If None, uses the 'SHAREDDATA_TOKEN' environment variable.
            groupid (Optional[str], optional): Optional group identifier for subscription.
            offset (str, optional): The offset position to start streaming from (
        """
        session = None
        websocket = None

        while True:
            try:
                endpoint_val = endpoint or os.environ['SHAREDDATA_WS_ENDPOINT']
                session, websocket = await ClientWebSocket.get_websocket(endpoint_val)
                login_msg = {
                    'action' : 'subscribe',
                    'container' : 'stream',
                    'database' : database,
                    'period' : period,
                    'source' : source,
                    'tablename' : tablename,
                    'user' : user,
                    'token' : token or os.environ['SHAREDDATA_TOKEN'],
                    'offset' : offset,
                }
                if groupid is not None:
                    login_msg['groupid'] = groupid
                await websocket.send_str(json.dumps(login_msg))

                login_response = await websocket.receive_json()
                if login_response.get('message') != 'login success!':
                    Logger.log.error(f'Failed to subscribe: {login_response}')
                    return

                Logger.log.info(f'Subscribed to stream {database}/{period}/{source}/{tablename}')
                while True:
                    msg = await websocket.receive_bytes()
                    msgdict = bson.BSON.decode(lz4f.decompress(msg))
                    for _msg in msgdict.get('data', []):
                        yield bson.BSON.decode(lz4f.decompress(_msg))

            except Exception as e:
                Logger.log.error(f'subscribe_stream() error: {e}')
                await asyncio.sleep(5)
            finally:
                if websocket:
                    try:
                        await websocket.close()
                    except Exception as e:
                        Logger.log.error(f'Error closing websocket: {e}')
                    finally:
                        websocket = None
                if session:
                    try:
                        await session.close()
                    except Exception as e:
                        Logger.log.error(f'Error closing session: {e}')
                    finally:
                        session = None
                Logger.log.info('Websocket closed')
        
    @staticmethod
    async def publish_stream(
        database: str,
        period: str,
        source: str,
        tablename: str,
        user: str = 'master',
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
    ) -> Tuple[asyncio.Queue, asyncio.Task]:
        """
        Asynchronously publishes dictionaries from an asyncio queue to a websocket stream in batches.
        
        Creates and returns an asyncio.Queue for incoming dictionary messages and a background asyncio.Task that continuously sends these messages to a specified websocket endpoint. Messages are batched up to BATCH_SIZE or sent after a BATCH_TIMEOUT to optimize network usage. The websocket connection is authenticated using provided or environment token credentials.
        
        Parameters:
            database (str): The database name to publish to.
            period (str): The period identifier for the stream.
            source (str): The source identifier for the stream.
            tablename (str): The table name within the database.
            user (str, optional): The username for authentication. Defaults to 'master'.
            endpoint (Optional[str], optional): The websocket endpoint URL. Defaults to environment variable 'SHAREDDATA_WS_ENDPOINT' if None.
            token (Optional[str], optional): The authentication token. Defaults to environment variable 'SHAREDDATA_TOKEN' if None.
        
        Returns:
            Tuple[asyncio.Queue, asyncio.Task]: A tuple containing the asyncio.Queue to which dictionaries can be added for publishing, and the asyncio.Task running the background publishing coroutine.
        """
        
        BATCH_SIZE = 10000
        BATCH_TIMEOUT = 0.02  # seconds
        queue: asyncio.Queue = asyncio.Queue(maxsize=50000)

        async def _worker():
            """
            '''
            Asynchronous worker coroutine that manages a persistent WebSocket connection to publish data batches.
            
            The worker continuously attempts to establish a WebSocket connection to a specified endpoint (defaulting to the environment variable 'SHAREDDATA_WS_ENDPOINT' if not provided). Upon connection, it sends a login message containing authentication and stream details (database, period, source, tablename, user, and token). If login is successful, it enters a loop to collect messages from an asynchronous queue, batching them up to a predefined size or timeout. Each batch is encoded using BSON, compressed with LZ4, and sent over the WebSocket.
            
            The worker handles connection errors, login failures, and message sending exceptions by logging errors and attempting to reconnect after a delay. It also properly closes the WebSocket and session on exit or error. Cancellation is supported to allow graceful shutdown.
            
            Dependencies:
            - ClientWebSocket for connection management
            - asyncio for asynchronous operations and queue management
            - bson for BSON encoding
            - lz4f for compression
            - Logger for logging events and errors
            
            Constants used:
            - BATCH_SIZE: maximum number of messages per batch
            - BATCH_TIMEOUT: maximum wait time to fill a batch
            
            This coroutine is intended to run indefinitely as a background task to publish streaming data reliably
            """
            while True:
                session = websocket = None
                try:
                    session, websocket = await ClientWebSocket.get_websocket(
                        endpoint or os.environ['SHAREDDATA_WS_ENDPOINT']
                    )
                    login_msg = {
                        'action': 'publish',
                        'container': 'stream',
                        'database': database,
                        'period': period,
                        'source': source,
                        'tablename': tablename,
                        'user': user,
                        'token': token or os.environ['SHAREDDATA_TOKEN'],
                    }
                    await websocket.send_str(json.dumps(login_msg))
                    login_response = await websocket.receive_json()
                    if login_response.get('message') != 'login success!':
                        Logger.log.error(f'Failed to login: {login_response}')
                        return
                    Logger.log.info(f'Publishing to stream {database}/{period}/{source}/{tablename}')
                    while True:
                        batch = []
                        msgdict = await queue.get()
                        batch.append(msgdict)
                        for _ in range(BATCH_SIZE - 1):
                            try:
                                msgdict = await asyncio.wait_for(queue.get(), timeout=BATCH_TIMEOUT)
                                batch.append(msgdict)
                            except asyncio.TimeoutError:
                                break
                        try:
                            msg_bytes = bson.BSON.encode({'data': batch})
                            compressed_msg = lz4f.compress(msg_bytes)
                            await websocket.send_bytes(compressed_msg)
                        except Exception as e:
                            Logger.log.error(f'Error sending message batch: {e}')
                            break
                except asyncio.CancelledError:
                    # Allow cancellation to propagate
                    raise
                except Exception as e:
                    Logger.log.error(f'Error in websocket publishing worker: {e}')
                finally:
                    if websocket is not None:
                        await websocket.close()
                    if session is not None:
                        await session.close()
                    Logger.log.info('Websocket closed')
                await asyncio.sleep(15)
        task = asyncio.create_task(_worker())
        return queue, task

if __name__ == '__main__':
    import sys
    import time
    import argparse
    from SharedData.Logger import Logger
    from SharedData.SharedData import SharedData

    parser = argparse.ArgumentParser(
        description="ClientWebSocket command-line utility"
    )
    parser.add_argument("host", help="Host IP to bind")
    parser.add_argument("port", type=int, help="Port to bind")
    parser.add_argument("database", help="Database name")
    parser.add_argument("period", help="Period")
    parser.add_argument("source", help="Source")
    parser.add_argument("tablename", help="Table name")
    parser.add_argument(
        "pubsub", choices=["publish", "subscribe"], 
        help="Choose publish or subscribe"
    )

    args = parser.parse_args()

    shdata = SharedData('SharedData.IO.ClientWebSocket', user='master')
    table = shdata.table(args.database, args.period, args.source, args.tablename)
    if args.pubsub == 'publish':
        table.publish(args.host, args.port)
    elif args.pubsub == 'subscribe':
        table.subscribe(args.host, args.port)

    while True:
        time.sleep(1)