
import asyncio
import time
import math
import bson
import lz4.frame
import sys
from aiohttp import web
import os
import json
import traceback
from gunicorn.app.base import BaseApplication


from SharedData.SharedData import SharedData
shdata = SharedData('SharedData.IO.ServerWebSocket',user='master')
from SharedData.Logger import Logger
from SharedData.IO.SyncTable import SyncTable

MAX_PAYLOAD_SIZE = 64 * 1024         # 64 KB per message to client (stream subscribe)
MAX_INPUT_MSG_SIZE = 512 * 1024      # 512 KB max input for publish

class ServerWebSocket:
    """
    Handles WebSocket connections for a server with per-worker user caching.
    
    Features:
    - Maintains a per-process cache of authenticated users.
    - Manages connected clients with concurrency-safe access.
    - Periodically refreshes user data from a database.
    - Authenticates clients based on tokens and permissions.
    - Supports subscribing to and publishing data streams or tables via WebSocket.
    - Compresses and decompresses messages using lz4 and BSON.
    - Tracks per-client upload and download statistics.
    - Sends periodic heartbeat logs with aggregated client statistics.
    
    Key methods:
    - fetch_users: Refresh user cache from the database.
    - refresh_users_periodically: Continuously update user cache every 60 seconds.
    - check_permissions: Verify if a client has permission for a requested path and method.
    - handle_client_thread: Manage lifecycle of a WebSocket client connection.
    - handle_client_websocket: Authenticate and route client requests for subscribing or publishing.
    - stream_subscribe_loop: Stream data to subscribed clients with batching and compression.
    - stream_publish_loop: Receive and publish client data streams with validation.
    - send_heartbeat: Periodically log upload/download stats for all connected clients.
    """
    BUFF_SIZE = int(128 * 1024)
    def __init__(self, app, shdata):
        # Store per-process cache for users (no global)
        """
        Initialize the instance with application context and shared data.
        
        Sets up asynchronous locks and dictionaries to manage per-process user cache and known clients,
        ensuring thread-safe access within an asynchronous environment.
        
        Parameters:
            app: The application context or main app instance.
            shdata: Shared data accessible to this instance.
        """
        self._users_lock = asyncio.Lock()
        self._users = {}
        # Known clients (per worker)
        self.clients = {}
        self.clients_lock = asyncio.Lock()
        self.shdata = shdata
        self.app = app

    async def fetch_users(self):
        """
        Asynchronously fetches the latest user data from the database and updates the internal user dictionary.
        
        Acquires an asynchronous lock to ensure thread-safe access while querying the 'USERS' collection
        under the specified database path ('Symbols', 'D1', 'AUTH', 'USERS') with user context 'SharedData'.
        Retrieves all user documents, converts them into a dictionary keyed by each user's 'token', and
        stores this dictionary in the instance variable `_users`.
        """
        async with self._users_lock:
            user_collection = self.shdata.collection('Symbols', 'D1', 'AUTH', 'USERS', user='SharedData')
            _users = list(user_collection.find({}))
            self._users = {user['token'] : user for user in _users}
            # Logger.log.info(f"[USERS] Refreshed to {len(self._users)} users.")

    async def refresh_users_periodically(self):
        """
        Periodically refreshes the user data by calling the fetch_users method every 60 seconds.
        
        This asynchronous method runs indefinitely, attempting to update user information. If an exception occurs during the fetch_users call, it logs a warning message but continues running.
        
        Raises:
            None
        """
        while True:
            try:
                await self.fetch_users()
            except Exception as e:
                Logger.log.warning(f"User refresh failed: {e}")
            await asyncio.sleep(60)

    def check_permissions(self, reqpath, permissions, method):
        """
        Check if the specified HTTP method is permitted for a given request path based on a nested permissions structure.
        
        Parameters:
        - reqpath (list): A list of path segments representing the requested path.
        - permissions (dict): A nested dictionary representing permissions, where keys are path segments or '*' as a wildcard.
        - method (str): The HTTP method (e.g., 'GET', 'POST') to check permission for.
        
        Returns:
        - bool: True if the method is permitted for the path, False otherwise.
        
        The function traverses the permissions dictionary according to the path segments in reqpath.
        At each level, it attempts to match the current segment or a wildcard '*'.
        Permission is granted if the method is found in the permissions list at the final node or if a wildcard '*' is present.
        """
        node = permissions
        for segment in reqpath:
            if segment in node:
                node = node[segment]
            elif '*' in node:
                node = node['*']
            else:
                return False
            if not isinstance(node, dict):
                if '*' in node:
                    return True
                if isinstance(node, list) and method in node:
                    return True
                return False
        if '*' in node:
            return True
        if method in node:
            return True
        return False

    async def handle_client_thread(self, request):
        """
        Handle a new WebSocket client connection.
        
        This coroutine prepares a WebSocket response for the incoming HTTP request,
        registers the client in the internal clients map with initial metadata, and
        then delegates further handling to `handle_client_websocket`. It ensures proper
        cleanup by closing any associated streams, removing the client from the clients
        map, and closing the WebSocket connection upon disconnection or error.
        
        Args:
            request (aiohttp.web.Request): The incoming HTTP request initiating the WebSocket connection.
        
        Returns:
            aiohttp.web.WebSocketResponse: The prepared WebSocket response object.
        """
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        addr = request.remote

        # Add to clients map
        async with self.clients_lock:
            self.clients[ws] = {
                'watchdog': time.time_ns(),
                'transfer_rate': 0.0,
            }
        client = self.clients[ws]
        client['conn'] = ws
        client['addr'] = addr
        try:
            await self.handle_client_websocket(client)
        except Exception as e:
            # Use exception to log full trace and error message
            Logger.log.error(f"Client {addr} exception:\n{''.join(traceback.format_exception(type(e), e, e.__traceback__))}")
        finally:
            if 'stream' in client:
                try:
                    await client['stream'].async_close()
                except Exception:
                    pass
            async with self.clients_lock:
                self.clients.pop(ws, None)
            Logger.log.info(f"Client {addr} disconnected.")
            await ws.close()
        return ws

    async def handle_client_websocket(self, client):
        """
        Handle a WebSocket connection from a client, performing authentication, authorization, and managing subscription or publishing actions.
        
        This coroutine performs the following steps:
        1. Receives and validates a JSON login message containing required fields.
        2. Authenticates the client using a token and retrieves user data.
        3. Checks the client's permissions for the requested action (publish or subscribe) on the specified resource path.
        4. Sends a login success message upon successful authentication and authorization.
        5. Depending on the client's action and container type, initiates the appropriate subscription or publishing loop:
           - For 'subscribe' action:
             - If container is 'table', initializes the client and starts the SyncTable publish loop.
             - If container is 'stream', starts the stream subscription loop.
           - For 'publish' action:
             - If container is 'table', initializes the client, sends metadata about records, and starts the SyncTable subscription loop.
             - If container is 'stream', starts the stream publishing loop.
        
        Raises:
            Exception: If the login message JSON is invalid, required fields are missing, token is unknown, action is unknown, or permission is denied.
            ValueError: If required fields are missing in the login message.
        """
        ws = client['conn']
        client['authenticated'] = False

        # --- LOGIN & AUTH ---
        try:
            login_msg = await ws.receive_json()
        except Exception as e:
            raise Exception("Invalid JSON at login") from e

        required_fields = ['token', 'user', 'database', 'period', 'source', 'container', 'tablename', 'action']
        if not all(field in login_msg for field in required_fields):
            raise ValueError("Missing required fields in login message")
        client['watchdog'] = time.time_ns()

        token = login_msg['token']
        async with self._users_lock:
            user_obj = self._users.get(token)
        if user_obj is None:
            await asyncio.sleep(3)  # Slow down brute force
            errmsg = f'Unknown token {token} authentication failed!'
            Logger.log.error(f"{errmsg} from {client['addr']}")
            await ws.send_json({'message': errmsg})
            raise Exception(errmsg)

        client.update(login_msg)
        client['userdata'] = user_obj

        reqpath = f"{login_msg['user']}/{login_msg['database']}/{login_msg['period']}/{client['source']}/{client['container']}/{login_msg['tablename']}"
        reqpath = reqpath.split('/')
        method = 'POST' if client['action'] == 'publish' else ('GET' if client['action'] == 'subscribe' else '')
        if not method:
            msg = 'Unknown action: %s' % client['action']
            raise Exception(msg)
        if not self.check_permissions(reqpath, user_obj['permissions'], method):
            await asyncio.sleep(3)
            errmsg = f"Client {client['addr']} permission denied!"
            Logger.log.error(errmsg)
            await ws.send_json({'message': errmsg})
            await asyncio.sleep(0)
            raise Exception(errmsg)

        await ws.send_json({'message': 'login success!'})
        Logger.log.info(f"New client connected: {client['userdata'].get('symbol','?')} {client['addr']} {'/'.join(reqpath)}")

        # --- Subscription/Publishing ---
        if client['action'] == 'subscribe':
            if client['container'] == 'table':
                client = SyncTable.init_client(client)
                await SyncTable.websocket_publish_loop(client)
            elif client['container'] == 'stream':
                await self.stream_subscribe_loop(client)
        elif client['action'] == 'publish':
            if client['container'] == 'table':
                client = SyncTable.init_client(client)
                responsemsg = {
                    'mtime': float(client['records'].mtime),
                    'count': int(client['records'].count)
                }
                await ws.send_json(responsemsg)
                await SyncTable.websocket_subscription_loop(client)
            elif client['container'] == 'stream':
                await self.stream_publish_loop(client)

    async def stream_subscribe_loop(self, client):
        """
        Asynchronously subscribes a client's websocket connection to a data stream, continuously polling for new messages and sending them in compressed BSON format.
        
        This coroutine manages message batching for throughput optimization and tracks per-client upload and download byte counts. It expects the client dictionary to contain the following fields:
        - 'conn': a websocket-like connection object supporting async send_bytes and close methods.
        - 'addr': client address for logging.
        - 'database', 'period', 'source', 'tablename': parameters identifying the data stream.
        Optional fields include:
        - 'groupid': consumer group identifier for the stream subscription (defaults to "ws-{addr}").
        - 'offset': starting offset for the stream subscription (defaults to 'latest').
        - 'user': user identifier for stream access (defaults to 'master').
        
        The method subscribes to the stream using aiokafka, then enters a loop where it polls for messages with a 1-second timeout. If messages are received, they are compressed and sent to the client; if no messages arrive, a compressed ping with the current timestamp is sent to prevent busy-waiting.
        
        Handles cancellation and errors gracefully, logging relevant information. Ensures proper cleanup by closing the stream and websocket connection on exit.
        """
        conn = client['conn']
        addr = client['addr']
        client['upload'] = 0
        client['download'] = 0
        groupid = client.get('groupid', f"ws-{addr}")
        offset = client.get('offset', 'latest')
        shdata = self.shdata
        stream = None

        try:
            stream = shdata.stream(
                client['database'], client['period'], client['source'], client['tablename'],
                user=client.get('user', 'master'), use_aiokafka=True, create_if_not_exists=False
            )
            client['stream'] = stream
            await stream.async_subscribe(groupid=groupid, offset=offset)

            while True:
                try:
                    # Timeout pulls after 1s; don't compress
                    msgs = await stream.async_poll(groupid, timeout=1000, max_records=500, decompress=False)
                    if msgs:
                        payload = lz4.frame.compress(bson.BSON.encode({'data': msgs}))
                        client['upload'] += len(payload)
                        await conn.send_bytes(payload)
                    else:
                        # Prevent busy-spin if stream idle
                        payload = lz4.frame.compress(bson.BSON.encode({'ping': time.time_ns()}))
                        client['upload'] += len(payload)
                        await conn.send_bytes(payload)
                        
                except asyncio.CancelledError:
                    Logger.log.info(f"stream_subscribe_loop():{addr} cancelled.")
                    raise
                except Exception as loop_err:
                    Logger.log.warning(f"stream_subscribe_loop():{addr} inner error: {loop_err}")
                    break
        except Exception as e:
            Logger.log.error(f"stream_subscribe_loop():{addr}\n{traceback.format_exc()}")
        finally:     
            if stream:
                close_func = getattr(stream, "close", None)
                if callable(close_func):
                    try:
                        await close_func()
                    except Exception:
                        pass
            try:
                await conn.close()
            except Exception:
                pass

    async def stream_publish_loop(self, client):
        """
        Asynchronously receives lz4-compressed BSON messages from a websocket connection, validates their size, decompresses and decodes them, then publishes the contained data to a streaming service. Tracks upload and download byte counts for the client, handles errors gracefully by logging warnings or errors, and ensures the websocket connection is closed upon completion or failure.
        
        Parameters:
            client (dict): A dictionary containing client connection info, including:
                - 'conn': the websocket connection object to receive messages from.
                - 'addr': the client's address for logging purposes.
                - 'database', 'period', 'source', 'tablename': parameters for stream identification.
                - Optional 'user': username for stream access, defaults to 'master'.
        
        Behavior:
            - Continuously receives messages until an empty or oversized message is received.
            - Decompresses and decodes each message from lz4-compressed BSON format.
            - Publishes the 'data' field from each decoded message to the stream asynchronously.
            - Logs warnings on decode errors or invalid messages and terminates the loop.
            - Logs errors on unexpected exceptions.
            - Ensures the websocket connection is closed when done.
        """
        conn = client['conn']
        addr = client['addr']
        client['upload'] = 0
        client['download'] = 0
        shdata = self.shdata
        try:
            stream = shdata.stream(
                client['database'], client['period'], client['source'], client['tablename'],
                user=client.get('user', 'master'), use_aiokafka=True
            )
            client['stream'] = stream
            while True:
                msg_bytes = await conn.receive_bytes()
                if (not msg_bytes) or (len(msg_bytes) > MAX_INPUT_MSG_SIZE):
                    Logger.log.warning(f"Client {addr} sent too large or empty message, closing.")
                    break
                try:
                    msg = bson.BSON.decode(lz4.frame.decompress(msg_bytes))
                except Exception:
                    Logger.log.warning(f"BSON/LZ4 decode error from {addr}, closing connection.")
                    break
                client['download'] += len(msg_bytes)
                await stream.async_extend(msg['data'])
        except Exception as e:
            Logger.log.error(f"stream_publish_loop():{addr} \n{traceback.format_exc()}")
        finally:
            try:
                await conn.close()
            except Exception:
                pass

    async def send_heartbeat(self, host, port):
        """
        Asynchronously sends periodic heartbeat statistics for the current worker.
        
        This coroutine continuously calculates and logs the number of connected clients,
        as well as the upload and download speeds in MB/s, based on data collected from
        the clients. It acquires a lock to safely snapshot client data, computes the
        transfer rates over the elapsed time since the last heartbeat, and logs these
        metrics every 15 seconds.
        
        Args:
            host (str): The hostname or IP address of the worker.
            port (int): The port number the worker is listening on.
        
        Logs:
            Debug-level messages containing the host, port, number of clients,
            download speed, and upload speed.
        """
        last_total_upload = 0
        last_total_download = 0
        lasttime = time.time()
        while True:
            async with self.clients_lock:
                clients_snapshot = list(self.clients.items())
            nclients = len(clients_snapshot)
            total_upload = sum(c.get('upload', 0) for _, c in clients_snapshot)
            total_download = sum(c.get('download', 0) for _, c in clients_snapshot)
            te = time.time() - lasttime
            lasttime = time.time()
            upload = max(0, (total_upload - last_total_upload) / te)
            download = max(0, (total_download - last_total_download) / te)
            last_total_download = total_download
            last_total_upload = total_upload
            Logger.log.debug('#heartbeat#host:%s,port:%i,clients:%i,download:%.3fMB/s,upload:%.3fMB/s' %
                            (host, port, nclients, download/1024/1024, upload/1024/1024))
            await asyncio.sleep(15)

