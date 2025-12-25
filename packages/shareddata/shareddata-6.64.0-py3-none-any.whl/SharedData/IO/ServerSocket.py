
import time
import sys
import socket
import threading
import time
import select
import numpy as np
import pandas as pd
import json
import os
from cryptography.fernet import Fernet
import lz4.frame as lz4f
import struct

from SharedData.Logger import Logger
from SharedData.IO.SyncTable import SyncTable

#TODO: DONT SERVE DATA IF TABLE IS NOT IN MEMORY
class ServerSocket():
    
    # Dict to keep track of all connected client sockets
    """
    ServerSocket class manages a multithreaded TCP server that accepts client connections, authenticates them using a token, and facilitates data synchronization through subscription or publishing actions.
    
    Attributes:
        clients (dict): Thread-safe dictionary tracking connected client sockets and their metadata.
        lock (threading.Lock): Lock to synchronize access to the clients dictionary.
        server (socket.socket): The server socket instance.
        shdata: Shared data reference used for synchronization.
        accept_clients (threading.Thread): Thread handling incoming client connections.
    
    Methods:
        runserver(shdata, host, port):
            Initializes the server socket, sets socket options, and starts the client acceptance thread.
    
        accept_clients_thread(host, port):
            Binds the server socket to the specified host and port, listens for incoming connections, and spawns a new thread to handle each client.
    
        handle_client_thread(conn, addr):
            Manages an individual client connection, adding it to the clients dictionary, handling communication, and cleaning up on disconnect.
    
        handle_client_socket(client):
            Handles client authentication by decrypting and verifying a token, then initiates synchronization loops based on client action ('subscribe' or 'publish') and container type.
    """
    clients = {}
    # Create a lock to protect access to the clients Dict
    lock = threading.Lock()
    server = None
    shdata = None
    accept_clients = None

    @staticmethod
    def runserver(shdata, host, port):

        """
        Starts the server by initializing shared data, creating a TCP socket, and launching a thread to accept client connections.
        
        Parameters:
            shdata (any): Shared data to be used by the SyncTable.
            host (str): The hostname or IP address on which the server will listen.
            port (int): The port number on which the server will listen.
        
        This method sets up the server socket with the SO_REUSEADDR option to allow address reuse,
        assigns the shared data to SyncTable, and starts a new thread to handle incoming client connections.
        """
        SyncTable.shdata = shdata

        ServerSocket.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # This line allows the address to be reused
        ServerSocket.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Create the server and start accepting clients in a new thread
        ServerSocket.accept_clients = threading.Thread(
            target=ServerSocket.accept_clients_thread, args=(host, port))
        ServerSocket.accept_clients.start()

    @staticmethod
    def accept_clients_thread(host, port):
        """
        Starts a server socket that listens for incoming client connections on the specified host and port.
        For each accepted client connection, a new thread is spawned to handle the client using the `handle_client_thread` method.
        This method runs indefinitely, continuously accepting and processing new client connections.
        
        Args:
            host (str): The hostname or IP address to bind the server socket to.
            port (int): The port number to bind the server socket to.
        """
        ServerSocket.server.bind((host, port))
        ServerSocket.server.listen()

        Logger.log.info(f'Listening on {host}:{port}')

        while True:
            conn, addr = ServerSocket.server.accept()
            threading.Thread(target=ServerSocket.handle_client_thread,
                             args=(conn, addr)).start()

    @staticmethod
    def handle_client_thread(conn, addr):
        """
        Handles a new client connection in a separate thread.
        
        Initializes client-specific data, sets a timeout on the connection,
        and manages the client's lifecycle including authentication status,
        data transfer statistics, and connection cleanup.
        
        Parameters:
            conn (socket.socket): The client socket object.
            addr (tuple): The address of the connected client.
        
        This method logs connection and disconnection events, handles exceptions
        during client communication, and ensures proper resource cleanup.
        """
        Logger.log.debug(f"New client connected: {addr}")
        conn.settimeout(30.0)

        # Add the client socket to the list of connected clients
        with ServerSocket.lock:
            ServerSocket.clients[conn] = {
                'watchdog': time.time_ns(),
                'transfer_rate': 0.0,
                'download': 0,
                'upload': 0,
                'authenticated': False,
            }

        client = ServerSocket.clients[conn]
        client['conn'] = conn
        client['addr'] = addr
                
        try:
            ServerSocket.handle_client_socket(client)
        except Exception as e:
            Logger.log.error(f"Client {addr} disconnected with error: {e}")
        finally:
            with ServerSocket.lock:
                ServerSocket.clients.pop(conn)
            Logger.log.info(f"Client {addr} disconnected.")
            conn.close()

    @staticmethod
    def handle_client_socket(client):
        
        """
        Handles client socket authentication and communication.
        
        Waits up to 5 seconds for the client to send authentication data. It decrypts and verifies the client's token against an environment variable to authenticate the client. Upon successful authentication, initializes the client and manages communication based on the client's requested action and container type.
        
        Parameters:
            client (dict): A dictionary containing client connection information, authentication status, address, and other relevant data.
        
        Raises:
            Exception: If client authentication fails due to an invalid token.
        
        Behavior:
        - Uses non-blocking select to wait for incoming data.
        - Decrypts the received token using Fernet symmetric encryption.
        - Logs authentication success or failure.
        - Initializes client state via SyncTable.
        - If the client subscribes to a 'table' container, enters a publish loop.
        - If the client publishes to a 'table' container, sends metadata and enters a subscription loop.
        """
        conn = client['conn']
        tini = time.time()
        while not client['authenticated']:
            # Check if there is data ready to be read from the client
            ready_to_read, _, _ = select.select([conn], [], [], 0)
            if not ready_to_read:
                if time.time()-tini > 5:
                    break
                time.sleep(0.001)                
            else:
                # Receive data from the client
                data = conn.recv(1024)
                if not data:
                    break
                else:
                    # clear watchdog
                    client['watchdog'] = time.time_ns()                    
                    
                    login_msg = json.loads(data.decode())
                    client.update(login_msg)

                    # authenticate
                    key = os.environ['SHAREDDATA_SECRET_KEY'].encode()
                    token = os.environ['SHAREDDATA_TOKEN']
                    cipher_suite = Fernet(key)
                    received_token = cipher_suite.decrypt(login_msg['token'].encode())
                    if received_token.decode() != token:
                        errmsg = 'Client %s authentication failed!' % (client['addr'][0])
                        Logger.log.error(errmsg)
                        raise Exception(errmsg)
                    else:
                        client['authenticated'] = True
                        Logger.log.info('Client %s authenticated' % (client['addr'][0]))
                                                
                        client = SyncTable.init_client(client)
                        if client['action'] == 'subscribe':
                            if client['container'] == 'table':
                                SyncTable.socket_publish_loop(client)
                        elif client['action'] == 'publish':
                            if client['container'] == 'table':
                                # reply with mtime and count
                                responsemsg = {
                                    'mtime': float(client['records'].mtime),
                                    'count': int(client['records'].count),
                                }
                                conn.sendall(json.dumps(responsemsg).encode())

                                SyncTable.socket_subscription_loop(client)


