"""
SharedData API Server - Production Entry Point (Gunicorn)

This module provides the production server for the SharedData API using Gunicorn.
For development/testing, use ServerAPI.py which runs with Waitress.

Usage:
    python -m SharedData.API.ServerGunicorn [--host HOST] [--port PORT] [--nproc NPROC] [--nthreads NTHREADS]
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time
from gunicorn.app.base import BaseApplication

from SharedData.Logger import Logger
Logger.connect('SharedData.API.ServerGunicorn')

from SharedData.API import create_app

# Create Flask app at module level for Gunicorn
flask_app = create_app()


class GunicornEmbedded(BaseApplication):
    """
    A Gunicorn application wrapper that runs Gunicorn within the current Python interpreter.
    
    This class allows embedding Gunicorn server functionality directly into a Python process,
    enabling programmatic control over Gunicorn configuration and execution without spawning
    a separate Gunicorn process.
    
    Attributes:
        _wsgi_app: The WSGI application to be served by Gunicorn.
        _options: A dictionary of Gunicorn configuration options.
    
    Example:
        GunicornEmbedded(flask_app, {"bind": "0.0.0.0:8002", "workers": 4}).run()
    """
    def __init__(self, wsgi_app, options: dict[str, str | int]):
        """
        Initializes the instance with a WSGI application and configuration options.
        
        Parameters:
            wsgi_app: The WSGI application callable to be wrapped or used.
            options: A dictionary of Gunicorn configuration options.
        """
        self._wsgi_app = wsgi_app
        self._options = options or {}
        super().__init__()

    def load_config(self):
        """
        Loads configuration settings from a dictionary of options into the Gunicorn configuration.
        
        For each key-value pair in the provided options, this method sets the corresponding
        configuration value in the Gunicorn configuration object, provided that the key is valid.
        """
        for key, value in self._options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        """
        Returns the WSGI application instance.
        
        Returns:
            The WSGI application instance stored in this object.
        """
        return self._wsgi_app


def parse_cli():
    """
    Parse CLI arguments when running as a stand-alone script.
    
    Returns:
        Parsed arguments namespace.
    """
    p = argparse.ArgumentParser(
        description="Run SharedData API with embedded Gunicorn"
    )
    p.add_argument("--host", default="0.0.0.0", help="Listen address")
    p.add_argument("--port", type=int, default=8002, help="Listen port")
    p.add_argument("--nproc", type=int, default=4,
                   help="Number of Gunicorn worker processes")
    p.add_argument("--nthreads", type=int, default=8,
                   help="Number of request threads *per* worker (gthread)")
    p.add_argument("--timeout", type=int, default=120,
                   help="Hard kill after N seconds")
    p.add_argument("--log-level", default="warning")
    return p.parse_args()


def send_heartbeat():    
    """
    Sends periodic heartbeat signals to indicate that the routine is running.
    
    The function waits for an initial 15 seconds before logging a start message. 
    It then enters an infinite loop where it logs a debug heartbeat message every 
    15 seconds to signal ongoing activity.
    """
    heartbeat_interval = 15
    time.sleep(15)
    Logger.log.info('ROUTINE STARTED!')
    while True:
        Logger.log.debug('#heartbeat#')
        time.sleep(heartbeat_interval)
        
        
def start_background_threads():    
    """
    Starts a background daemon thread that continuously emits heartbeat metrics.
    """
    heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
    heartbeat_thread.start()


def main():
    """
    Entry point for the application. Parses command-line arguments, starts necessary 
    background helper threads, configures Gunicorn server options based on the parsed 
    arguments, and launches the Gunicorn server embedded within the process to serve 
    the Flask application.
    """
    args = parse_cli()
    
    # Launch in-process helper threads
    start_background_threads()

    # Assemble Gunicorn config
    gunicorn_opts = {
        "bind":            f"{args.host}:{args.port}",
        "workers":         args.nproc,
        "worker_class":    "gthread",      
        "threads":         args.nthreads,
        "timeout":         args.timeout,
        "graceful_timeout": 30,
        "preload_app":     False,           
        "accesslog":       None,  
        "errorlog":        "-",
        "loglevel":        args.log_level,
        "max_requests":    5000,           # recycle workers → tame leaks
        "max_requests_jitter": 500,
        "limit_request_line": 8190,       # 8190 is HTTP/1.1 spec max        
    }

    # Block here; Gunicorn handles signals and will exit cleanly
    GunicornEmbedded(flask_app, gunicorn_opts).run()


if __name__ == "__main__":
    # Basic env-var sanity checks
    required_env = ("SHAREDDATA_SECRET_KEY", "SHAREDDATA_TOKEN")
    missing = [v for v in required_env if v not in os.environ]
    if missing:
        sys.exit(f"Missing environment variables: {', '.join(missing)}")

    main()
