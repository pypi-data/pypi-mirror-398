"""
Shared utility functions for ServerAPI response handling and parameter parsing.
"""

import gzip
import json
from typing import Any, Optional, Union

import bson
import lz4.frame as lz4f
import pandas as pd
from flask import Response

from SharedData.API.constants import (
    DEFAULT_USER,
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
)


def make_json_response(
    data: Any,
    status: int = 200,
    compress: bool = False,
    accept_encoding: str = ''
) -> Response:
    """
    Create a JSON response with optional gzip compression.
    
    Parameters:
        data: Data to serialize to JSON.
        status: HTTP status code.
        compress: Whether to attempt compression.
        accept_encoding: The Accept-Encoding header value from the request.
    
    Returns:
        Flask Response object with proper headers.
    """
    response_data = json.dumps(data).encode('utf-8')
    
    if compress and 'gzip' in accept_encoding:
        compressed = gzip.compress(response_data, compresslevel=1)
        response = Response(compressed, status=status, mimetype='application/json')
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = len(compressed)
    else:
        response = Response(response_data, status=status, mimetype='application/json')
        response.headers['Content-Length'] = len(response_data)
    
    return response


def make_error_response(
    error: Union[str, Exception],
    status: int = 500,
    error_type: str = 'InternalServerError'
) -> Response:
    """
    Create a standardized error response.
    
    Parameters:
        error: Error message or exception.
        status: HTTP status code.
        error_type: Type of error for the response body.
    
    Returns:
        Flask Response object with error details.
    """
    error_message = str(error).replace('\n', ' ')
    error_data = json.dumps({
        'type': error_type,
        'message': error_message
    }).encode('utf-8')
    response = Response(error_data, status=status, mimetype='application/json')
    response.headers['Content-Length'] = len(error_data)
    return response


def make_empty_response(status: int = 204) -> Response:
    """
    Create an empty response (typically for 204 No Content).
    
    Parameters:
        status: HTTP status code.
    
    Returns:
        Flask Response object with zero content length.
    """
    response = Response(status=status)
    response.headers['Content-Length'] = 0
    return response


def make_bson_lz4_response(data: Any, status: int = 200) -> Response:
    """
    Create a BSON-encoded, LZ4-compressed response.
    
    Parameters:
        data: Data to encode (must be BSON-serializable).
        status: HTTP status code.
    
    Returns:
        Flask Response object with compressed BSON data.
    """
    bson_data = bson.encode(data)
    compressed = lz4f.compress(bson_data)
    response = Response(compressed, status=status, mimetype='application/octet-stream')
    response.headers['Content-Encoding'] = 'lz4'
    response.headers['Content-Length'] = len(compressed)
    return response


def make_csv_response(
    csv_data: str,
    compress: bool = False,
    accept_encoding: str = ''
) -> Response:
    """
    Create a CSV response with optional gzip compression.
    
    Parameters:
        csv_data: CSV string data.
        compress: Whether to attempt compression.
        accept_encoding: The Accept-Encoding header value from the request.
    
    Returns:
        Flask Response object with CSV data.
    """
    response_bytes = csv_data.encode('utf-8')
    
    if compress and 'gzip' in accept_encoding:
        compressed = gzip.compress(response_bytes, compresslevel=1)
        response = Response(compressed, mimetype='text/csv')
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = len(compressed)
    else:
        response = Response(response_bytes, mimetype='text/csv')
        response.headers['Content-Length'] = len(response_bytes)
    
    return response


def make_binary_response(
    data: bytes,
    compress: bool = False,
    accept_encoding: str = ''
) -> Response:
    """
    Create a binary response with optional gzip compression.
    
    Parameters:
        data: Binary data.
        compress: Whether to attempt compression.
        accept_encoding: The Accept-Encoding header value from the request.
    
    Returns:
        Flask Response object with binary data.
    """
    if compress and 'gzip' in accept_encoding:
        compressed = gzip.compress(data, compresslevel=1)
        response = Response(compressed, mimetype='application/octet-stream')
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = len(compressed)
    else:
        response = Response(data, mimetype='application/octet-stream')
        response.headers['Content-Length'] = len(data)
    
    return response


