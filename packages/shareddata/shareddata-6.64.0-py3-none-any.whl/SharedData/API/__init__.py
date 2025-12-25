"""
SharedData API Package - Flask Blueprint-based API structure.

This package provides a modular, blueprint-based Flask API for SharedData operations.
"""

import os
from pathlib import Path

from flask import Flask
from flasgger import Swagger
from werkzeug.middleware.proxy_fix import ProxyFix

from SharedData.SharedData import SharedData
from SharedData.Logger import Logger

from SharedData.API.auth import authenticate
from SharedData.API.routes.tables import tables_bp, init_tables_routes
from SharedData.API.routes.collections import collections_bp, init_collections_routes
from SharedData.API.routes.timeseries import timeseries_bp, init_timeseries_routes
from SharedData.API.routes.workers import workers_bp, init_workers_routes
from SharedData.API.routes.metadata import metadata_bp, init_metadata_routes
from SharedData.API.routes.system import (
    system_bp, 
    init_system_routes, 
    register_request_hooks,
    get_traffic_stats_data,
    get_traffic_rates_data,
    get_stats_lock,
)


def create_app(shdata=None, quiet=True):
    """
    Create and configure the Flask application with all blueprints.
    
    Parameters:
        shdata: Optional SharedData instance. If not provided, one will be created.
        quiet: Whether to suppress SharedData logging.
    
    Returns:
        Configured Flask application instance.
    """
    # Create Flask app
    app = Flask(__name__)
    app.config['APP_NAME'] = 'SharedData API'
    app.config['FLASK_ENV'] = 'production'
    app.config['FLASK_DEBUG'] = '0'

    # Validate secret key
    if 'SHAREDDATA_SECRET_KEY' not in os.environ:
        raise Exception('SHAREDDATA_SECRET_KEY environment variable not set')

    app.config['SECRET_KEY'] = os.environ['SHAREDDATA_SECRET_KEY']
    app.config['SWAGGER'] = {
        'title': 'SharedData API',
        'uiversion': 3,
        'hide_top_bar': True,
        'doc_expansion': 'list'
    }

    # Setup Swagger documentation
    DOCSPATH = Path(__file__).parent / 'apidocs.yml'
    if DOCSPATH.exists():
        swagger = Swagger(app, template_file=str(DOCSPATH))
    else:
        swagger = Swagger(app)

    # Setup proxy fix for proper header handling
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Create SharedData instance if not provided
    if shdata is None:
        shdata = SharedData('SharedData.API', user='master', quiet=quiet)

    # Create authentication function bound to shdata
    def authenticate_fn(request, sd):
        return authenticate(request, sd)

    # Initialize and register blueprints
    init_tables_routes(shdata, authenticate_fn)
    init_collections_routes(shdata, authenticate_fn)
    init_timeseries_routes(shdata, authenticate_fn)
    init_workers_routes(shdata, authenticate_fn)
    init_metadata_routes(shdata, authenticate_fn)
    init_system_routes(shdata, authenticate_fn)

    # Register blueprints with /api prefix
    app.register_blueprint(tables_bp, url_prefix='/api')
    app.register_blueprint(collections_bp, url_prefix='/api')
    app.register_blueprint(timeseries_bp, url_prefix='/api')
    app.register_blueprint(workers_bp, url_prefix='/api')
    app.register_blueprint(metadata_bp, url_prefix='/api')
    app.register_blueprint(system_bp, url_prefix='/api')

    # Register request lifecycle hooks
    register_request_hooks(app)

    # Store shdata on app for access in routes
    app.shdata = shdata

    return app


# Create global app instance for backward compatibility with ServerHttp.py
# This is imported as: from SharedData.API import app
app = None


def get_app():
    """
    Get or create the Flask application instance.
    
    Returns:
        Flask application instance.
    """
    global app
    if app is None:
        app = create_app()
    return app


# Export commonly used items
__all__ = [
    'create_app',
    'get_app',
    'app',
    'authenticate',
    'get_traffic_stats_data',
    'get_traffic_rates_data', 
    'get_stats_lock',
]