# ---- Gunicorn Embedding ----

class GunicornAioHttpApp(BaseApplication):
    """
    A Gunicorn application class that embeds an aiohttp web application.
    
    This class extends Gunicorn's BaseApplication to allow running an aiohttp app
    within Gunicorn by providing configuration options and loading the aiohttp app.
    
    Attributes:
        _aiohttp_app: The aiohttp web application instance to run.
        _options (dict): Configuration options for Gunicorn.
    
    Methods:
        load_config(): Loads Gunicorn configuration from the provided options.
        load(): Returns the aiohttp application instance to be served.
    """
    def __init__(self, aiohttp_app, options: dict):
        """
        Initializes the instance with an aiohttp application and configuration options.
        
        Parameters:
            aiohttp_app: The aiohttp application instance to be used.
            options (dict): A dictionary of configuration options.
        
        Calls the superclass initializer after setting instance variables.
        """
        self._aiohttp_app = aiohttp_app
        self._options = options
        super().__init__()

    def load_config(self):
        """
        Loads configuration options from the instance's _options dictionary into the cfg object.
        For each key-value pair in _options, if the value is not None, it sets the corresponding
        key in cfg to that value.
        """
        for key, value in self._options.items():
            if value is not None:
                self.cfg.set(key, value)

    def load(self):
        """
        Returns the internal aiohttp application instance.
        
        This method provides access to the underlying aiohttp application object stored in the instance.
        
        Returns:
            aiohttp.web.Application: The aiohttp application associated with this instance.
        """
        return self._aiohttp_app

