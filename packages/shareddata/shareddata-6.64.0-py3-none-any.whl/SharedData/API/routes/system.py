"""
System routes blueprint for ServerAPI (health, auth, logs, webhooks, traffic_stats).
"""

import json
import threading
import time
from collections import defaultdict

import lz4.frame as lz4f
import pandas as pd
from flask import Blueprint, Response, g, jsonify, request

from SharedData.Logger import Logger

from SharedData.API.constants import (
    ERROR_SLEEP_SECONDS,
    HEALTH_CHECK_SLEEP_SECONDS,
)
from SharedData.API.auth import user_by_token
from SharedData.API.utils import make_json_response, make_error_response


# Blueprint definition
system_bp = Blueprint('system', __name__)

# Thread-safe in-memory storage for traffic statistics
traffic_stats = {
    'total_requests': 0,
    'endpoints': defaultdict(lambda: {
        'requests': 0,
        'total_response_time': 0.0,
        'status_codes': defaultdict(int),
        'total_bytes_sent': 0,
        'total_bytes_received': 0  
    })
}

traffic_rates = {
    'last_total_requests': 0,
    'last_total_bytes_sent': 0,
    'last_total_bytes_received': 0,  
    'last_timestamp': time.time()
}

# Lock for thread-safe updates to traffic_stats
stats_lock = threading.Lock()


def get_traffic_stats_data():
    """Get current traffic stats (for external access)."""
    return traffic_stats


def get_traffic_rates_data():
    """Get current traffic rates (for external access)."""
    return traffic_rates


def get_stats_lock():
    """Get stats lock (for external access)."""
    return stats_lock


def init_system_routes(shdata, authenticate_fn):
    """
    Initialize system routes with required dependencies.
    
    Parameters:
        shdata: SharedData instance.
        authenticate_fn: Authentication function.
    """
    
    @system_bp.route('/traffic_stats', methods=['GET'])
    def get_traffic_stats():
        """
        Handle GET requests to the '/api/traffic_stats' endpoint, returning aggregated 
        traffic statistics in JSON format.
        """
        try:
            if not authenticate_fn(request, shdata):
                return jsonify({'error': 'unauthorized'}), 401

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
                        'total_bytes_received': data['total_bytes_received']
                    }

            return make_json_response(stats_response)

        except Exception as e:
            return make_error_response(e)
        
    @system_bp.route('/heartbeat', methods=['GET', 'POST'])
    def heartbeat():
        """
        Endpoint to check the server heartbeat.
        """
        time.sleep(HEALTH_CHECK_SLEEP_SECONDS)
        return make_json_response({'heartbeat': True})
        
    @system_bp.route('/health', methods=['GET', 'POST'])
    def health():
        """
        Endpoint to check the server health.
        """
        time.sleep(HEALTH_CHECK_SLEEP_SECONDS)
        return make_json_response({'health': True})

    @system_bp.route('/auth', methods=['GET', 'POST'])
    def auth():
        """
        Handle authentication requests via GET or POST methods.
        """
        try:
            if not authenticate_fn(request, shdata):
                return jsonify({'error': 'unauthorized'}), 401
            
            return make_json_response({'authenticated': True})
        except Exception as e:
            time.sleep(ERROR_SLEEP_SECONDS)
            return make_error_response(e)

    @system_bp.route('/logs', methods=['POST'])
    def logs():
        """
        Handle POST requests to the '/api/logs' endpoint by authenticating the request, 
        decompressing and parsing the incoming LZ4-compressed JSON log data, and 
        enqueueing the log record for processing.
        """
        try:
            if not authenticate_fn(request, shdata):
                return jsonify({'error': 'unauthorized'}), 401

            data = lz4f.decompress(request.data)
            rec = json.loads(data.decode('utf-8'))
            with Logger.lock:
                if Logger.log_writer_thread is None:
                    Logger.log_writer_thread = threading.Thread(
                        target=Logger.log_writer, args=(shdata,), daemon=True
                    )
                    Logger.log_writer_thread.start()
            Logger.log_queue.put(rec)
            
            return Response(status=201)

        except Exception as e:
            time.sleep(ERROR_SLEEP_SECONDS)
            response = Response(status=500)                
            response.headers['Error-Message'] = str(e).replace('\n', ' ')
            return response

    @system_bp.route('/webhooks', methods=['POST'])
    def webhooks():
        """
        Handle POST requests to the '/api/webhooks' endpoint.
        """
        try:
            if not authenticate_fn(request, shdata):
                return jsonify({'error': 'unauthorized'}), 401

            data = request.get_json()
            if not data:
                return jsonify({'error': 'invalid data'}), 400
            
            token = request.args.get('token')
            if not token:
                token = request.headers.get('X-Custom-Authorization')
            if not token:
                token = request.headers.get('x-api-key')

            userdata = user_by_token[token]
            
            data['date'] = pd.Timestamp.utcnow()
            data['hash'] = userdata['email']
            
            tbl = shdata.table('Text', 'RT', 'WORKERPOOL', 'WEBHOOKS', 
                                names=['date', 'hash'], formats=['<M8[ns]', '|S256'],
                                hasindex=False, is_schemaless=True, size=0)
            tbl = tbl.extend(data)
            
            return Response(status=200)

        except Exception as e:
            time.sleep(ERROR_SLEEP_SECONDS)
            response = Response(status=500)
            return response

    return system_bp


def register_request_hooks(app):
    """
    Register before_request and after_request hooks on the Flask app.
    
    Parameters:
        app: Flask application instance.
    """
    
    @app.before_request
    def start_timer():
        """Initialize timing and request size tracking before processing each request."""
        g.start_time = time.time()
        content_length = request.headers.get('Content-Length', 0)
        try:
            g.request_bytes = int(content_length)
        except ValueError:
            g.request_bytes = len(request.get_data()) if request.data else 0

    @app.after_request
    def log_request(response):
        """Logs details of each HTTP request after it is processed."""
        response_time = time.time() - g.start_time    
        response.headers['Server'] = 'SharedData'    
        response.headers['X-Response-Time'] = f"{response_time * 1000:.2f}ms"

        endpoint = request.endpoint or request.path
        method = request.method

        content_length = response.headers.get('Content-Length', 0)
        try:
            bytes_sent = int(content_length)
        except ValueError:
            bytes_sent = len(response.get_data()) if response.data else 0

        bytes_received = g.request_bytes

        with stats_lock:
            traffic_stats['total_requests'] += 1
            endpoint_stats = traffic_stats['endpoints'][f"{method} {endpoint}"]
            endpoint_stats['requests'] += 1
            endpoint_stats['total_response_time'] += response_time
            endpoint_stats['status_codes'][response.status_code] += 1
            endpoint_stats['total_bytes_sent'] += bytes_sent
            endpoint_stats['total_bytes_received'] += bytes_received

        return response
