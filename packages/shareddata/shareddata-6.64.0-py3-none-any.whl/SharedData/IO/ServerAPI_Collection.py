
# Import all common variables, functions, and the Flask app
from SharedData.IO.ServerAPI_Common import *

@app.route('/api/collections', methods=['GET'])
def list_collections():
    """
    GET endpoint to retrieve a list of collections.
    
    Optional query parameters:
    - keyword (str): Filter collections by keyword in their names.
    - user (str): Specify the user whose collections to list; defaults to 'master'.
    
    Returns:
    - 200 OK with a JSON array of collection details if collections are found.
    - 204 No Content if no collections match the criteria.
    - 401 Unauthorized if authentication fails.
    - 500 Internal Server Error if an exception occurs.
    
    The response JSON contains serialized collection information with ISO-formatted dates.
    """
    try:
        if not authenticate(request):
            return jsonify({'error': 'unauthorized'}), 401
        keyword = request.args.get('keyword', '')
        user = request.args.get('user', 'master')
        collections = shdata.list_collections(keyword=keyword, user=user)
        if collections.empty:
            return Response(status=204)
        collections = collections.reset_index().to_dict('records')
        collections = CollectionMongoDB.serialize(collections,iso_dates=True)
        response_data = json.dumps(collections).encode('utf-8')
        response = Response(response_data, mimetype='application/json')        
        return response
    except Exception as e:        
        response = Response(status=500)
        error_data = json.dumps({'error': str(e).replace('\n', ' ')}).encode('utf-8')
        response.headers['Error-Message'] = error_data
        return response

def parse_json_query(query: dict) -> dict:
    """
    Recursively parses a MongoDB-like query dictionary, converting string representations of '_id' fields to `ObjectId` instances and 'date' fields to `pandas.Timestamp` objects.
    
    This function handles nested dictionaries and MongoDB query operators such as `$gte`, `$lte`, `$in`, and others by applying the appropriate conversions to their values. It modifies the input dictionary in place and returns the updated dictionary.
    
    Parameters:
        query (dict): The MongoDB-like query dictionary to parse.
    
    Returns:
        dict: The parsed query dictionary with '_id' fields as `ObjectId` and 'date' fields as `pandas.Timestamp`.
    """
    for key in list(query.keys()):
        value = query[key]
        if key == '_id':
            if isinstance(value, dict):
                # Handle MongoDB operators like $gte, $lte, $in, etc.
                for op_key, op_value in value.items():
                    if op_key.startswith('$'):
                        try:
                            if op_key == '$in' and isinstance(op_value, list):
                                # Handle $in operator with list of _id values
                                value[op_key] = [ObjectId(str(item)) for item in op_value]
                            else:
                                # Handle other operators like $gte, $lte, $ne, etc.
                                value[op_key] = ObjectId(str(op_value))
                        except Exception:
                            pass
                    elif isinstance(op_value, dict):
                        value[op_key] = parse_json_query({op_key: op_value})[op_key]
            else:
                query[key] = ObjectId(str(value))
        elif key == 'date':
            if isinstance(value, dict):
                # Handle MongoDB operators like $gte, $lte, etc.
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

@app.route('/api/collection/<database>/<period>/<source>/<tablename>', methods=['HEAD','GET', 'POST', 'PATCH', 'DELETE'])
@swag_from(docspath)
def collection(database, period, source, tablename):
    """
    Handle CRUD operations on a specified collection within a database.
    
    This endpoint supports HEAD, GET, POST, PATCH, and DELETE HTTP methods to interact with a collection identified by the given database, period, source, and tablename parameters.
    
    Authentication is required for all requests. If authentication fails, a 401 Unauthorized response is returned.
    
    Parameters:
    - database (str): The name of the database.
    - period (str): The period identifier.
    - source (str): The source identifier.
    - tablename (str): The name of the table or collection.
    
    Returns:
    - JSON response with the result of the requested operation.
    - 401 Unauthorized if authentication fails.
    - 405 Method Not Allowed if the HTTP method is not supported.
    - 500 Internal Server Error with error details if an exception occurs.
    """
    try:
        if not authenticate(request):
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
        time.sleep(1)  # Sleep for 1 second before returning the error        
        response = Response(status=500)                
        response.headers['Error-Message'] = str(e).replace('\n', ' ')
        return response
    
