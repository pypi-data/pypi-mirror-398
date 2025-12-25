import time
import sys
import socket
import numpy as np
import pandas as pd
import json
import os
from cryptography.fernet import Fernet
import lz4.frame as lz4f
import struct

from SharedData.Logger import Logger
from SharedData.IO.SyncTable import SyncTable


class ClientSocket():
    """
    Provides static methods to manage persistent socket connections for subscribing to and publishing data tables.
    
    Methods:
    - subscribe_table_thread(table, host, port, lookbacklines=1000, lookbackdate=None, snapshot=False, bandwidth=1e6):
        Continuously attempts to connect to a server and subscribe to updates for a specified table.
        Handles reconnection on failure with logging and delay.
    
    - publish_table_thread(table, host, port, lookbacklines=1000, lookbackdate=None, snapshot=False, bandwidth=1e6):
        Continuously attempts to connect to a server and publish updates for a specified table.
        Compares remote and local table metadata to log warnings if remote data is newer or has more records.
        Handles reconnection on failure with logging and delay.
    
    Parameters common to both methods:
    - table: The table object to subscribe to or publish.
    - host: The server hostname or IP address.
    - port: The server port number.
    - lookbacklines: Number of historical lines to request initially (default 1000).
    - lookbackdate: Optional date to limit historical data requested.
    - snapshot: Whether to request a snapshot of the table (default False).
    - bandwidth: Bandwidth limit for the connection (default 1e6
    """
    @staticmethod
    def subscribe_table_thread(table, host, port, 
        lookbacklines=1000, lookbackdate=None, snapshot=False, bandwidth=1e6):
        
        """
        Continuously subscribes to updates from a specified data table on a given host and port.
        
        This static method establishes a TCP connection to the specified server, sends a subscription request
        for the given table with optional parameters for historical data and snapshot retrieval, and processes
        incoming data in a loop. If the connection or subscription fails, it logs a warning and retries after a delay.
        
        Parameters:
            table (object): The table object to subscribe to, containing metadata such as database, period, source, and tablename.
            host (str): The hostname or IP address of the server to connect to.
            port (int): The port number on the server to connect to.
            lookbacklines (int, optional): Number of historical lines to request upon subscription. Defaults to 1000.
            lookbackdate (str or None, optional): Date string specifying the starting point for historical data. Defaults to None.
            snapshot (bool, optional): Whether to request a snapshot of the current table state. Defaults to False.
            bandwidth (float, optional): Bandwidth limit for the subscription in bytes per second. Defaults to 1e6.
        
        The method runs indefinitely, handling reconnections and resubscriptions automatically in case of errors.
        """
        while True:
            try:
                # Connect to the server
                client_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((host, port))

                # Send the subscription message
                msg = SyncTable.subscribe_table_message(
                    table, lookbacklines, lookbackdate, snapshot, bandwidth)
                msgb = msg.encode('utf-8')
                bytes_sent = client_socket.send(msgb)
                
                # Subscription loop
                client = json.loads(msg)
                client['conn'] = client_socket                
                client['addr'] = (host, port) 
                client = SyncTable.init_client(client,table)
                SyncTable.socket_subscription_loop(client)
                time.sleep(15)

            except Exception as e:
                msg = 'Retrying subscription %s,%s,%s,table,%s!\n%s' % \
                    (table.database, table.period,
                     table.source, table.tablename, str(e))
                Logger.log.warning(msg)
                time.sleep(15)

    @staticmethod
    def publish_table_thread(table, host, port, 
        lookbacklines=1000, lookbackdate=None, snapshot=False, bandwidth=1e6):
        
        """
        '''
        Continuously subscribes to updates from a specified table and publishes them to a remote server.
        
        This static method establishes a persistent TCP connection to the given host and port, sends a subscription
        request based on the provided table and parameters, and listens for updates. It compares the remote data's
        modification time and record count with the local table, logging warnings if the remote data is newer or has
        more records. The method handles connection interruptions and exceptions by retrying the subscription after a delay.
        
        Parameters:
            table (object): The table object containing database, period, source, tablename, and records metadata.
            host (str): The hostname or IP address of the server to connect to.
            port (int): The port number of the server to connect to.
            lookbacklines (int, optional): Number of lines to look back for historical data. Defaults to 1000.
            lookbackdate (str or None, optional): Specific date to look back to for historical data. Defaults to None.
            snapshot (bool, optional): Whether to request a snapshot of the table. Defaults to False.
            bandwidth (float, optional): Bandwidth limit for the subscription in bytes per second. Defaults to 1e6.
        
        This method runs indefinitely until
        """
        while True:
            try:
                # Connect to the server
                client_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((host, port))

                # Send the subscription message
                msg = SyncTable.publish_table_message(
                    table, lookbacklines, lookbackdate, snapshot, bandwidth)
                msgb = msg.encode('utf-8')
                client_socket.sendall(msgb)

                response = client_socket.recv(1024)
                if response == b'':
                    msg = 'Subscription %s,%s,%s,table,%s closed on response!' % \
                        (table.database, table.period,
                            table.source, table.tablename)
                    Logger.log.error(msg)
                    client_socket.close()
                    break
                response = json.loads(response)
                if response['mtime'] > table.records.mtime:
                    Logger.log.warning('Remote %s is newer!' % table.relpath)
                
                if response['count'] > table.records.count:
                    Logger.log.warning('Remote %s has more records!' % table.relpath)
                                       

                # Subscription loop
                client = json.loads(msg)
                client['conn'] = client_socket                
                client['addr'] = (host, port) 
                client = SyncTable.init_client(client,table)
                client.update(response)
                
                SyncTable.socket_publish_loop(client)
                time.sleep(15)

            except Exception as e:
                msg = 'Retrying subscription %s,%s,%s,table,%s!\n%s' % \
                    (table.database, table.period,
                     table.source, table.tablename, str(e))
                Logger.log.warning(msg)
                time.sleep(15)
    


if __name__ == '__main__':
    import sys
    from SharedData.Logger import Logger
    from SharedData.SharedData import SharedData
    shdata = SharedData('SharedData.IO.ClientSocket', user='master')

    if len(sys.argv) >= 2:
        _argv = sys.argv[1:]
    else:
        msg = 'Please specify IP and port to bind!'
        Logger.log.error(msg)
        raise Exception(msg)

    args = _argv[0].split(',')
    host = args[0]
    port = int(args[1])
    database = args[2]
    period = args[3]
    source = args[4]
    tablename = args[5]
    if len(args) > 6:
        pubsub = int(args[6])
    
    table = shdata.table(database, period, source, tablename)
    if pubsub == 'publish':
        table.publish(host, port)
    elif pubsub == 'subscribe':
        table.subscribe(host, port)

    while True:
        time.sleep(1)        