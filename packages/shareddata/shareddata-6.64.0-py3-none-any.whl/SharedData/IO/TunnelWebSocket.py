import asyncio
import websockets
import argparse

def get_args():
    """
    Parses command-line arguments for configuring a WebSocket tunnel.
    
    Returns:
        argparse.Namespace: An object containing the parsed arguments:
            - local_host (str): Local host address (default: '127.0.0.1')
            - local_port (int): Local port number (default: 2222)
            - remote_uri (str): Remote WebSocket URI (required)
    """
    parser = argparse.ArgumentParser(description="Websocket tunnel configuration")
    parser.add_argument('--local_host', type=str, default='127.0.0.1', help="Local host address")
    parser.add_argument('--local_port', type=int, default=2222, help="Local port number")
    parser.add_argument('--remote_uri', type=str, required=True, help="Remote WebSocket URI wss://")

    return parser.parse_args()

# Configuration
args = get_args()
LOCAL_HOST = args.local_host
LOCAL_PORT = args.local_port
REMOTE_URI = args.remote_uri

async def forward_data(websocket, reader, writer):
    """
    Asynchronously forwards data from a websocket to a stream writer.
    
    Continuously reads messages from the provided websocket and writes them to the given stream writer, ensuring the writer is drained after each write. Handles any exceptions by printing an error message and guarantees the writer is properly closed and awaited upon completion or error.
    
    Args:
        websocket: An asynchronous websocket connection to read messages from.
        reader: An asynchronous stream reader (included for interface consistency, not used).
        writer: An asynchronous stream writer to forward messages to.
    """
    try:
        async for message in websocket:
            writer.write(message)
            await writer.drain()
    except Exception as e:
        print(f"Error in forward_data: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

async def forward_socket_to_websocket(reader, websocket):
    """
    Asynchronously forwards data from a socket-like stream reader to a WebSocket.
    
    This coroutine continuously reads data in chunks of up to 4096 bytes from the given asynchronous `reader`. When data is received, it is sent immediately to the provided asynchronous `websocket`. The forwarding loop ends when the reader yields no more data. Any exceptions during reading or sending are caught and logged.
    
    Args:
        reader: An asynchronous stream reader object with a `read` method that returns bytes.
        websocket: An asynchronous WebSocket connection object with a `send` method that accepts bytes.
    """
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
            await websocket.send(data)
    except Exception as e:
        print(f"Error in forward_socket_to_websocket: {e}")

async def handle_client(reader, writer):
    """
    Handles a client connection by establishing a WebSocket connection to a remote server and forwarding data bidirectionally between the client socket and the WebSocket.
    
    Parameters:
        reader (asyncio.StreamReader): The stream reader for the client socket.
        writer (asyncio.StreamWriter): The stream writer for the client socket.
    
    This coroutine creates two asynchronous tasks to forward data from the client socket to the WebSocket and from the WebSocket back to the client socket concurrently. It ensures proper cleanup by closing the client socket writer upon completion or in case of an error.
    
    Exceptions are caught and logged to the console.
    """
    try:
        async with websockets.connect(REMOTE_URI) as websocket:
            # Create tasks for bidirectional data forwarding
            to_server = asyncio.create_task(forward_socket_to_websocket(reader, websocket))
            to_client = asyncio.create_task(forward_data(websocket, reader, writer))

            await asyncio.gather(to_server, to_client)
    except Exception as e:
        print(f"Error in handle_client: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    """
    Starts an asynchronous TCP server that listens on a specified local host and port.
    
    The server uses the `handle_client` coroutine to handle incoming client connections.
    Once started, it prints a message indicating the address it is listening on and runs indefinitely,
    serving clients asynchronously.
    
    Requires the `asyncio` module and predefined `LOCAL_HOST`, `LOCAL_PORT`, and `handle_client`.
    """
    server = await asyncio.start_server(handle_client, LOCAL_HOST, LOCAL_PORT)
    async with server:
        print(f"Listening on {LOCAL_HOST}:{LOCAL_PORT}...")
        await server.serve_forever()

# Run the main function when the script is executed
if __name__ == "__main__":
    asyncio.run(main())