# Import all common variables, functions, and the Flask app
from SharedData.IO.ServerAPI_Common import *

# Import route handlers from split modules
from SharedData.IO.ServerAPI_Collection import *
from SharedData.IO.ServerAPI_Table import *
from SharedData.IO.ServerAPI_Worker import *
from SharedData.IO.ServerAPI_Timeseries import *

@app.before_request
def start_timer():
    # Store the start time of the request
    """
    Initialize timing and request size tracking before processing each request.
    
    This function records the current time as the start time of the request and attempts to determine the size of the inbound request in bytes. It first tries to read the 'Content-Length' header; if that is not available or invalid, it falls back to measuring the length of the request data. The results are stored in the Flask `g` context for use during the request lifecycle.
    """
    g.start_time = time.time()
    # Store the inbound request size (if available)
    content_length = request.headers.get('Content-Length', 0)
    try:
        g.request_bytes = int(content_length)
    except ValueError:
        g.request_bytes = len(request.get_data()) if request.data else 0

@app.after_request
def log_request(response):
    # Calculate response time
    """
    Logs details of each HTTP request after it is processed, including response time, request method and endpoint, bytes sent and received, and updates aggregated traffic statistics in a thread-safe manner.
    
    Parameters:
        response (flask.Response): The HTTP response object to be sent to the client.
    
    Returns:
        flask.Response: The same response object passed in, unmodified.
    
    This function is intended to be used as a Flask after_request handler. It calculates the time taken to process the request, determines the number of bytes sent and received, and updates global traffic statistics including counts of requests, response times, status codes, and data transfer metrics per endpoint and HTTP method.
    """
    response_time = time.time() - g.start_time    
    response.headers['Server'] = 'SharedData'    
    response.headers['X-Response-Time'] = f"{response_time * 1000:.2f}ms"

    # Get endpoint and method
    endpoint = request.endpoint or request.path
    method = request.method

    # Calculate bytes sent (outbound)
    content_length = response.headers.get('Content-Length', 0)
    try:
        bytes_sent = int(content_length)
    except ValueError:
        bytes_sent = len(response.get_data()) if response.data else 0

    # Get bytes received (inbound) from before_request
    bytes_received = g.request_bytes

    # Update statistics in a thread-safe manner
    with stats_lock:
        traffic_stats['total_requests'] += 1
        endpoint_stats = traffic_stats['endpoints'][f"{method} {endpoint}"]
        endpoint_stats['requests'] += 1
        endpoint_stats['total_response_time'] += response_time
        endpoint_stats['status_codes'][response.status_code] += 1
        endpoint_stats['total_bytes_sent'] += bytes_sent
        endpoint_stats['total_bytes_received'] += bytes_received  # Track inbound traffic

    return response

@app.route('/api/traffic_stats', methods=['GET'])
def get_traffic_stats():
    """
    Handle GET requests to the '/api/traffic_stats' endpoint, returning aggregated traffic statistics in JSON format.
    
    This function authenticates the incoming request, then accesses shared traffic statistics data in a thread-safe manner using a lock.
    It compiles a summary including total requests, per-endpoint request counts, average response times, status code distributions,
    and total bytes sent and received. The response is returned with appropriate headers. In case of errors, it returns a JSON error message
    with a 500 status code.
    
    Returns:
        Response: A Flask Response object containing JSON-encoded traffic statistics or an error message.
    """
    try:
        
        if not authenticate(request):
            return jsonify({'error': 'unauthorized'}), 401

        # Prepare statistics for response in a thread-safe manner
        stats_response = {
            'total_requests': 0,
            'endpoints': {}
        }

        with stats_lock:
            stats_response['total_requests'] = traffic_stats['total_requests']
            for endpoint, data in traffic_stats['endpoints'].items():
                stats_response['endpoints'][endpoint] = {
                    'requests': data['requests'],
                    'average_response_time': data['total_response_time'] / data['requests'] if data['requests'] > 0 else 0,
                    'status_codes': dict(data['status_codes']),
                    'total_bytes_sent': data['total_bytes_sent'],
                    'total_bytes_received': data['total_bytes_received']  # Add inbound stats
                }

        response_data = json.dumps(stats_response).encode('utf-8')
        response = Response(response_data, mimetype='application/json')
        response.headers['Content-Length'] = len(response_data)
        return response

    except Exception as e:
        error_data = json.dumps({'error': str(e)}).encode('utf-8')
        response = Response(error_data, status=500, mimetype='application/json')
        response.headers['Content-Length'] = len(error_data)
        return response
    
