"""
Shared constants for the ServerAPI.
"""

# Response size limits
MAX_RESPONSE_SIZE_BYTES = 20 * 1024 * 1024  # 20MB

# Pagination defaults
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10000
DEFAULT_TABLE_PAGE_SIZE = 0  # 0 means no limit for tables

# Security delays (to slow down brute force attacks)
AUTH_FAILURE_SLEEP_SECONDS = 3
ERROR_SLEEP_SECONDS = 1

# Health check delays
HEALTH_CHECK_SLEEP_SECONDS = 3

# Heartbeat configuration
HEARTBEAT_INTERVAL_SECONDS = 15
HEARTBEAT_STARTUP_DELAY_SECONDS = 15

# Default user
DEFAULT_USER = 'master'

# Output formats
FORMAT_JSON = 'json'
FORMAT_CSV = 'csv'
FORMAT_BIN = 'bin'
FORMAT_BSON = 'bson'