def head_collection(database: str, period: str, source: str, tablename: str, request):
    """
    Handle HTTP HEAD requests by returning metadata headers for a specified MongoDB collection.
    
    This function retrieves a random sample of documents from the collection to determine the set of fields present.
    It then responds with headers indicating the total document count, the fields found in the sample, and the primary keys for the database.
    
    Parameters:
    - database (str): The name of the database.
    - period (str): The period or time frame identifier.
    - source (str): The data source identifier.
    - tablename (str): The name of the collection or table.
    - request: The HTTP request object containing query parameters.
    
    Returns:
    - Response: An HTTP response with status 200 and headers:
        - "Collection-Count": Estimated or exact count of documents in the collection.
        - "Collection-Fields": Comma-separated list of fields found in the sampled documents.
        - "Collection-Pkey": Comma-separated list of primary key fields for the database.
    """
    user = request.args.get('user', 'master')
    tablesubfolder = request.args.get('tablesubfolder')  # Optional
    if tablesubfolder:
        tablename = f"{tablename}/{tablesubfolder}"

    collection = shdata.collection(database, period, source, tablename, user=user, create_if_not_exists=False)

    sample_size = 10000  # or any number you want
    # Get a random sample using $sample
    try:
        cursor = collection.collection.aggregate([{"$sample": {"size": sample_size}}])
    except Exception:
        # fallback in case $sample is not supported, e.g. very small collections
        cursor = collection.find({}, limit=sample_size)
    
    field_set = set()
    for doc in cursor:
        field_set.update(doc.keys())
    doc_fields = sorted(field_set)

    pkey = DATABASE_PKEYS[database] if database in DATABASE_PKEYS else []
    try:
        count = collection.collection.estimated_document_count()
    except Exception:
        # fallback to slow but accurate if estimate fails
        count = collection.collection.count_documents({})
    response = Response(status=200)
    response.headers["Collection-Count"] = str(count)
    response.headers["Collection-Fields"] = ",".join(doc_fields)
    response.headers["Collection-Pkey"] = ",".join(pkey)
    return response    