@app.route('/api/heartbeat', methods=['GET', 'POST'])
def heartbeat():
    """
    Endpoint to check the server heartbeat.
    
    Handles GET and POST requests by pausing for 3 seconds before responding with a JSON object indicating the server is alive. Returns a 200 OK response with a JSON payload `{"heartbeat": true}` and sets the appropriate Content-Length header.
    """
    time.sleep(3)
    response_data = json.dumps({'heartbeat': True}).encode('utf-8')
    response = Response(response_data, status=200, mimetype='application/json')
    response.headers['Content-Length'] = len(response_data)
    return response
    
@app.route('/api/health', methods=['GET', 'POST'])
def health():
    """
    Endpoint to check the server health.
    
    Handles GET and POST requests by pausing for 3 seconds before responding with a JSON object indicating the server is alive. Returns a 200 OK response with a JSON payload `{"heartbeat": true}` and sets the appropriate Content-Length header.
    """
    time.sleep(3)
    response_data = json.dumps({'health': True}).encode('utf-8')
    response = Response(response_data, status=200, mimetype='application/json')
    response.headers['Content-Length'] = len(response_data)
    return response

@app.route('/api/auth', methods=['GET', 'POST'])
def auth():
    """
    Handle authentication requests via GET or POST methods.
    
    This endpoint checks for a valid authentication token in the request headers using the `authenticate` function.
    - If authentication fails, it returns a 401 Unauthorized response with an error message.
    - If authentication succeeds, it returns a 200 OK response with a JSON payload indicating successful authentication.
    - In case of any exceptions during processing, it returns a 500 Internal Server Error with the error details.
    
    Returns:
        Response: A Flask Response object containing JSON data and appropriate HTTP status codes.
    """
    try:
        # Check for the token in the header        
        if not authenticate(request):
            return jsonify({'error': 'unauthorized'}), 401
        
        response_data = json.dumps({'authenticated': True}).encode('utf-8')
        response = Response(response_data, status=200, mimetype='application/json')
        response.headers['Content-Length'] = len(response_data)
        return response
    except Exception as e:
        time.sleep(1)  # Sleep for 1 second before returning the error        
        error_message = json.dumps({"type": "InternalServerError", "message": str(e)})
        response = Response(error_message, status=500, mimetype='application/json')
        response.headers['Content-Length'] = len(error_message)
        return response

@app.route('/api/logs', methods=['POST'])
def logs():
    """
    Handle POST requests to the '/api/logs' endpoint by authenticating the request, decompressing and parsing the incoming LZ4-compressed JSON log data, and enqueueing the log record for processing.
    
    Returns:
        Response with status code 201 on successful log receipt.
        Response with status code 401 and JSON error message if authentication fails.
        Response with status code 500 and an error message header if an exception occurs during processing.
    """
    try:
        if not authenticate(request):
            return jsonify({'error': 'unauthorized'}), 401

        data = lz4f.decompress(request.data)
        rec = json.loads(data.decode('utf-8'))
        with Logger.lock:
            if Logger.log_writer_thread is None:
                Logger.log_writer_thread = threading.Thread(
                    target=Logger.log_writer,args=(shdata,), daemon=True
                )
                Logger.log_writer_thread.start()
        Logger.log_queue.put(rec)
        
        return Response(status=201)

    except Exception as e:
        time.sleep(1)  # Sleep for 1 second before returning the error        
        response = Response(status=500)                
        response.headers['Error-Message'] = str(e).replace('\n', ' ')
        return response

@app.route('/api/webhooks', methods=['POST'])
def webhooks():
    """
    Handle POST requests to the '/api/webhooks' endpoint.
    
    This endpoint authenticates the request using a token provided either as a query parameter or in the headers.
    Upon successful authentication, it processes the incoming JSON payload by adding a timestamp and user email hash,
    then stores the data in a specified collection.
    
    Returns:
        Response with status code 200 on successful processing.
        Response with status code 400 if the JSON payload is invalid or missing.
        Response with status code 401 if authentication fails.
        Response with status code 500 if an unexpected error occurs during processing.
    """
    try:
        if not authenticate(request):
            return jsonify({'error': 'unauthorized'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'error': 'invalid data'}), 400
        
        token = request.args.get('token')  # Not Optional
        if not token:
            token = request.headers.get('X-Custom-Authorization')
        if not token:
            token = request.headers.get('x-api-key')

        userdata = user_by_token[token]
        
        data['date'] = pd.Timestamp.utcnow()
        data['hash'] = userdata['email']
        
        tbl = shdata.table('Text','RT','WORKERPOOL','WEBHOOKS', 
                            names = ['date','hash'],formats=['<M8[ns]','|S256'],
                            hasindex=False, is_schemaless=True, size=0)
        tbl = tbl.extend(data)
        
        return Response(status=200)

    except Exception as e:
        time.sleep(1)  # Sleep for 1 second before returning the error        
        response = Response(status=500)
        return response

