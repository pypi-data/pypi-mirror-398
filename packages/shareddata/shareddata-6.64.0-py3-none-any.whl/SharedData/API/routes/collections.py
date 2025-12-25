"""
Collection routes blueprint for ServerAPI.
"""

import datetime
import gzip
import json
import time

import bson
from bson import json_util
from bson.objectid import ObjectId
import lz4.frame as lz4f
import pandas as pd
import pymongo
from flask import Blueprint, Response, jsonify, request

from SharedData.CollectionMongoDB import CollectionMongoDB
from SharedData.Database import DATABASE_PKEYS

from SharedData.API.constants import (
    DEFAULT_USER,
    DEFAULT_PAGE_SIZE,
    ERROR_SLEEP_SECONDS,
)
from SharedData.API.utils import (
    apply_subfolder,
    make_empty_response,
    parse_bool_param,
    parse_int_param,
)


# Blueprint definition
collections_bp = Blueprint('collections', __name__)

def parse_json_query(query: dict) -> dict:
    """
    Recursively parses a MongoDB-like query dictionary, converting string representations 
    of '_id' fields to `ObjectId` instances and 'date' fields to `pandas.Timestamp` objects.
    
    Parameters:
        query (dict): The MongoDB-like query dictionary to parse.
    
    Returns:
        dict: The parsed query dictionary with '_id' fields as `ObjectId` and 'date' fields as `pandas.Timestamp`.
    """
    for key in list(query.keys()):
        value = query[key]
        if key == '_id':
            if isinstance(value, dict):
                for op_key, op_value in value.items():
                    if op_key.startswith('$'):
                        try:
                            if op_key == '$in' and isinstance(op_value, list):
                                value[op_key] = [ObjectId(str(item)) for item in op_value]
                            else:
                                value[op_key] = ObjectId(str(op_value))
                        except Exception:
                            pass
                    elif isinstance(op_value, dict):
                        value[op_key] = parse_json_query({op_key: op_value})[op_key]
            else:
                query[key] = ObjectId(str(value))
        elif key == 'date':
            if isinstance(value, dict):
                for op_key, op_value in value.items():
                    if op_key.startswith('$'):
                        try:
                            value[op_key] = pd.Timestamp(op_value)
                        except Exception:
                            pass
                    elif isinstance(op_value, dict):
                        value[op_key] = parse_json_query({op_key: op_value})[op_key]
            else:
                try:
                    query[key] = pd.Timestamp(value)
                except Exception:
                    pass
        elif isinstance(value, dict):
            query[key] = parse_json_query(value)
    return query


