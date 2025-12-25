"""
Table routes blueprint for ServerAPI.
"""

import datetime
import gzip
import json
import time

import bson
import lz4.frame as lz4f
import numpy as np
import pandas as pd
from flask import Blueprint, Response, jsonify, request

from SharedData.CollectionMongoDB import CollectionMongoDB
from SharedData.Database import DATABASE_PKEYS

from SharedData.API.constants import (
    DEFAULT_USER,
    ERROR_SLEEP_SECONDS,
    MAX_RESPONSE_SIZE_BYTES,
)
from SharedData.API.utils import (
    apply_subfolder,
    make_empty_response,
    make_error_response,
    parse_bool_param,
    parse_int_param,
    parse_json_param,
)


# Blueprint definition
tables_bp = Blueprint('tables', __name__)


def init_tables_routes(shdata, authenticate_fn):
    """
    Initialize table routes with required dependencies.
    
    Parameters:
        shdata: SharedData instance.
        authenticate_fn: Authentication function.
    """
    
    @tables_bp.route('/tables', methods=['GET'])
    def list_tables():
        """
        GET /api/tables - Returns a JSON list of tables filtered by optional query parameters.
        """
        try:
            if not authenticate_fn(request, shdata):
                return jsonify({'error': 'unauthorized'}), 401

            keyword = request.args.get('keyword', '')
            user = request.args.get('user', DEFAULT_USER)

            tables = shdata.list_tables(keyword=keyword, user=user)
            if tables.empty:
                return Response(status=204)
            tables = tables.reset_index().to_dict('records')        
            tables = CollectionMongoDB.serialize(tables, iso_dates=True)
            response_data = json.dumps(tables).encode('utf-8')
            response = Response(response_data, mimetype='application/json')
            response.headers['Content-Length'] = len(response_data)
            return response

        except Exception as e:
            response = Response(status=500)
            error_data = json.dumps({'error': str(e).replace('\n', ' ')}).encode('utf-8')
            response.headers['Error-Message'] = error_data
            return response

    @tables_bp.route('/table/<database>/<period>/<source>/<tablename>', methods=['HEAD', 'GET', 'POST', 'DELETE', 'PATCH'])
    def table(database, period, source, tablename):
        """
        Handle CRUD operations on a specified table within a database.
        """
        try:
            if not authenticate_fn(request, shdata):
                return jsonify({'error': 'unauthorized'}), 401

            if request.method == 'HEAD':
                return head_table(database, period, source, tablename, request)                
            elif request.method == 'GET':
                return get_table(database, period, source, tablename, request)        
            elif request.method == 'POST':
                return post_table(database, period, source, tablename, request)
            elif request.method == 'DELETE':
                return delete_table(database, period, source, tablename, request)
            elif request.method == 'PATCH':
                return write_table(database, period, source, tablename, request)
            else:
                return jsonify({'error': 'method not allowed'}), 405
            
        except Exception as e:
            time.sleep(ERROR_SLEEP_SECONDS)
            response = Response(status=500)                
            response.headers['Error-Message'] = str(e).replace('\n', ' ')
            return response

    def head_table(database, period, source, tablename, request):
        """Generate an HTTP response containing header metadata from a specified table."""
        tablesubfolder = request.args.get('tablesubfolder')    
        user = request.args.get('user', default=DEFAULT_USER)
        
        tablepath = apply_subfolder(tablename, tablesubfolder)
        tbl = shdata.table(database, period, source, tablepath, user=user)
        hdr = tbl.table.hdr    
        hdrdict = {name: hdr[name].item() if hasattr(hdr[name], 'item') else hdr[name]
                   for name in hdr.dtype.names}
        response = Response(200)    
        for key, value in hdrdict.items():
            response.headers['Table-' + key] = value    
        return response

    def get_table(database, period, source, tablename, request):
        """Retrieve and filter data from a specified table in the database."""
        tablesubfolder = request.args.get('tablesubfolder')
        startdate = request.args.get('startdate')
        enddate = request.args.get('enddate')
        symbols = request.args.get('symbols')
        portfolios = request.args.get('portfolios')
        tags = request.args.get('tags')
        page = parse_int_param(request.args.get('page'), 1)
        per_page = parse_int_param(request.args.get('per_page'), 0)
        output_format = request.args.get('format', 'json').lower()
        query = parse_json_param(request.args.get('query'), {})
        user = request.args.get('user', default=DEFAULT_USER)

        tablepath = apply_subfolder(tablename, tablesubfolder)
        tbl = shdata.table(database, period, source, tablepath, user=user)
        
        loc = None

        if startdate is not None and enddate is not None:
            startdate = pd.Timestamp(startdate)
            enddate = pd.Timestamp(enddate)
            loc = tbl.get_date_loc_gte_lte(startdate, enddate)
        elif startdate is not None:
            startdate = pd.Timestamp(startdate)
            loc = tbl.get_date_loc_gte(startdate)            
        elif enddate is not None:
            enddate = pd.Timestamp(enddate)
            loc = tbl.get_date_loc_lte(enddate)        
        else:
            loc = np.arange(tbl.count)

        if len(loc) == 0:
            return make_empty_response(204)
        
        # filter data by symbols    
        if symbols is not None:
            symbols = symbols.split(',')
            symbolloc = []
            for symbol in symbols:
                symbolloc.extend(tbl.get_symbol_loc(symbol))
            symbolloc = np.array(symbolloc)
            if len(symbolloc) > 0:
                loc = np.intersect1d(loc, symbolloc)
            else:
                loc = np.array([])

        # filter data by portfolios
        if portfolios is not None:
            portfolios = portfolios.split(',')
            portloc = []
            for port in portfolios:
                portloc.extend(tbl.get_portfolio_loc(port))
            portloc = np.array(portloc)
            if len(portloc) > 0:
                loc = np.intersect1d(loc, portloc)
            else:
                loc = np.array([])

        # filter data by tags
        if tags is not None:
            tags = tags.split(',')
            tagloc = []
            for tag in tags:
                tagloc.extend(tbl.get_tag_loc(tag))
            tagloc = np.array(tagloc)
            if len(tagloc) > 0:
                loc = np.intersect1d(loc, tagloc)
            else:
                loc = np.array([])
        
        if loc is not None:
            loc = np.array(loc)
        
        # cycle query keys
        if query.keys() is not None:        
            for key in query.keys():            
                if pd.api.types.is_string_dtype(tbl[key]):
                    idx = tbl[loc][key] == query[key].encode()
                elif pd.api.types.is_datetime64_any_dtype(tbl[key]):
                    idx = tbl[loc][key] == pd.Timestamp(query[key])
                else:                    
                    idx = tbl[loc][key] == query[key]
                loc = loc[idx]
        
        if len(loc) == 0:
            return make_empty_response(204)
        
        # filter columns
        pkey = DATABASE_PKEYS[database]
        columns = request.args.get('columns')
        if columns:
            if not tbl.is_schemaless:
                columns = columns.split(',')
                columns = np.array([c for c in columns if c not in pkey])
                columns = pkey + list(np.unique(columns))
                names = columns
                formats = [tbl.dtype.fields[name][0].str for name in names]
                dtype = np.dtype(list(zip(names, formats)))
                # Apply pagination    
                maxrows = int(np.floor(MAX_RESPONSE_SIZE_BYTES / dtype.itemsize))
                maxrows = min(maxrows, len(loc))
                if (per_page > maxrows) | (per_page == 0):
                    per_page = maxrows        
                startpage = (page - 1) * per_page
                endpage = startpage + per_page        
                content_pages = int(np.ceil(len(loc) / per_page))
                recs2send = tbl[loc[startpage:endpage]]
                # Create new array
                arrays = [recs2send[field] for field in columns]
                recs2send = np.rec.fromarrays(arrays, dtype=dtype)
            else:
                pass
        else:
            # Apply pagination    
            maxrows = int(np.floor(MAX_RESPONSE_SIZE_BYTES / tbl.itemsize))
            maxrows = min(maxrows, len(loc))
            if (per_page > maxrows) | (per_page == 0):
                per_page = maxrows
            startpage = (page - 1) * per_page
            endpage = startpage + per_page        
            content_pages = int(np.ceil(len(loc) / per_page))
            recs2send = tbl[loc[startpage:endpage]]
        
        # send response
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if output_format == 'csv':
            # Return CSV
            df = tbl.records2df(recs2send)
            df = df.reset_index()
            csv_data = df.to_csv(index=False)
            if 'gzip' in accept_encoding:
                response_csv = csv_data.encode('utf-8')
                response_compressed = gzip.compress(response_csv, compresslevel=1)
                response = Response(response_compressed, mimetype='text/csv')
                response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Length'] = len(response_compressed)
                response.headers['Content-Pages'] = content_pages
                return response
            else:
                response_data = csv_data.encode('utf-8')
                response = Response(response_data, mimetype='text/csv')
                response.headers['Content-Length'] = len(response_data)
                return response
        elif output_format == 'json':
            # Return JSON
            df = tbl.records2df(recs2send)
            pkey = df.index.names
            df = df.reset_index()
            df = df.applymap(lambda x: x.isoformat() if isinstance(x, datetime.datetime) else x)
            response_data = {
                'page': page,
                'per_page': per_page,
                'total': len(loc),
                'pkey': pkey,
                'data': df.to_dict(orient='records')
            }
            if 'gzip' in accept_encoding:
                response_json = json.dumps(response_data).encode('utf-8')
                response_compressed = gzip.compress(response_json, compresslevel=1)
                response = Response(response_compressed, mimetype='application/json')
                response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Length'] = len(response_compressed)
                response.headers['Content-Pages'] = content_pages
                return response
            else:
                response_data_json = json.dumps(response_data).encode('utf-8')
                response = Response(response_data_json, mimetype='application/json')
                response.headers['Content-Length'] = len(response_data_json)
                return response
        else:  # output_format=='bin'
            names = list(recs2send.dtype.names)
            formats = [recs2send.dtype.fields[name][0].str for name in names]

            dict_list = []
            if tbl.is_schemaless:
                dict_list = tbl.get_dict_list(loc[startpage:endpage])
                if columns:
                    columns = columns.split(',')
                    filtered_dict_list = []
                    for record in dict_list:
                        filtered_record = {col: record[col] for col in columns if col in record}
                        filtered_dict_list.append(filtered_record)

            json_payload = {
                'names': names,
                'formats': formats,
                'pkey': DATABASE_PKEYS[database],            
            }
            if not tbl.is_schemaless:
                json_payload['data'] = recs2send.tobytes()
            else:            
                json_payload['dict_list'] = dict_list

            bson_payload = bson.BSON.encode(json_payload)
            compressed = lz4f.compress(bson_payload)
            
            response = Response(compressed, mimetype='application/octet-stream')
            response.headers['Content-Encoding'] = 'lz4'        
            response.headers['Content-Pages'] = content_pages        
            return response

    def post_table(database, period, source, tablename, request):
        """Handles a POST request to create or update a table in the specified database."""
        tablesubfolder = request.args.get('tablesubfolder')
        overwrite = parse_bool_param(request.args.get('overwrite'), False)
        user = request.args.get('user', DEFAULT_USER)
        hasindex = parse_bool_param(request.args.get('hasindex'), True)
        is_schemaless = parse_bool_param(request.args.get('is_schemaless'), False)

        value = None
        if not request.data:
            raise Exception('No data provided')
        
        content_encoding = request.headers.get('Content-Encoding', "")
        if content_encoding != 'lz4':
            raise Exception('Content-Encoding must be lz4')
        
        data = lz4f.decompress(request.data)
        json_payload = bson.decode(data)
        names = json_payload.get('names')
        formats = json_payload.get('formats')
        size = json_payload.get('size')
            
        value = None
        if 'data' in json_payload:
            meta_names = json_payload['meta_names']
            meta_formats = json_payload['meta_formats']
            dtype = np.dtype(list(zip(meta_names, meta_formats)))
            value = np.frombuffer(json_payload['data'], dtype=dtype).copy()
        elif 'dict_list' in json_payload:
            value = json_payload['dict_list']
                    
        tablepath = apply_subfolder(tablename, tablesubfolder)
                
        if names is None or formats is None:
            tbl = shdata.table(database, period, source, tablepath,
                            names=names, formats=formats, size=size,
                            overwrite=overwrite, user=user, value=value, 
                            hasindex=hasindex, is_schemaless=is_schemaless)
        else:
            tbl = shdata.table(database, period, source, tablepath,
                            names=names, formats=formats, size=size,
                            overwrite=overwrite, user=user, value=None, 
                            hasindex=hasindex, is_schemaless=is_schemaless)
            if value is not None:
                if tbl.hasindex:
                    tbl.upsert(value)
                else:
                    tbl = tbl.extend(value)
                
        if size is not None:
            if tbl.size < size:
                tbl.free()
                tbl = shdata.table(database, period, source, tablepath,
                    names=names, formats=formats, size=size,
                    overwrite=overwrite, user=user, 
                    hasindex=hasindex, is_schemaless=is_schemaless)
                
        response = Response(status=201)
        response.headers['Content-Length'] = 0
        return response

    def delete_table(database, period, source, tablename, request):
        """Deletes a specified table from the given database, period, and source."""
        tablesubfolder = request.args.get('tablesubfolder')
        user = request.args.get('user', DEFAULT_USER)
        tablepath = apply_subfolder(tablename, tablesubfolder)
        success = shdata.delete_table(database, period, source, tablepath, user=user)
        if success:
            return Response(status=204)
        else:
            return Response(status=404)

    def write_table(database, period, source, tablename, request):
        """Triggers a write operation for a specified table, persisting data to disk or S3."""
        tablesubfolder = request.args.get('tablesubfolder')
        user = request.args.get('user', DEFAULT_USER)
        force_write = parse_bool_param(request.args.get('force_write'), False)
        
        tablepath = apply_subfolder(tablename, tablesubfolder)
        
        try:
            tbl = shdata.table(database, period, source, tablepath, user=user)
            
            if tbl is None:
                return Response(status=404)
                        
            tbl.write(force_write=force_write)
            
            response_data = json.dumps({
                'status': 'success',
                'message': 'Table write operation completed',
                'database': database,
                'period': period,
                'source': source,
                'tablename': tablepath,
                'user': user,
                'force_write': force_write
            }).encode('utf-8')
            
            response = Response(response_data, status=200, mimetype='application/json')
            response.headers['Content-Length'] = str(len(response_data))
            return response
            
        except Exception as e:
            return make_error_response(e)

    return tables_bp
