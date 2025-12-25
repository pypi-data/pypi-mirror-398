"""
Metadata routes blueprint for SharedData API.

Provides CRUD operations for Metadata class instances.
Data I/O uses BSON with LZ4 compression to preserve data types.
"""

import time
import json
import pandas as pd

from flask import Blueprint, Response, jsonify, request

from SharedData.Logger import Logger
from SharedData.Metadata import Metadata
from SharedData.API.constants import (
    DEFAULT_USER,
    ERROR_SLEEP_SECONDS,
)
from SharedData.API.utils import (
    make_error_response,
    make_bson_lz4_response,
    parse_bool_param,
    get_user_param,
    decode_bson_request,
)

# Blueprint definition
metadata_bp = Blueprint('metadata', __name__)


def init_metadata_routes(shdata, authenticate_fn):
    """
    Initialize metadata routes with required dependencies.
    
    Parameters:
        shdata: SharedData instance.
        authenticate_fn: Authentication function.
    """
    
    @metadata_bp.route('/metadata', methods=['GET'])
    def list_metadata():
        """
        GET /api/metadata - List metadata entries matching a keyword.
        
        Query Parameters:
            keyword (str): Search keyword for metadata names (required).
            user (str): User identifier (default: 'master').
        
        Returns:
            JSON array of metadata names matching the keyword.
        """
        try:
            if not authenticate_fn(request, shdata):
                time.sleep(ERROR_SLEEP_SECONDS)
                return jsonify({'error': 'unauthorized'}), 401
            
            keyword = request.args.get('keyword', '')
            user = get_user_param(request)
            
            keys = Metadata.list(keyword, user=user)
            
            response_data = json.dumps(keys).encode('utf-8')
            response = Response(response_data, mimetype='application/json')
            response.headers['Content-Length'] = len(response_data)
            return response
            
        except Exception as e:
            Logger.log.error(f'list_metadata error: {e}')
            time.sleep(ERROR_SLEEP_SECONDS)
            return make_error_response(e)

    @metadata_bp.route('/metadata/<name>', methods=['HEAD', 'GET', 'POST', 'PUT', 'DELETE'])
    def metadata_crud(name):
        """
        Handle CRUD operations on a specific metadata entry.
        
        URL Parameters:
            name (str): The metadata name identifier.
        
        Query Parameters:
            user (str): User identifier (default: 'master').
            save_excel (bool): Whether to also save Excel file on POST (default: False).
        
        Methods:
            HEAD: Check if metadata exists.
            GET: Retrieve metadata as BSON+LZ4 (preserves data types).
            POST: Create or replace metadata from BSON+LZ4 payload.
            PUT: Merge update existing metadata with BSON+LZ4 payload.
            DELETE: Delete the metadata entry.
        """
        try:
            if not authenticate_fn(request, shdata):
                time.sleep(ERROR_SLEEP_SECONDS)
                return jsonify({'error': 'unauthorized'}), 401
            
            if request.method == 'HEAD':
                return head_metadata(name, request)
            elif request.method == 'GET':
                return get_metadata(name, request)
            elif request.method == 'POST':
                return post_metadata(name, request)
            elif request.method == 'PUT':
                return put_metadata(name, request)
            elif request.method == 'DELETE':
                return delete_metadata(name, request)
            else:
                return jsonify({'error': 'method not allowed'}), 405
                
        except Exception as e:
            Logger.log.error(f'metadata_crud error ({request.method} {name}): {e}')
            time.sleep(ERROR_SLEEP_SECONDS)
            return make_error_response(e)

    def head_metadata(name, request):
        """
        Check if metadata exists.
        
        Returns:
            200 with headers if exists.
            404 if not found.
        """
        user = get_user_param(request)
        
        try:
            md = Metadata(name, user=user)
            if md.static.empty:
                return Response(status=404)
            
            response = Response(status=200)
            response.headers['X-Metadata-Name'] = name
            response.headers['X-Metadata-User'] = user
            response.headers['X-Metadata-Rows'] = str(len(md.static))
            response.headers['X-Metadata-Columns'] = str(len(md.static.columns))
            response.headers['X-Metadata-HasIndex'] = str(md.hasindex())
            return response
        except Exception:
            return Response(status=404)

    def get_metadata(name, request):
        """
        Retrieve metadata as BSON+LZ4 compressed data.
        
        Query Parameters:
            user (str): User identifier.
        
        Returns:
            BSON+LZ4 compressed response with:
                - data: List of records (DataFrame rows as dicts).
                - index_columns: List of index column names if indexed.
                - columns: List of column names.
                - dtypes: Dict mapping column names to dtype strings.
        """
        user = get_user_param(request)
        
        md = Metadata(name, user=user)
        
        if md.static.empty:
            return Response(status=404)
        
        # Reset index for serialization if has index
        df = md.static
        index_columns = []
        if md.hasindex():
            index_columns = md._index_columns.tolist()
            df = df.reset_index()
        
        # Build response payload preserving types
        payload = {
            'name': name,
            'user': user,
            'data': df.to_dict(orient='records'),
            'index_columns': index_columns,
            'columns': df.columns.tolist(),
            'dtypes': {col: str(df[col].dtype) for col in df.columns},
        }
        
        response = make_bson_lz4_response(payload)
        response.headers['X-Metadata-Name'] = name
        response.headers['X-Metadata-User'] = user
        response.headers['X-Metadata-Rows'] = str(len(md.static))
        response.headers['X-Metadata-Columns'] = str(len(md.static.columns))
        response.headers['X-Metadata-HasIndex'] = str(md.hasindex())
        if md.hasindex():
            response.headers['X-Metadata-IndexColumns'] = ','.join(index_columns)
        
        return response

    def post_metadata(name, request):
        """
        Create or replace metadata from BSON+LZ4 payload.
        
        Request Body (BSON+LZ4 compressed):
            - data: Array of records (list of dicts).
            - index_columns: Optional list of column names to use as index.
            - dtypes: Optional dict mapping column names to dtype strings.
        
        Query Parameters:
            user (str): User identifier.
            save_excel (bool): Also save as Excel file (default: False).
        
        Returns:
            201 Created on success.
        """
        user = get_user_param(request)
        save_excel = parse_bool_param(request.args.get('save_excel'), False)
        
        # Decode BSON+LZ4 request body
        payload = decode_bson_request(request)
        
        if payload is None:
            return jsonify({'error': 'invalid BSON payload'}), 400
        
        # Extract data and options from payload
        if isinstance(payload, dict) and 'data' in payload:
            data = payload['data']
            index_columns = payload.get('index_columns', None)
            dtypes = payload.get('dtypes', None)
        else:
            return jsonify({'error': 'payload must contain data field'}), 400
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Apply dtypes if provided
        if dtypes:
            for col, dtype in dtypes.items():
                if col in df.columns:
                    try:
                        df[col] = df[col].astype(dtype)
                    except (ValueError, TypeError):
                        pass  # Keep original type if conversion fails
        
        # Set index if specified
        if index_columns:
            if isinstance(index_columns, str):
                index_columns = [index_columns]
            df = df.set_index(index_columns)
        
        # Create metadata and save
        md = Metadata(name, user=user)
        md.static = df
        md.save(save_excel=save_excel)
        
        response = Response(status=201)
        response.headers['X-Metadata-Name'] = name
        response.headers['X-Metadata-User'] = user
        response.headers['X-Metadata-Rows'] = str(len(df))
        return response

    def put_metadata(name, request):
        """
        Merge update existing metadata with BSON+LZ4 payload.
        
        Uses Metadata.mergeUpdate() to update existing entries and add new ones.
        
        Request Body (BSON+LZ4 compressed):
            - data: Array of records (list of dicts).
            - index_columns: Optional list of column names to use as index.
            - dtypes: Optional dict mapping column names to dtype strings.
        
        Query Parameters:
            user (str): User identifier.
            save_excel (bool): Also save as Excel file (default: False).
        
        Returns:
            200 OK on success.
            404 if metadata doesn't exist.
        """
        user = get_user_param(request)
        save_excel = parse_bool_param(request.args.get('save_excel'), False)
        
        # Decode BSON+LZ4 request body
        payload = decode_bson_request(request)
        
        if payload is None:
            return jsonify({'error': 'invalid BSON payload'}), 400
        
        # Load existing metadata
        md = Metadata(name, user=user)
        
        if md.static.empty:
            return jsonify({'error': 'metadata not found, use POST to create'}), 404
        
        # Extract data and options from payload
        if isinstance(payload, dict) and 'data' in payload:
            data = payload['data']
            index_columns = payload.get('index_columns', None)
            dtypes = payload.get('dtypes', None)
        else:
            return jsonify({'error': 'payload must contain data field'}), 400
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Apply dtypes if provided
        if dtypes:
            for col, dtype in dtypes.items():
                if col in df.columns:
                    try:
                        df[col] = df[col].astype(dtype)
                    except (ValueError, TypeError):
                        pass  # Keep original type if conversion fails
        
        # Set index - must match existing metadata index
        if index_columns:
            if isinstance(index_columns, str):
                index_columns = [index_columns]
            df = df.set_index(index_columns)
        elif md.hasindex():
            # Use existing index columns
            existing_index_cols = md._index_columns.tolist()
            if all(col in df.columns for col in existing_index_cols):
                df = df.set_index(existing_index_cols)
        
        # Merge update
        md.mergeUpdate(df)
        md.save(save_excel=save_excel)
        
        response = Response(status=200)
        response.headers['X-Metadata-Name'] = name
        response.headers['X-Metadata-User'] = user
        response.headers['X-Metadata-Rows'] = str(len(md.static))
        return response

    def delete_metadata(name, request):
        """
        Delete metadata entry.
        
        Query Parameters:
            user (str): User identifier.
        
        Returns:
            204 No Content on success.
            404 if metadata doesn't exist.
        """
        user = get_user_param(request)
        
        success = Metadata.delete(name, user=user)
        
        if success:
            return Response(status=204)
        else:
            return jsonify({'error': 'metadata not found or delete failed'}), 404

    return metadata_bp
