"""
Timeseries routes blueprint for ServerAPI.
"""

import gzip
import json
import time

import bson
import lz4.frame as lz4f
import numpy as np
import pandas as pd
from flask import Blueprint, Response, jsonify, request

from SharedData.API.constants import (
    DEFAULT_USER,
    ERROR_SLEEP_SECONDS,
)
from SharedData.API.utils import (
    apply_subfolder,
    make_empty_response,
    make_error_response,
    parse_bool_param,
)


# Blueprint definition
timeseries_bp = Blueprint('timeseries', __name__)


def init_timeseries_routes(shdata, authenticate_fn):
    """
    Initialize timeseries routes with required dependencies.
    
    Parameters:
        shdata: SharedData instance.
        authenticate_fn: Authentication function.
    """
    
    @timeseries_bp.route('/timeseries', methods=['GET'])
    def list_timeseries():
        """GET /api/timeseries - Returns a JSON list of timeseries metadata."""
        try:
            if not authenticate_fn(request, shdata):
                return jsonify({'error': 'unauthorized'}), 401
            keyword = request.args.get('keyword', '')
            user = request.args.get('user', DEFAULT_USER)
            
            timeseries_df = shdata.list_timeseries(keyword=keyword, user=user)
            
            if len(timeseries_df) == 0:
                return Response(status=204)
            
            timeseries_list = timeseries_df.reset_index().to_dict('records')
            
            for ts in timeseries_list:
                for key, value in ts.items():
                    if pd.isna(value):
                        ts[key] = None
                    elif isinstance(value, pd.Timestamp):
                        ts[key] = value.isoformat()
            
            response_data = json.dumps(timeseries_list).encode('utf-8')
            response = Response(response_data, mimetype='application/json')
            response.headers['Content-Length'] = len(response_data)
            return response
        except Exception as e:        
            error_data = json.dumps({'error': str(e).replace('\n', ' ')}).encode('utf-8')
            response = Response(error_data, status=500, mimetype='application/json')
            response.headers['Content-Length'] = len(error_data)
            response.headers['Error-Message'] = error_data
            return response        

    @timeseries_bp.route('/timeseries/<database>/<period>/<source>', methods=['HEAD'])
    def head_timeseries_source(database, period, source):
        """Check if a timeseries container exists and return metadata about its tags."""
        try:
            if not authenticate_fn(request, shdata):
                return Response(status=401)
            
            user = request.args.get('user', DEFAULT_USER)
            
            ts = shdata.timeseries(database, period, source, user=user)
            ts.load()
            tags = list(ts.tags.keys())
            
            response = Response(status=200)
            response.headers['Timeseries-Tags'] = ','.join(tags)
            response.headers['Timeseries-Database'] = database
            response.headers['Timeseries-Period'] = period
            response.headers['Timeseries-Source'] = source
            return response
            
        except Exception:
            return Response(status=404)
        
    @timeseries_bp.route('/timeseries/<database>/<period>/<source>', methods=['POST'])
    def create_timeseries_source(database, period, source):
        """Create a timeseries container for a specified database, period, and source."""
        try:
            if not authenticate_fn(request, shdata):
                return jsonify({'error': 'unauthorized'}), 401
            
            user = request.args.get('user', DEFAULT_USER)
            startdate = request.args.get('startdate')        
            
            startdate_obj = None
            if startdate:
                startdate_obj = pd.Timestamp(startdate)
                        
            shdata.timeseries(database, period, source, 
                             user=user, 
                             startDate=startdate_obj)
            
            response_data = json.dumps({
                'status': 'success', 
                'message': 'Timeseries container created',
                'database': database,
                'period': period,
                'source': source,
                'user': user
            }).encode('utf-8')
            
            response = Response(response_data, status=201, mimetype='application/json')
            response.headers['Content-Length'] = str(len(response_data))
            return response
            
        except Exception as e:
            return make_error_response(e)

    @timeseries_bp.route('/timeseries/<database>/<period>/<source>/write', methods=['PATCH'])
    def write_timeseries_source(database: str, period: str, source: str):
        """Triggers a write operation to persist all timeseries data for a specified source container."""
        try:
            if not authenticate_fn(request, shdata):
                return jsonify({'error': 'unauthorized'}), 401
                
            user = request.args.get('user', DEFAULT_USER)
            startdate = request.args.get('startdate')
            
            startdate_obj = None
            if startdate is not None:
                startdate_obj = pd.Timestamp(startdate)
            
            ts = shdata.timeseries(database, period, source, user=user, startDate=startdate)
            ts.write(startDate=startdate_obj)
            
            response_data = json.dumps({
                'status': 'success',
                'message': 'Timeseries source write operation completed',
                'database': database,
                'period': period,
                'source': source,
                'user': user,
                'startdate': startdate
            }).encode('utf-8')
            
            response = Response(response_data, status=200, mimetype='application/json')
            response.headers['Content-Length'] = str(len(response_data))
            return response
            
        except Exception as e:
            return make_error_response(e)

    @timeseries_bp.route('/timeseries/<database>/<period>/<source>', methods=['DELETE'])
    def delete_timeseries_source(database, period, source):
        """Delete all timeseries data for a specified database, period, and source."""
        try:
            if not authenticate_fn(request, shdata):
                return jsonify({'error': 'unauthorized'}), 401
            
            user = request.args.get('user', DEFAULT_USER)
            success = shdata.delete_timeseries(database, period, source, user=user)
            
            if success:
                return Response(status=204)
            else:
                return Response(status=404)
                
        except Exception as e:
            time.sleep(ERROR_SLEEP_SECONDS)
            response = Response(status=500)                
            response.headers['Error-Message'] = str(e).replace('\n', ' ')
            return response

    @timeseries_bp.route('/timeseries/<database>/<period>/<source>/<tag>', methods=['HEAD', 'GET', 'POST', 'DELETE', 'PATCH'])
    def timeseries(database, period, source, tag):
        """Handle CRUD operations on a specified timeseries within a database."""
        try:
            if not authenticate_fn(request, shdata):
                return jsonify({'error': 'unauthorized'}), 401
            
            if request.method == 'HEAD':
                return head_timeseries(database, period, source, tag, request)
            elif request.method == 'GET':
                return get_timeseries(database, period, source, tag, request)
            elif request.method == 'POST':
                return post_timeseries(database, period, source, tag, request)
            elif request.method == 'DELETE':
                return delete_timeseries(database, period, source, tag, request)
            elif request.method == 'PATCH':
                return write_timeseries(database, period, source, tag, request)
            else:
                return jsonify({'error': 'method not allowed'}), 405
            
        except Exception as e:
            time.sleep(ERROR_SLEEP_SECONDS)
            response = Response(status=500)                
            response.headers['Error-Message'] = str(e).replace('\n', ' ')
            return response

    def head_timeseries(database: str, period: str, source: str, tag: str, request):
        """Handle HTTP HEAD requests to provide metadata about a specified timeseries."""
        tagsubfolder = request.args.get('tagsubfolder')
        user = request.args.get('user', DEFAULT_USER)
        
        tagpath = apply_subfolder(tag, tagsubfolder)
        
        try:
            ts_data = shdata.timeseries(database, period, source, tagpath, user=user)
            
            if ts_data is None or len(ts_data) == 0:
                return Response(status=404)
            
            response = Response(status=200)
            response.headers["Timeseries-Columns"] = ",".join(ts_data.columns.tolist())
            response.headers["Timeseries-Start"] = ts_data.index.min().isoformat()
            response.headers["Timeseries-End"] = ts_data.index.max().isoformat()
            response.headers["Timeseries-Count"] = str(len(ts_data))
            response.headers["Timeseries-Period"] = period
            return response
            
        except Exception:
            return Response(status=404)

    def get_timeseries(database: str, period: str, source: str, tag: str, request):
        """Retrieve a timeseries dataset from a specified database and return it in the requested format."""
        tagsubfolder = request.args.get('tagsubfolder')
        user = request.args.get('user', DEFAULT_USER)
        startdate = request.args.get('startdate')
        enddate = request.args.get('enddate')
        columns = request.args.get('columns')
        output_format = request.args.get('format', 'bin').lower()
        dropna = parse_bool_param(request.args.get('dropna'), True)
        accept_encoding = request.headers.get('Accept-Encoding', '')
        
        tagpath = apply_subfolder(tag, tagsubfolder)
        
        try:
            ts_data = shdata.timeseries(database, period, source, tagpath, user=user)
            
            # Check for new columns that may have been added by other processes
            path = f'{user}/{database}/{period}/{source}/timeseries'
            ts_disk = shdata.data[path].tags[tagpath]
            ts_disk.check_for_new_columns()
            
            # Apply date filtering - create a copy to avoid modifying original data
            if startdate is not None:
                startdate = pd.Timestamp(startdate)
                ts_data = ts_data.loc[startdate:].copy()
                
            if enddate is not None:
                enddate = pd.Timestamp(enddate)
                ts_data = ts_data.loc[:enddate].copy()
                
            # Apply column filtering
            if columns is not None:
                columns_list = [s.strip() for s in columns.split(',')]
                columns_list = [s for s in columns_list if s in ts_data.columns]
                if columns_list:
                    ts_data = ts_data[columns_list].copy()
            
            # Drop rows that are all NaN (optional)
            if dropna:
                ts_data = ts_data.dropna(how='all')
            
            if len(ts_data) == 0:
                return make_empty_response(204)
            
            # Return data in requested format
            if output_format == 'csv':
                csv_data = ts_data.to_csv()
                if 'gzip' in accept_encoding:
                    response_csv = csv_data.encode('utf-8')
                    response_compressed = gzip.compress(response_csv, compresslevel=1)
                    response = Response(response_compressed, mimetype='text/csv')
                    response.headers['Content-Encoding'] = 'gzip'
                    response.headers['Content-Length'] = len(response_compressed)
                    return response
                else:
                    response_data = csv_data.encode('utf-8')
                    response = Response(response_data, mimetype='text/csv')
                    response.headers['Content-Length'] = len(response_data)
                    return response
                    
            elif output_format == 'bin':
                bson_payload = {
                    'index': ts_data.index.astype(np.int64).values.tobytes(),
                    'columns': ts_data.columns.tolist(),
                    'data': ts_data.values.astype(np.float64).tobytes(),
                    'shape': ts_data.shape
                }
                bson_data = bson.encode(bson_payload)
                compressed = lz4f.compress(bson_data)
                
                response = Response(compressed, mimetype='application/octet-stream')
                response.headers['Content-Encoding'] = 'lz4'
                response.headers['Content-Length'] = len(compressed)
                return response
                
            else:  # JSON format
                ts_json = ts_data.reset_index()
                ts_json['date'] = ts_json['date'].dt.isoformat()
                
                response_data = {
                    'tag': tagpath,
                    'period': period,
                    'total': len(ts_data),
                    'data': ts_json.to_dict(orient='records')
                }
                
                if 'gzip' in accept_encoding:
                    response_json = json.dumps(response_data).encode('utf-8')
                    response_compressed = gzip.compress(response_json, compresslevel=1)
                    response = Response(response_compressed, mimetype='application/json')
                    response.headers['Content-Encoding'] = 'gzip'
                    response.headers['Content-Length'] = len(response_compressed)
                    return response
                else:
                    response_json = json.dumps(response_data).encode('utf-8')
                    response = Response(response_json, mimetype='application/json')
                    response.headers['Content-Length'] = len(response_json)
                    return response
                    
        except Exception as e:
            return make_error_response(e)

    def post_timeseries(database: str, period: str, source: str, tag: str, request):
        """Handle a POST request to insert or update timeseries data."""
        tagsubfolder = request.args.get('tagsubfolder')
        user = request.args.get('user', DEFAULT_USER)
        columns = request.args.get('columns')
        overwrite = parse_bool_param(request.args.get('overwrite'), False)
        
        tagpath = apply_subfolder(tag, tagsubfolder)
        
        try:
            # Handle case where only columns are provided (create empty timeseries)
            if not request.data and columns:
                columns_list = columns.split(',')
                columns_idx = pd.Index(columns_list)
                
                shdata.timeseries(database, period, source, tagpath,
                                 user=user, columns=columns_idx, overwrite=overwrite)

                response_data = json.dumps({'status': 'success', 'tag': tagpath, 'message': 'Empty timeseries created with columns'}).encode('utf-8')
                response = Response(response_data, status=201, mimetype='application/json')
                response.headers['Content-Length'] = str(len(response_data))
                return response
            
            if not request.data:
                return jsonify({'message': 'No data provided'}), 400
            
            content_encoding = request.headers.get('Content-Encoding', '').lower()
            
            if content_encoding == 'lz4':
                decompressed = lz4f.decompress(request.data)
                data_payload = bson.decode(decompressed)
                
                if 'data' in data_payload and 'index' in data_payload and 'columns' in data_payload:
                    index_data = np.frombuffer(data_payload['index'], dtype=np.int64)
                    index = pd.to_datetime(index_data)
                    columns_list = data_payload['columns']
                    shape = data_payload['shape']
                    values = np.frombuffer(data_payload['data'], dtype=np.float64).reshape(shape)
                    df = pd.DataFrame(values, index=index, columns=columns_list)
                else:
                    df = pd.DataFrame(data_payload)
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.set_index('date')
            else:
                data = json.loads(request.data.decode('utf-8'))
                df = pd.DataFrame(data)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date')
            
            if not isinstance(df.index, pd.DatetimeIndex):
                return jsonify({'message': 'Data must have a datetime index'}), 400
            
            columns_list = df.columns.tolist() if columns is None else columns.split(',')
            columns_idx = pd.Index(columns_list)
            
            ts = shdata.timeseries(database, period, source, tagpath,
                             user=user, columns=columns_idx, value=df, overwrite=overwrite)

            # Check for new columns that don't exist in the timeseries
            new_columns = [col for col in df.columns if col not in ts.columns]
            appended_columns = []
            
            if new_columns:
                path = f'{user}/{database}/{period}/{source}/timeseries'
                if path in shdata.data:
                    ts_container = shdata.data[path]
                    if tagpath in ts_container.tags:
                        ts_disk = ts_container.tags[tagpath]
                        ts_disk.append_columns(new_columns)
                        appended_columns = new_columns
                        ts = ts_disk.data
            
            # Now write data to all columns (including newly appended ones)
            icols = df.columns.intersection(ts.columns)
            iindex = df.index.intersection(ts.index)
            ts.loc[iindex, icols] = df.loc[iindex, icols].values

            response_message = 'Timeseries updated'
            if appended_columns:
                response_message += f' (appended columns: {", ".join(appended_columns)})'
            
            response_data = json.dumps({'status': 'success', 'tag': tagpath, 'message': response_message, 'appended_columns': appended_columns}).encode('utf-8')
            response = Response(response_data, status=201, mimetype='application/json')
            response.headers['Content-Length'] = str(len(response_data))
            return response
            
        except Exception as e:
            return make_error_response(e)

    def delete_timeseries(database: str, period: str, source: str, tag: str, request):
        """Deletes a specified timeseries or a portion of it."""
        tagsubfolder = request.args.get('tagsubfolder')
        user = request.args.get('user', DEFAULT_USER)
        startdate = request.args.get('startdate')
        enddate = request.args.get('enddate')
        
        tagpath = apply_subfolder(tag, tagsubfolder)
        
        try:
            if startdate is not None or enddate is not None:
                ts_data = shdata.timeseries(database, period, source, tagpath, user=user)
                
                if ts_data is None or len(ts_data) == 0:
                    return Response(status=404)
                
                mask = pd.Series(True, index=ts_data.index)
                
                if startdate is not None:
                    startdate = pd.Timestamp(startdate)
                    mask = mask & (ts_data.index >= startdate)
                    
                if enddate is not None:
                    enddate = pd.Timestamp(enddate)
                    mask = mask & (ts_data.index <= enddate)
                
                ts_data.loc[mask, :] = np.nan
                
                shdata.timeseries(database, period, source, tagpath, 
                                 user=user, value=ts_data, overwrite=True)
                
                return Response(status=204)
            else:
                shdata.delete_timeseries(database, period, source, tagpath, user=user)
                return Response(status=204)
                
        except Exception:
            return Response(status=404)

    def write_timeseries(database: str, period: str, source: str, tag: str, request):
        """Triggers a write operation for a specified timeseries, persisting data to disk or S3."""
        tagsubfolder = request.args.get('tagsubfolder')
        user = request.args.get('user', DEFAULT_USER)
        startdate = request.args.get('startdate')
        
        tagpath = apply_subfolder(tag, tagsubfolder)
        
        try:
            path = f'{user}/{database}/{period}/{source}/timeseries'
            
            if path not in shdata.data:
                return Response(status=404)
            
            ts_container = shdata.data[path]
            
            if ts_container is None:
                return Response(status=404)
            
            startdate_obj = None
            if startdate is not None:
                startdate_obj = pd.Timestamp(startdate)
            
            ts_container.write(startDate=startdate_obj)
            
            response_data = json.dumps({
                'status': 'success',
                'message': 'Timeseries write operation completed',
                'database': database,
                'period': period,
                'source': source,
                'tag': tagpath,
                'user': user,
                'startdate': startdate
            }).encode('utf-8')
            
            response = Response(response_data, status=200, mimetype='application/json')
            response.headers['Content-Length'] = str(len(response_data))
            return response
            
        except Exception as e:
            return make_error_response(e)

    return timeseries_bp