def get_collection(database, period, source, tablename, request):
    # Get the collection    
    """
    Retrieve and return a collection from the specified database with filtering, sorting, pagination, and formatting options.
    
    Parameters:
    - database (str): The name of the database to query.
    - period (str): The period or partition of the database.
    - source (str): The data source identifier.
    - tablename (str): The name of the table or collection to query.
    - request (flask.Request): The Flask request object containing query parameters and headers.
    
    Query Parameters (via request.args):
    - user (str, optional): User identifier for access control, defaults to 'master'.
    - tablesubfolder (str, optional): Subfolder appended to the tablename.
    - query (str, optional): JSON-encoded query filter for MongoDB.
    - sort (str, optional): JSON-encoded sort specification.
    - columns (str, optional): Comma-separated list of columns to include in the result.
    - page (int, optional): Page number for pagination, defaults to 1.
    - per_page (int, optional): Number of items per page, defaults to 10000.
    - format (str, optional): Output format, one of 'bson' (default), 'json', or 'csv'.
    
    Headers:
    - Accept-Encoding: Used to determine if gzip
    """
    user = request.args.get('user', 'master')  # Optional
    tablesubfolder = request.args.get('tablesubfolder')  # Optional
    query = request.args.get('query')
    if query:
        query = json_util.loads(query)  # Optional
    else:
        query = {}        
    sort = request.args.get('sort')  # Optional        
    if sort:
        sort = json_util.loads(sort)
    else:
        sort = {}
    columns = request.args.get('columns')  # Optional
    projection = None
    if columns:
        columns = json_util.loads(columns)
        projection = {f.strip(): 1 for f in columns.split(',')}
        for pkey in DATABASE_PKEYS[database]:
            projection[pkey] = 1

    page = request.args.get('page', default='1')
    page = int(float(page))
    per_page = request.args.get('per_page', default='10000')
    per_page = int(float(per_page))
    output_format = request.args.get('format', 'bson').lower()  # 'json' by default, can be 'csv'
    accept_encoding = request.headers.get('Accept-Encoding', '')
    
    if tablesubfolder is not None:
        tablename = tablename+'/'+tablesubfolder
    collection = shdata.collection(database, period, source, tablename, user=user,
                                   create_if_not_exists=False)

    query = parse_json_query(query)
    result = collection.find(query, sort=sort, limit=per_page, skip=(page-1)*per_page, projection=projection)
    if len(result) == 0:
        response = Response(status=204)
        response.headers['Content-Length'] = 0
        return response
    
    if output_format == 'bson':
        bson_data = bson.encode({'data': list(result)})
        compressed_data = lz4f.compress(bson_data)

        response = Response(compressed_data, mimetype='application/octet-stream')
        response.headers['Content-Encoding'] = 'lz4'
        response.headers['Content-Length'] = len(compressed_data)
        response.headers['Content-Type'] = 'application/octet-stream'
        return response

    elif output_format == 'csv':
        # Return CSV
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
        # Return JSON
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
    # 1. Parse query parameters
    """
    Handle a POST request to insert or upsert a collection of documents into a specified database collection.
    
    Parameters:
    - database (str): The name of the database.
    - period (str): The period or timeframe identifier.
    - source (str): The data source identifier.
    - tablename (str): The base name of the target table or collection.
    - request (flask.Request): The incoming HTTP request object containing query parameters, headers, and data.
    
    Behavior:
    1. Parses optional query parameters:
       - 'tablesubfolder' to append to the tablename.
       - 'user' with a default value of 'master'.
       - 'hasindex' indicating whether the collection has an index (default True).
    2. Acquires a collection object using the provided parameters.
    3. Validates that request data is present; returns HTTP 400 if missing.
    4. Handles input data which can be either:
       - lz4 compressed BSON binary data (with 'Content-Encoding' header set to 'lz4'), or
       - JSON formatted data.
    5. Validates that the decoded data is a list of documents; returns HTTP 400 if not.
    6. Inserts or upserts the documents into the collection depending on the 'hasindex' flag.
    7.
    """
    tablesubfolder = request.args.get('tablesubfolder')  # Optional
    user = request.args.get('user', 'master')            # Default to 'master'
    hasindex = request.args.get('hasindex', 'True')    
    hasindex = hasindex=='True'

    if tablesubfolder:
        tablename = f"{tablename}/{tablesubfolder}"

    # 2. Acquire collection object
    collection = shdata.collection(database, period, source, tablename, user=user,hasindex=hasindex)

    # 3. Ensure data is present
    if not request.data:
        Response({'message':'No data'}, status=400)
    
    # 4. Handle input data (lz4+BSON or JSON)
    # Check for binary, compressed upload
    if request.headers.get('Content-Encoding', '').lower() == 'lz4':
        decompressed = lz4f.decompress(request.data)
        documents = bson.decode(decompressed)['data']
    else:
        # fallback: assume JSON
        documents = json.loads(request.data)

    if not isinstance(documents, list):
        Response({'message':'Data must be a list'}, status=400)
    
    # 5. Insert/Upsert
    # (Assume upsert method supports list input)
    if hasindex:
        collection.upsert(documents)
    else:
        collection.extend(documents)

    # 6. Prepare and return response
    response_data = json.dumps({'status': 'success'}).encode('utf-8')
    response = Response(response_data, status=201, mimetype='application/json')
    response.headers['Content-Length'] = str(len(response_data))
    return response   

