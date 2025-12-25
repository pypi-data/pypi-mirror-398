"""
Route blueprints package for ServerAPI.

This package contains all route blueprints for the SharedData API.
Each module provides an initialization function that must be called
with a SharedData instance and authentication function before the
blueprint can be registered.
"""

from SharedData.API.routes.tables import tables_bp, init_tables_routes
from SharedData.API.routes.collections import collections_bp, init_collections_routes
from SharedData.API.routes.timeseries import timeseries_bp, init_timeseries_routes
from SharedData.API.routes.workers import workers_bp, init_workers_routes
from SharedData.API.routes.system import (
    system_bp, 
    init_system_routes,
    register_request_hooks,
    get_traffic_stats_data,
    get_traffic_rates_data,
    get_stats_lock,
)

__all__ = [
    # Blueprints
    'tables_bp',
    'collections_bp', 
    'timeseries_bp',
    'workers_bp',
    'system_bp',
    # Initialization functions
    'init_tables_routes',
    'init_collections_routes',
    'init_timeseries_routes',
    'init_workers_routes',
    'init_system_routes',
    'register_request_hooks',
    # Traffic tracking
    'get_traffic_stats_data',
    'get_traffic_rates_data',
    'get_stats_lock',
]