def init_collections_routes(shdata, authenticate_fn):
    """
    Initialize collection routes with required dependencies.
    
    Parameters:
        shdata: SharedData instance.
        authenticate_fn: Authentication function.
    """
    
    @collections_bp.route('/collections', methods=['GET'])
    def list_collections():
        """GET endpoint to retrieve a list of collections."""
        try:
            if not authenticate_fn(request, shdata):
                return jsonify({'error': 'unauthorized'}), 401
            keyword = request.args.get('keyword', '')
            user = request.args.get('user', DEFAULT_USER)
            collections = shdata.list_collections(keyword=keyword, user=user)
            if collections.empty:
                return Response(status=204)
            collections = collections.reset_index().to_dict('records')
            collections = CollectionMongoDB.serialize(collections, iso_dates=True)
            response_data = json.dumps(collections).encode('utf-8')
            response = Response(response_data, mimetype='application/json')        
            return response
        except Exception as e:        
            response = Response(status=500)
            error_data = json.dumps({'error': str(e).replace('\n', ' ')}).encode('utf-8')
            response.headers['Error-Message'] = error_data
            return response

    @collections_bp.route('/collection/<database>/<period>/<source>/<tablename>', methods=['HEAD', 'GET', 'POST', 'PATCH', 'DELETE'])
    def collection(database, period, source, tablename):
        """Handle CRUD operations on a specified collection within a database."""
        try:
            if not authenticate_fn(request, shdata):
                return jsonify({'error': 'unauthorized'}), 401
            
            if request.method == 'HEAD':
                return head_collection(database, period, source, tablename, request)
            elif request.method == 'GET':
                return get_collection(database, period, source, tablename, request)
            elif request.method == 'POST':
                return post_collection(database, period, source, tablename, request)
            elif request.method == 'PATCH':
                return patch_collection(database, period, source, tablename, request)        
            elif request.method == 'DELETE':
                return delete_collection(database, period, source, tablename, request)
            else:
                return jsonify({'error': 'method not allowed'}), 405
            
        except Exception as e:
            time.sleep(ERROR_SLEEP_SECONDS)
            response = Response(status=500)                
            response.headers['Error-Message'] = str(e).replace('\n', ' ')
            return response
        
    def head_collection(database: str, period: str, source: str, tablename: str, request):
        """Handle HTTP HEAD requests by returning metadata headers for a specified MongoDB collection."""
        user = request.args.get('user', DEFAULT_USER)
        tablesubfolder = request.args.get('tablesubfolder')
        tablepath = apply_subfolder(tablename, tablesubfolder)

        collection = shdata.collection(database, period, source, tablepath, user=user, create_if_not_exists=False)

        sample_size = 10000
        try:
            cursor = collection.collection.aggregate([{"$sample": {"size": sample_size}}])
        except Exception:
            cursor = collection.find({}, limit=sample_size)
        
        field_set = set()
        for doc in cursor:
            field_set.update(doc.keys())
        doc_fields = sorted(field_set)

        pkey = DATABASE_PKEYS[database] if database in DATABASE_PKEYS else []
        try:
            count = collection.collection.estimated_document_count()
        except Exception:
            count = collection.collection.count_documents({})
        response = Response(status=200)
        response.headers["Collection-Count"] = str(count)
        response.headers["Collection-Fields"] = ",".join(doc_fields)
        response.headers["Collection-Pkey"] = ",".join(pkey)
        return response    

    def get_collection(database, period, source, tablename, request):
        """Retrieve and return a collection from the specified database with filtering, sorting, pagination, and formatting options."""
        user = request.args.get('user', DEFAULT_USER)
        tablesubfolder = request.args.get('tablesubfolder')
        query = request.args.get('query')
        if query:
            query = json_util.loads(query)
        else:
            query = {}        
        sort = request.args.get('sort')
        if sort:
            sort = json_util.loads(sort)
        else:
            sort = {}
        columns = request.args.get('columns')
        projection = None
        if columns:
            columns = json_util.loads(columns)
            projection = {f.strip(): 1 for f in columns.split(',')}
            for pkey in DATABASE_PKEYS[database]:
                projection[pkey] = 1

        page = parse_int_param(request.args.get('page'), 1)
        per_page = parse_int_param(request.args.get('per_page'), DEFAULT_PAGE_SIZE)
        output_format = request.args.get('format', 'bson').lower()
        accept_encoding = request.headers.get('Accept-Encoding', '')
        
        tablepath = apply_subfolder(tablename, tablesubfolder)
        collection = shdata.collection(database, period, source, tablepath, user=user,
                                       create_if_not_exists=False)

        query = parse_json_query(query)
        result = collection.find(query, sort=sort, limit=per_page, skip=(page - 1) * per_page, projection=projection)
        if len(result) == 0:
            return make_empty_response(204)
        
        if output_format == 'bson':
            bson_data = bson.encode({'data': list(result)})
            compressed_data = lz4f.compress(bson_data)

            response = Response(compressed_data, mimetype='application/octet-stream')
            response.headers['Content-Encoding'] = 'lz4'
            response.headers['Content-Length'] = len(compressed_data)
            response.headers['Content-Type'] = 'application/octet-stream'
            return response

        elif output_format == 'csv':
            df = collection.documents2df(result)
            csv_data = df.to_csv()
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
        else:
            pkey = ''
            if database in DATABASE_PKEYS:
                pkey = DATABASE_PKEYS[database]
            response_data = {
                'page': page,
                'per_page': per_page,
                'total': len(result),
                'pkey': pkey,
                'data': collection.documents2json(result)
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

    def post_collection(database, period, source, tablename, request):    
        """Handle a POST request to insert or upsert a collection of documents."""
        tablesubfolder = request.args.get('tablesubfolder')
        user = request.args.get('user', DEFAULT_USER)
        hasindex = parse_bool_param(request.args.get('hasindex'), True)

        tablepath = apply_subfolder(tablename, tablesubfolder)

        collection = shdata.collection(database, period, source, tablepath, user=user, hasindex=hasindex)

        if not request.data:
            Response({'message': 'No data'}, status=400)
        
        if request.headers.get('Content-Encoding', '').lower() == 'lz4':
            decompressed = lz4f.decompress(request.data)
            documents = bson.decode(decompressed)['data']
        else:
            documents = json.loads(request.data)

        if not isinstance(documents, list):
            Response({'message': 'Data must be a list'}, status=400)
        
        if hasindex:
            collection.upsert(documents)
        else:
            collection.extend(documents)

        response_data = json.dumps({'status': 'success'}).encode('utf-8')
        response = Response(response_data, status=201, mimetype='application/json')
        response.headers['Content-Length'] = str(len(response_data))
        return response   

    def patch_collection(database, period, source, tablename, request):
        """Update a single document in a specified collection within the database."""
        pkey = ''
        if database in DATABASE_PKEYS:
            pkey = DATABASE_PKEYS[database]
        else:
            error_data = json.dumps({'error': 'database not found'}).encode('utf-8')
            response = Response(error_data, status=400, mimetype='application/json')
            response.headers['Content-Length'] = len(error_data)
            return response
        
        user = request.args.get('user', DEFAULT_USER)
        tablesubfolder = request.args.get('tablesubfolder')
        tablepath = apply_subfolder(tablename, tablesubfolder)
        collection = shdata.collection(database, period, source, tablepath, user=user)
        
        filter_param = request.args.get('filter')
        if filter_param is None:
            error_data = json.dumps({'error': 'filter is required'}).encode('utf-8')
            response = Response(error_data, status=400, mimetype='application/json')
            response.headers['Content-Length'] = len(error_data)
            return response    
        filter_param = json.loads(filter_param)
        filter_param = parse_json_query(filter_param)
        
        update = request.args.get('update')
        if update is None:
            error_data = json.dumps({'error': 'update is required'}).encode('utf-8')
            response = Response(error_data, status=400, mimetype='application/json')
            response.headers['Content-Length'] = len(error_data)
            return response
        update = json.loads(update)

        sort = request.args.get('sort')    
        if sort:
            sort = json.loads(sort)
        else:
            sort = {}
        
        coll = collection.collection
        res = coll.find_one_and_update(
            filter=filter_param, 
            update=update, 
            sort=sort, 
            return_document=pymongo.ReturnDocument.AFTER)
        
        if res:
            if '_id' in res:
                res['_id'] = str(res['_id'])
            
            for key in res:
                if pd.api.types.is_datetime64_any_dtype(res[key]) or isinstance(res[key], datetime.datetime):
                    res[key] = res[key].isoformat()
            response_data = {
                'pkey': pkey,
                'data': json.dumps(res),
            }
            response_json = json.dumps(response_data).encode('utf-8')
            response = Response(response_json, mimetype='application/json')
            response.headers['Content-Length'] = len(response_json)
            return response
        else:
            return make_empty_response(204)

    def delete_collection(database, period, source, tablename, request):
        """Deletes a specific collection or documents within a collection from the database."""
        user = request.args.get('user', DEFAULT_USER)
        tablesubfolder = request.args.get('tablesubfolder')
        tablepath = apply_subfolder(tablename, tablesubfolder)

        query = request.args.get('query')
        if query:        
            query = json.loads(query) 
            query = parse_json_query(query)
            collection = shdata.collection(database, period, source, tablepath, user=user, create_if_not_exists=False)
            result = collection.collection.delete_many(query)
            if result.deleted_count > 0:
                return Response(status=204)
            else:
                return Response(status=404)
        else:
            success = shdata.delete_collection(database, period, source, tablepath, user=user)
            if success:
                return Response(status=204)
            else:
                return Response(status=404)

    return collections_bp