if __name__ == '__main__':

    from SharedData.Logger import Logger
    from SharedData.SharedData import SharedData
    shdata = SharedData('SharedData.IO.ServerSocket', user='master')

    if len(sys.argv) >= 2:
        _argv = sys.argv[1:]
    else:
        errmsg = 'Please specify IP and port to bind!'
        Logger.log.error(errmsg)
        raise Exception(errmsg)
    
    args = _argv[0].split(',')
    host = args[0]
    port = int(args[1])    
        
    ServerSocket.runserver(shdata, host, port)
    
    Logger.log.info('ROUTINE STARTED!')

    lasttotalupload = 0
    lasttotaldownload = 0
    lasttime = time.time()
    while True:        
        # Create a list of keys before entering the loop
        client_keys = list(ServerSocket.clients.keys())
        nclients = 0
        totalupload = 0
        totaldownload = 0
        for client_key in client_keys:
            nclients = nclients+1
            c = ServerSocket.clients.get(client_key)
            if c is not None:
                if 'upload' in c:
                    totalupload += c['upload']
                if 'download' in c:
                    totaldownload += c['download']
        te = time.time()-lasttime
        lasttime = time.time()
        download = (totaldownload-lasttotaldownload)/te
        upload = (totalupload-lasttotalupload)/te
        lasttotaldownload = totaldownload
        lasttotalupload = totalupload        

        Logger.log.debug('#heartbeat#host:%s,port:%i,clients:%i,download:%.2fMB/s,upload:%.2fMB/s' \
                         % (host, port, nclients, download/1024, upload/1024))
        time.sleep(15)