def parse_bool_param(value: Optional[str], default: bool = True) -> bool:
    """
    Parse a boolean query parameter.
    
    Parameters:
        value: String value from query parameter (e.g., 'True', 'False', 'true').
        default: Default value if value is None.
    
    Returns:
        Parsed boolean value.
    """
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes')


def parse_int_param(value: Optional[str], default: int = 0) -> int:
    """
    Parse an integer query parameter, handling float strings.
    
    Parameters:
        value: String value from query parameter.
        default: Default value if value is None or invalid.
    
    Returns:
        Parsed integer value.
    """
    if value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def parse_date_param(value: Optional[str]) -> Optional[pd.Timestamp]:
    """
    Parse a date query parameter to pandas Timestamp.
    
    Parameters:
        value: Date string in any format pandas can parse.
    
    Returns:
        Parsed Timestamp or None if value is None.
    """
    if value is None:
        return None
    return pd.Timestamp(value)


def parse_json_param(value: Optional[str], default: Any = None) -> Any:
    """
    Parse a JSON query parameter.
    
    Parameters:
        value: JSON string.
        default: Default value if value is None or invalid.
    
    Returns:
        Parsed JSON value or default.
    """
    if value is None:
        return default if default is not None else {}
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else {}


def parse_list_param(value: Optional[str], separator: str = ',') -> Optional[list]:
    """
    Parse a comma-separated list query parameter.
    
    Parameters:
        value: Comma-separated string.
        separator: Character to split on.
    
    Returns:
        List of strings or None if value is None.
    """
    if value is None:
        return None
    return [item.strip() for item in value.split(separator) if item.strip()]


def get_user_param(request) -> str:
    """
    Extract the user parameter from a request with default.
    
    Parameters:
        request: Flask request object.
    
    Returns:
        User string (defaults to 'master').
    """
    return request.args.get('user', DEFAULT_USER)


def get_pagination_params(request, default_per_page: int = DEFAULT_PAGE_SIZE) -> tuple:
    """
    Extract pagination parameters from a request.
    
    Parameters:
        request: Flask request object.
        default_per_page: Default page size.
    
    Returns:
        Tuple of (page, per_page).
    """
    page = parse_int_param(request.args.get('page'), DEFAULT_PAGE)
    per_page = parse_int_param(request.args.get('per_page'), default_per_page)
    return page, per_page


def apply_subfolder(basepath: str, subfolder: Optional[str]) -> str:
    """
    Append a subfolder to a base path if provided.
    
    Parameters:
        basepath: The base table/tag name.
        subfolder: Optional subfolder to append.
    
    Returns:
        Combined path or original basepath.
    """
    if subfolder is not None:
        return f"{basepath}/{subfolder}"
    return basepath


def decompress_request_data(request) -> bytes:
    """
    Decompress request data if LZ4 encoded, otherwise return raw data.
    
    Parameters:
        request: Flask request object.
    
    Returns:
        Decompressed or raw bytes.
    """
    content_encoding = request.headers.get('Content-Encoding', '').lower()
    if content_encoding == 'lz4':
        return lz4f.decompress(request.data)
    return request.data


def decode_bson_request(request) -> Any:
    """
    Decompress and decode BSON data from request.
    
    Parameters:
        request: Flask request object with LZ4-compressed BSON data.
    
    Returns:
        Decoded Python object.
    """
    decompressed = lz4f.decompress(request.data)
    return bson.decode(decompressed)


def decode_json_request(request) -> Any:
    """
    Get JSON data from request, handling both compressed and uncompressed.
    
    Parameters:
        request: Flask request object.
    
    Returns:
        Decoded JSON data.
    """
    content_encoding = request.headers.get('Content-Encoding', '').lower()
    if content_encoding == 'lz4':
        decompressed = lz4f.decompress(request.data)
        return json.loads(decompressed.decode('utf-8'))
    return request.get_json()