# ====== MAIN APP SETUP ======
def create_app(args):
    """
    Create and configure an aiohttp web application with a WebSocket server.
    
    This function initializes a web application, sets up shared data access, and creates a WebSocket handler
    for managing client connections. It registers a WebSocket route at the root path ('/') and attaches
    startup and cleanup lifecycle events to manage background tasks for user data refreshing and heartbeat signals.
    
    Args:
        args: An object containing configuration parameters, expected to have 'host' and 'port' attributes.
    
    Returns:
        web.Application: The configured aiohttp web application instance ready to run.
    """
    app = web.Application()
    shdata = SharedData('SharedData.IO.ServerWebSocket', user='master')
    SyncTable.shdata = shdata

    # Prepare one handler per worker for safety
    handler = ServerWebSocket(app, shdata)

    # Attach as 'handler' for router
    app['handler'] = handler

    async def websocket_entry(request):
        """
        Asynchronous entry point for handling a websocket connection.
        
        This function receives a websocket connection request and delegates
        the handling of the client to the `handle_client_thread` method of
        the `handler` object.
        
        Args:
            request: The incoming websocket connection request.
        
        Returns:
            The result of the `handle_client_thread` coroutine, typically
            representing the websocket response or connection handler.
        """
        return await handler.handle_client_thread(request)

    app.router.add_get('/', websocket_entry)

    async def on_startup(app):
        # Initial cache (non-blocking!)
        """
        Asynchronous startup handler for the application.
        
        This function performs initial setup tasks when the application starts:
        - Fetches the initial user cache asynchronously.
        - Starts a periodic task to refresh user data for each worker.
        - Starts a heartbeat task to send periodic stats to a specified host and port.
        
        Args:
            app (dict): The application instance to which background tasks are added.
        """
        await handler.fetch_users()
        # Periodic user refresh task per worker
        app['user_refresh_task'] = asyncio.create_task(handler.refresh_users_periodically())
        # Per-worker stats heartbeat
        app['heartbeat'] = asyncio.create_task(handler.send_heartbeat(args.host, args.port))

    async def on_cleanup(app):
        """
        Asynchronously cleans up the application by cancelling and awaiting specified background tasks.
        
        This function checks for the presence of 'user_refresh_task' and 'heartbeat' tasks in the given
        app dictionary. If found, it cancels these tasks and waits for their completion, handling any exceptions
        that may arise during the cancellation process.
        
        Args:
            app (dict): The application dictionary containing background tasks to be cleaned up.
        
        Returns:
            None
        """
        tasks = []
        if 'user_refresh_task' in app:
            app['user_refresh_task'].cancel()
            tasks.append(app['user_refresh_task'])
        if 'heartbeat' in app:
            app['heartbeat'].cancel()
            tasks.append(app['heartbeat'])
        await asyncio.gather(*tasks, return_exceptions=True)

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app

# ========== entrypoint ==========
if __name__ == '__main__':
    import argparse
    Logger.log.info('ROUTINE STARTED!')
    parser = argparse.ArgumentParser(description="Run SharedData WebSocket via Gunicorn")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--nproc", type=int, default=4, help="Number of Gunicorn worker processes")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--log-level", default="info")
    args = parser.parse_args()

    # Single aiohttp app instance (each worker gets a copy)
    app = create_app(args)

    gunicorn_opts = {
        "bind": f"{args.host}:{args.port}",
        "workers": args.nproc,
        "worker_class": "aiohttp.worker.GunicornWebWorker",
        "timeout": args.timeout,
        "loglevel": args.log_level,
    }
    # All handling is in GunicornAioHttpApp:
    GunicornAioHttpApp(app, gunicorn_opts).run()
