"""
SharedData API Server - Development Entry Point

This module provides the development server for the SharedData API.
For production, use ServerHttp.py which runs with Gunicorn.

Usage:
    python -m SharedData.API.ServerWaitress [--host HOST] [--port PORT]
"""

import os
import sys
import argparse

from waitress import serve

from SharedData.Logger import Logger


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='SharedData API Development Server')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8002,
                        help='Port to bind to (default: 8002)')
    parser.add_argument('--threads', type=int, default=4,
                        help='Number of worker threads (default: 4)')
    return parser.parse_args()


def validate_environment():
    """Validate required environment variables are set."""
    required_env = ('SHAREDDATA_SECRET_KEY', 'SHAREDDATA_TOKEN')
    missing = [v for v in required_env if v not in os.environ]
    if missing:
        sys.exit(f"Missing environment variables: {', '.join(missing)}")


def main():
    """Main entry point for the development server."""
    # Validate environment
    validate_environment()
    
    # Parse arguments
    args = parse_args()
    
    # Setup logging
    Logger.connect('SharedData.API.ServerWaitress')
    Logger.log.info(f'Starting SharedData API development server on {args.host}:{args.port}')
    
    # Import and create app (after logging is setup)
    from SharedData.API import create_app
    app = create_app()
    
    # Run with Waitress (production-quality WSGI server)
    Logger.log.info(f'Server ready - http://{args.host}:{args.port}')
    serve(app, host=args.host, port=args.port, threads=args.threads)


if __name__ == '__main__':
    main()