if __name__ == '__main__':
    from waitress import serve
    import logging
    # Suppress Waitress logs
    waitress_logger = logging.getLogger('waitress')
    waitress_logger.setLevel(logging.CRITICAL)
    waitress_logger.addHandler(logging.NullHandler())

    import threading
    import sys
    import time  
    import argparse
            
    parser = argparse.ArgumentParser(description="Server configuration")
    parser.add_argument('--host', default='0.0.0.0', help='Server host address')
    parser.add_argument('--port', type=int, default=8002, help='Server port number')
    parser.add_argument('--nthreads', type=int, default=8, help='Number of server threads')

    args = parser.parse_args()
    host = args.host
    port = args.port
    nthreads = args.nthreads    
        
    heartbeat_running = True  # Flag to control the heartbeat thread    
    def send_heartbeat():
        global heartbeat_running, traffic_rates
        heartbeat_interval = 15
        time.sleep(15)
        Logger.log.info('ROUTINE STARTED!')
        while heartbeat_running:
            current_time = time.time()
            with stats_lock:
                current_total_requests = traffic_stats['total_requests']
                current_total_bytes_sent = sum(ep['total_bytes_sent'] for ep in traffic_stats['endpoints'].values())
                current_total_bytes_received = sum(ep['total_bytes_received'] for ep in traffic_stats['endpoints'].values())
                
                # Calculate time elapsed since last heartbeat
                time_elapsed = current_time - traffic_rates['last_timestamp']
                if time_elapsed > 0:
                    # Calculate rates
                    requests_delta = current_total_requests - traffic_rates['last_total_requests']
                    bytes_sent_delta = current_total_bytes_sent - traffic_rates['last_total_bytes_sent']
                    bytes_received_delta = current_total_bytes_received - traffic_rates['last_total_bytes_received']
                    requests_per_sec = requests_delta / time_elapsed
                    bytes_sent_per_sec = bytes_sent_delta / time_elapsed
                    bytes_received_per_sec = bytes_received_delta / time_elapsed
                else:
                    requests_per_sec = 0.0
                    bytes_sent_per_sec = 0.0
                    bytes_received_per_sec = 0.0
                
                # Update the last values for the next iteration
                traffic_rates['last_total_requests'] = current_total_requests
                traffic_rates['last_total_bytes_sent'] = current_total_bytes_sent
                traffic_rates['last_total_bytes_received'] = current_total_bytes_received
                traffic_rates['last_timestamp'] = current_time

            # Log the heartbeat with rates
            Logger.log.debug('#heartbeat#host:%s,port:%i,reqs:%i,reqps:%.2f,download:%.2fMB/s,upload:%.2fMB/s' % 
                            (host, port, current_total_requests, requests_per_sec, 
                                bytes_received_per_sec/(1024**2), bytes_sent_per_sec/(1024**2)))
            time.sleep(heartbeat_interval)
            
    t = threading.Thread(target=send_heartbeat, args=(), daemon=True)
    t.start()    

    try:
        serve(
            app, 
            host=host, 
            port=port,  
            threads=nthreads,
            expose_tracebacks=False,
            asyncore_use_poll=True,
            _quiet=True,
            ident='SharedData'
        )
    except Exception as e:
        Logger.log.error(f"Waitress server encountered an error: {e}")
        heartbeat_running = False  # Stop the heartbeat thread
        t.join()  # Wait for the heartbeat thread to finish
        sys.exit(1)  # Exit the program with an error code
    finally:
        # This block will always execute, even if an exception occurs.
        # Useful for cleanup if needed.
        Logger.log.info("Server shutting down...")
        heartbeat_running = False  # Ensure heartbeat stops on normal shutdown
        t.join()  # Wait for heartbeat thread to finish
        Logger.log.info("Server shutdown complete.")