def patch_collection(database, period, source, tablename, request):
    # Get the collection    
    """
    Update a single document in a specified collection within the database based on filter and update criteria provided via HTTP request parameters.
    
    Parameters:
    - database (str): Name of the database to access.
    - period (str): Time period identifier used to locate the collection.
    - source (str): Source identifier used to locate the collection.
    - tablename (str): Name of the table/collection to update.
    - request (flask.Request): Flask request object containing query parameters.
    
    Returns:
    - flask.Response: JSON response containing the updated document with primary key information if successful,
      a 400 error response if required parameters are missing or invalid,
      or a 204 No Content response if no matching document is found.
    
    Behavior:
    - Validates the existence of the database and retrieves its primary key.
    - Extracts optional parameters 'user' and 'tablesubfolder' from the request.
    - Parses and validates the 'filter' and 'update' JSON parameters from the request.
    - Converts '_id' fields to ObjectId and attempts to parse 'date' fields to timestamps.
    - Optionally parses a 'sort' parameter to determine update order.
    - Performs a find_one_and_update operation on the collection.
    - Formats datetime fields and ObjectId in the response document for JSON serialization.
    """
    pkey = ''
    if database in DATABASE_PKEYS:
        pkey = DATABASE_PKEYS[database]
    else:
        error_data = json.dumps({'error': 'database not found'}).encode('utf-8')
        response = Response(error_data, status=400, mimetype='application/json')
        response.headers['Content-Length'] = len(error_data)
        return response
    
    user = request.args.get('user', 'master')  # Optional    
    tablesubfolder = request.args.get('tablesubfolder', None)  # Optional
    if tablesubfolder is not None:
        tablename = tablename+'/'+tablesubfolder
    collection = shdata.collection(database, period, source, tablename, user=user)
    
    filter = request.args.get('filter')
    if filter is None:
        error_data = json.dumps({'error': 'filter is required'}).encode('utf-8')
        response = Response(error_data, status=400, mimetype='application/json')
        response.headers['Content-Length'] = len(error_data)
        return response    
    filter = json.loads(filter)
    filter = parse_json_query(filter)
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
        filter=filter, 
        update=update, 
        sort=sort, 
        return_document=pymongo.ReturnDocument.AFTER)
    
    if res:
        if '_id' in res:
            res['_id'] = str(res['_id'])
        
        for key in res:
            if pd.api.types.is_datetime64_any_dtype(res[key]) or isinstance(res[key], datetime.datetime):
                res[key] = res[key].isoformat()
        # Return JSON
        response_data = {
            'pkey': pkey,
            'data': json.dumps(res),
        }
        response_json = json.dumps(response_data).encode('utf-8')
        response = Response(response_json, mimetype='application/json')
        response.headers['Content-Length'] = len(response_json)
        return response
    else:
        response = Response('', status=204)
        response.headers['Content-Length'] = 0
        return response

def delete_collection(database, period, source, tablename, request):
    # Get the collection    
    """
    Deletes a specific collection or documents within a collection from the database based on the given parameters and optional query.
    
    Parameters:
    - database (str): The name of the database.
    - period (str): The period identifier for the collection.
    - source (str): The source identifier for the collection.
    - tablename (str): The base name of the table/collection to delete.
    - request (flask.Request): The Flask request object containing optional query parameters.
    
    Optional query parameters in the request:
    - user (str): The user performing the deletion. Defaults to 'master' if not provided.
    - tablesubfolder (str): An optional subfolder appended to the tablename.
    - query (str): A JSON string representing a filter query to delete specific documents within the collection.
    
    Behavior:
    - If a 'query' parameter is provided, deletes documents matching the query within the specified collection.
    - If no 'query' is provided, deletes the entire collection.
    
    Returns:
    - flask.Response: HTTP 204 No Content if deletion is successful.
                      HTTP 404 Not Found if the collection or documents do not exist or deletion fails.
    """
    user = request.args.get('user', 'master')  # Optional
    tablesubfolder = request.args.get('tablesubfolder')  # Optional
    if tablesubfolder is not None:
        tablename = tablename + '/' + tablesubfolder

    query = request.args.get('query')
    if query:        
        query = json.loads(query) 
        query = parse_json_query(query)
        collection = shdata.collection(database, period, source, tablename, user=user, create_if_not_exists=False)
        result = collection.collection.delete_many(query)
        if result.deleted_count > 0:
            return Response(status=204)
        else:
            return Response(status=404)
    else:
        # original: drop the whole collection
        success = shdata.delete_collection(database, period, source, tablename, user=user)
        if success:
            return Response(status=204)
        else:
            return Response(status=404)
