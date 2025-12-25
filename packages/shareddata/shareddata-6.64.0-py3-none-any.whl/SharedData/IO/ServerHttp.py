"""
run_shareddata.py
Start the whole SharedData stack (Flask app + Gunicorn + background threads)
from a single Python script.

$ python run_shareddata.py --host 0.0.0.0 --port 8002 --workers 4 --threads 20
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time
from gunicorn.app.base import BaseApplication

# ----------------------------------------------------------------------
# 1) Import your Flask application factory or the global `app`
# ----------------------------------------------------------------------

from SharedData.Logger import Logger
Logger.connect('SharedData.IO.ServerHttp')

from SharedData.IO.ServerAPI import app as flask_app                 # ← adjust module name

# ----------------------------------------------------------------------
# 2) “Embedded” Gunicorn class
#    Subclassing BaseApplication lets us pass config dicts programmatically
# ----------------------------------------------------------------------
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
            options (dict[str, str | int]): A dictionary of configuration options where keys are strings and values are either strings or integers.
        """
        self._wsgi_app = wsgi_app
        self._options = options
        super().__init__()

    # Gunicorn hooks ----------------------------------------------------
    def load_config(self):
        """
        Loads configuration options from the instance's _options dictionary into the cfg attribute,
        excluding any options with a value of None.
        """
        config = {key: value for key, value in self._options.items()
                  if value is not None}
        for key, value in config.items():
            self.cfg.set(key, value)

    def load(self):
        """
        Return the WSGI application instance.
        
        This method provides access to the underlying WSGI application object
        stored in the `_wsgi_app` attribute.
        
        Returns:
            object: The WSGI application instance.
        """
        return self._wsgi_app


# ----------------------------------------------------------------------
# 3) Command-line parsing
# ----------------------------------------------------------------------
def parse_cli():
    """
    Parse command-line arguments for running the SharedData API with Gunicorn.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments including:
            --host (str): Host address to bind to (default: "0.0.0.0").
            --port (int): Port number to listen on (default: 8002).
            --nproc (int): Number of Gunicorn worker processes (default: 4).
            --nthreads (int): Number of request threads per worker (default: 8).
            --timeout (int): Timeout in seconds before hard killing a worker (default: 120).
            --log-level (str): Logging level (default: "warning").
    """
    p = argparse.ArgumentParser(description="Run SharedData API via Gunicorn")
    p.add_argument("--host",    default="0.0.0.0")
    p.add_argument("--port",    type=int, default=8002)
    p.add_argument("--nproc", type=int, default=4,
                   help="Number of Gunicorn worker processes")
    p.add_argument("--nthreads", type=int, default=8,
                   help="Number of request threads *per* worker (gthread)")
    p.add_argument("--timeout", type=int, default=120,
                   help="Hard kill after N seconds")
    p.add_argument("--log-level", default="warning")
    return p.parse_args()


# ----------------------------------------------------------------------
# 4) Kick-off helper threads *before* Gunicorn forks workers
# ----------------------------------------------------------------------
def send_heartbeat():    
    """
    Sends periodic heartbeat signals to indicate that the routine is running.
    
    The function waits for an initial 15 seconds before logging a start message. It then enters an infinite loop where it logs a debug heartbeat message every 15 seconds to signal ongoing activity.
    
    Note:
    - Uses a fixed heartbeat interval of 15 seconds.
    - Assumes Logger is a pre-configured logging utility.
    - This function blocks indefinitely once started.
    """
    heartbeat_interval = 15
    time.sleep(15)
    Logger.log.info('ROUTINE STARTED!')
    while True:
        current_time = time.time()        
        # Log the heartbeat with rates
        Logger.log.debug('#heartbeat#')
        time.sleep(heartbeat_interval)
        
def start_background_threads():    
    # Thread that emits heartbeat metrics
    """
    Starts a background daemon thread that continuously emits heartbeat metrics by running the send_heartbeat function.
    """
    heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
    heartbeat_thread.start()


# ----------------------------------------------------------------------
# 5) main()
# ----------------------------------------------------------------------
def main():
    """
    Entry point for the application. Parses command-line arguments, starts necessary background helper threads, configures Gunicorn server options based on the parsed arguments, and launches the Gunicorn server embedded within the process to serve the Flask application. The server runs with specified worker and thread settings, handles graceful shutdowns, and manages worker recycling to mitigate memory leaks.
    """
    args = parse_cli()
    
    # 5a. Launch in-process helper threads
    start_background_threads()

    # 5b. Assemble Gunicorn config
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

    # 5c. Block here; Gunicorn handles signals and will exit cleanly
    GunicornEmbedded(flask_app, gunicorn_opts).run()


# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Basic env-var sanity checks (just like your original Waitress entry)
    required_env = ("SHAREDDATA_SECRET_KEY", "SHAREDDATA_TOKEN")
    missing = [v for v in required_env if v not in os.environ]
    if missing:
        sys.exit(f"Missing environment variables: {', '.join(missing)}")

    main()
