
# Import all common variables, functions, and the Flask app
from SharedData.IO.ServerAPI_Common import *

@app.route('/api/subscribe/table/<database>/<period>/<source>/<tablename>', methods=['GET'])
def subscribe_table(database, period, source, tablename):
    """
    Handle GET requests to subscribe to data updates from a specified table.
    
    Streams compressed (lz4) binary data from a table identified by the given database, period, source, and tablename parameters.
    Supports optional query parameters for filtering and pagination:
    
    - tablesubfolder: str (optional) - Subfolder appended to the tablename.
    - lookbacklines: int (optional, default=1000) - Number of recent lines to retrieve.
    - lookbackdate: str (optional) - ISO format date string to filter rows from this date onwards.
    - mtime: str (optional) - ISO format timestamp to filter rows modified after this time.
    - count: int (optional) - Client's current row count to fetch new rows beyond this count.
    - page: int (optional, default=1) - Page number for paginated responses.
    
    Returns a Flask Response object containing the compressed data with headers indicating encoding, content length, and pagination.
    If no new data is available, returns HTTP 204 No Content.
    If authentication fails, returns HTTP 401 Unauthorized.
    On errors, returns HTTP 500 with a JSON error message.
    """
    try:        
        if not authenticate(request):
            return jsonify({'error': 'unauthorized'}), 401

        tablesubfolder = request.args.get('tablesubfolder')  # Optional
        if tablesubfolder is not None:
            table = shdata.table(database, period, source, tablename+'/'+tablesubfolder)
        else:
            table = shdata.table(database, period, source, tablename)

        if table.table.hasindex:
            lookbacklines = request.args.get('lookbacklines', default=1000, type=int)  # Optional
            lookbackid = table.count - lookbacklines
            if 'lookbackdate' in request.args:
                lookbackdate = pd.Timestamp(request.args.get('lookbackdate'))                
                loc = table.get_date_loc_gte(lookbackdate)
                if len(loc)>0:
                    lookbackid = min(loc)
            if lookbackid < 0:
                lookbackid = 0

            ids2send = np.arange(lookbackid, table.count)
            if 'mtime' in request.args:
                mtime = pd.Timestamp(request.args.get('mtime'))
                newids = lookbackid + np.where(table['mtime'][ids2send] >= mtime)[0]
                ids2send = np.intersect1d(ids2send, newids)
        else:
            clientcount = request.args.get('count', default=0, type=int)  # Optional
            if clientcount < table.count:
                ids2send = np.arange(clientcount, table.count-1)
            else:
                ids2send = np.array([])
        
        rows2send = len(ids2send)
        if rows2send == 0:
            response = Response(status=204)
            response.headers['Content-Length'] = 0
            return response
        
        # Compress & paginate the response                
        maxrows = np.floor(MAX_RESPONSE_SIZE_BYTES/table.itemsize)
        if rows2send > maxrows:
            # paginate
            page = request.args.get('page', default=1, type=int)
            ids2send = ids2send[int((page-1)*maxrows):int(page*maxrows)]

        compressed = lz4f.compress(table[ids2send].tobytes())
        responsebytes = len(compressed)
        response = Response(compressed, mimetype='application/octet-stream')
        response.headers['Content-Encoding'] = 'lz4'
        response.headers['Content-Length'] = responsebytes        
        response.headers['Content-Pages'] = int(np.ceil(rows2send/maxrows))
        return response
    
    except Exception as e:
        error_data = json.dumps({'error': str(e)}).encode('utf-8')
        response = Response(error_data, status=500, mimetype='application/json')
        response.headers['Content-Length'] = len(error_data)
        return response
    
@app.route('/api/publish/table/<database>/<period>/<source>/<tablename>', methods=['GET'])
def publish_table_get(database, period, source, tablename):
    """
    Handle GET requests to publish metadata about a specified table in the database.
    
    This endpoint returns JSON containing the count of records in the specified table and, if the table has an index, the latest modification time (mtime) within an optional lookback window.
    
    URL Parameters:
    - database (str): The database name.
    - period (str): The period identifier.
    - source (str): The data source name.
    - tablename (str): The table name, optionally combined with a subfolder.
    
    Query Parameters:
    - tablesubfolder (str, optional): Subfolder within the table path.
    - lookbacklines (int, optional): Number of recent lines to consider for mtime calculation (default is 1000).
    - lookbackdate (str, optional): ISO format date string to specify the earliest date for lookback filtering.
    
    Authentication:
    - Requires successful authentication via the `authenticate` function; returns 401 Unauthorized if authentication fails.
    
    Returns:
    - JSON response with:
      - 'count': Total number of records in the table.
      - 'mtime' (optional): ISO formatted timestamp of the latest modification time within the lookback window if the table has an index.
    
    Error Handling:
    - Returns a JSON error message with status code 500 if an exception occurs.
    """
    try:        
        if not authenticate(request):
            return jsonify({'error': 'unauthorized'}), 401
                
        tablesubfolder = request.args.get('tablesubfolder')  # Optional
        if tablesubfolder is not None:
            table = shdata.table(database, period, source, tablename+'/'+tablesubfolder)
        else:
            table = shdata.table(database, period, source, tablename)

        msg = {'count': int(table.count)}

        if table.table.hasindex:
            lookbacklines = request.args.get('lookbacklines', default=1000, type=int)  # Optional
            lookbackid = table.count - lookbacklines
            if 'lookbackdate' in request.args:
                lookbackdate = pd.Timestamp(request.args.get('lookbackdate'))                
                loc = table.get_date_loc_gte(lookbackdate)
                if len(loc)>0:
                    lookbackid = min(loc)
            if lookbackid < 0:
                lookbackid = 0

            ids2send = np.arange(lookbackid, table.count)
            if len(ids2send) == 0:
                msg['mtime'] = pd.Timestamp(np.datetime64('1970-01-01')).isoformat()    
            else:
                msg['mtime'] = pd.Timestamp(np.datetime64(np.max(table['mtime'][ids2send]))).isoformat()

        response_data = json.dumps(msg).encode('utf-8')
        response = Response(response_data, mimetype='application/json')
        response.headers['Content-Length'] = len(response_data)
        return response

    except Exception as e:
        error_data = json.dumps({'error': str(e)}).encode('utf-8')
        response = Response(error_data, status=500, mimetype='application/json')
        response.headers['Content-Length'] = len(error_data)
        return response

@app.route('/api/publish/table/<database>/<period>/<source>/<tablename>', methods=['POST'])
def publish_table_post(database, period, source, tablename):
    """
    Handle POST requests to publish compressed data to a specified table within a database.
    
    This endpoint accepts lz4f-compressed binary data in the request body, decompresses it, and writes the resulting records to the specified table. An optional subfolder within the table path can be specified via the 'tablesubfolder' query parameter.
    
    Parameters:
    - database (str): The name of the database.
    - period (str): The period identifier.
    - source (str): The data source identifier.
    - tablename (str): The name of the table to publish data to.
    
    Query Parameters:
    - tablesubfolder (str, optional): An optional subfolder within the table path.
    
    Behavior:
    - Authenticates the request; returns 401 Unauthorized if authentication fails.
    - Decompresses the request body using lz4f.
    - Converts decompressed data into records matching the table's dtype.
    - If the table has an index, performs an upsert of all records.
    - Otherwise, extends the table with the new records.
    - Returns HTTP 200 with empty body if data was processed successfully.
    - Returns HTTP 204 No Content if no complete records were found in the data.
    - Returns HTTP 500 with error details if an exception occurs.
    """
    try:        
        if not authenticate(request):
            return jsonify({'error': 'unauthorized'}), 401
                
        tablesubfolder = request.args.get('tablesubfolder')  # Optional
        if tablesubfolder is not None:
            table = shdata.table(database, period, source, tablename+'/'+tablesubfolder)
        else:
            table = shdata.table(database, period, source, tablename)
        
        data = lz4f.decompress(request.data)
        buffer = bytearray()
        buffer.extend(data)
        if len(buffer) >= table.itemsize:
            # Determine how many complete records are in the buffer
            num_records = len(buffer) // table.itemsize
            # Take the first num_records worth of bytes
            record_data = buffer[:num_records * table.itemsize]
            # And remove them from the buffer
            del buffer[:num_records * table.itemsize]
            # Convert the bytes to a NumPy array of records
            rec = np.frombuffer(record_data, dtype=table.dtype)
                
            if table.table.hasindex:
                # Upsert all records at once
                table.upsert(rec)
            else:
                # Extend all records at once
                table.extend(rec)
            
            response = Response(status=200)
            response.headers['Content-Length'] = 0
            return response        
        
        response = Response(status=204)
        response.headers['Content-Length'] = 0
        return response

    except Exception as e:
        error_data = json.dumps({'error': str(e)}).encode('utf-8')
        response = Response(error_data, status=500, mimetype='application/json')
        response.headers['Content-Length'] = len(error_data)
        return response

@app.route('/api/tables', methods=['GET'])
def list_tables() -> Response:
    """
    GET /api/tables
    
    Returns a JSON list of tables filtered by optional query parameters.
    
    Query Parameters:
    - keyword (str, optional): Filter tables by keyword in their names. Defaults to empty string (no filter).
    - user (str, optional): Username to filter tables by owner. Defaults to 'master'.
    
    Authentication:
    - Requires valid authentication; returns 401 Unauthorized if authentication fails.
    
    Responses:
    - 200 OK: JSON array of table information.
    - 204 No Content: No tables found matching the criteria.
    - 401 Unauthorized: Authentication failed.
    - 500 Internal Server Error: An error occurred during processing.
    
    Headers:
    - Content-Length: Length of the JSON response.
    - Error-Message (on 500): JSON encoded error message.
    """
    try:
        if not authenticate(request):
            return jsonify({'error': 'unauthorized'}), 401

        keyword = request.args.get('keyword', '')
        user = request.args.get('user', 'master')

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

@app.route('/api/table/<database>/<period>/<source>/<tablename>', methods=['HEAD', 'GET', 'POST', 'DELETE'])
@swag_from(docspath)
def table(database, period, source, tablename):
    """
    Handle CRUD operations on a specified table within a database for a given period and source.
    
    Supports HEAD, GET, POST, and DELETE HTTP methods:
    - HEAD: Retrieve metadata or headers related to the specified table.
    - GET: Retrieve data from the specified table.
    - POST: Insert or update data in the specified table.
    - DELETE: Remove data from the specified table.
    
    Authentication is required for all requests. Returns appropriate JSON responses and HTTP status codes:
    - 401 Unauthorized if authentication fails.
    - 405 Method Not Allowed for unsupported HTTP methods.
    - 500 Internal Server Error for unexpected exceptions.
    
    Parameters:
    - database (str): The name of the database.
    - period (str): The time period related to the data.
    - source (str): The data source identifier.
    - tablename (str): The name of the table to operate on.
    
    Returns:
    - JSON response with data or error message and corresponding HTTP status code, or a Response object with status 500 and error message header on exceptions.
    """
    try:
        if not authenticate(request):
            return jsonify({'error': 'unauthorized'}), 401

        if request.method == 'HEAD':
            return head_table(database, period, source, tablename, request)                
        elif request.method == 'GET':
            return get_table(database, period, source, tablename, request)        
        elif request.method == 'POST':
            return post_table(database, period, source, tablename, request)
        elif request.method == 'DELETE':
            return delete_table(database, period, source, tablename, request)
        else:
            return jsonify({'error': 'method not allowed'}), 405
        
    except Exception as e:
        time.sleep(1)  # Sleep for 1 second before returning the error                
        response = Response(status=500)                
        response.headers['Error-Message'] = str(e).replace('\n', ' ')
        return response

def head_table(database, period, source, tablename, request):
    """
    Generate an HTTP response containing header metadata from a specified table.
    
    Parameters:
        database (str): The name of the database.
        period (str): The time period identifier.
        source (str): The data source name.
        tablename (str): The name of the table to access.
        request (flask.Request): The Flask request object containing query parameters.
    
    Returns:
        flask.Response: An HTTP response with status code 200 and table header metadata
                        included as custom headers prefixed with 'Table-'.
    
    Description:
        Retrieves a table object from the 'shdata' module based on the provided parameters.
        If a 'tablesubfolder' query parameter is present in the request, it appends this
        subfolder to the table path. The 'user' query parameter defaults to 'master' if not
        provided. Extracts the header information from the table and adds each header field
        as a separate HTTP header in the response, prefixed with 'Table-'.
    """
    tablesubfolder = request.args.get('tablesubfolder')    
    user = request.args.get('user', default='master')
    
    if tablesubfolder is not None:
        tbl = shdata.table(database, period, source, tablename+'/'+tablesubfolder, user=user)
    else:
        tbl = shdata.table(database, period, source, tablename, user=user)
    hdr = tbl.table.hdr    
    hdrdict = {name: hdr[name].item() if hasattr(hdr[name], 'item') else hdr[name]
               for name in hdr.dtype.names}
    response = Response(200)    
    for key, value in hdrdict.items():
        response.headers['Table-'+key] = value    
    return response

def get_table(database, period, source, tablename, request):
    """
    Retrieve and filter data from a specified table in the database based on HTTP request parameters, then return the data in the requested format.
    
    Parameters:
        database (str): The name of the database.
        period (str): The period identifier for the data.
        source (str): The data source identifier.
        tablename (str): The name of the table to query.
        request (flask.Request): The HTTP request object containing query parameters and headers.
    
    Query Parameters (all optional):
        tablesubfolder (str): Subfolder within the table to query.
        startdate (str): Start date filter in a format parseable by pandas.Timestamp.
        enddate (str): End date filter in a format parseable by pandas.Timestamp.
        symbols (str): Comma-separated list of symbols to filter.
        portfolios (str): Comma-separated list of portfolios to filter.
        tags (str): Comma-separated list of tags to filter.
        page (int): Page number for pagination (default is 1).
        per_page (int): Number of records per page (default is 0, meaning no limit).
        format (str): Output format, one of 'json' (default), 'csv', or 'bin'.
        query (str):
    """
    tablesubfolder = request.args.get('tablesubfolder')  # Optional
    startdate = request.args.get('startdate')  # Optional
    enddate = request.args.get('enddate')  # Optional
    symbols = request.args.get('symbols')  # Optional
    portfolios = request.args.get('portfolios')  # Optional
    tags = request.args.get('tags')  # Optional
    page = request.args.get('page', default='1')
    page = int(float(page))
    per_page = request.args.get('per_page', default='0')
    per_page = int(float(per_page))
    output_format = request.args.get('format', 'json').lower()  # 'json' by default, can be 'csv' and 'bin'        
    query = request.args.get('query')
    user = request.args.get('user', default='master')

    if query:
        query = json.loads(query)  # Optional
    else:
        query = {}

    if tablesubfolder is not None:
        tbl = shdata.table(database, period, source, tablename+'/'+tablesubfolder, user=user)
    else:
        tbl = shdata.table(database, period, source, tablename, user=user)
    
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
        response = Response(status=204)
        response.headers['Content-Length'] = 0
        return response
    
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
    
    if not loc is None:
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
        response = Response(status=204)
        response.headers['Content-Length'] = 0
        return response
    
    
    # filter columns
    pkey = DATABASE_PKEYS[database]
    columns = request.args.get('columns')  # Optional
    if columns:
        if not tbl.is_schemaless:
            columns = columns.split(',')
            columns = np.array([c for c in columns if not c in pkey])
            columns = pkey + list(np.unique(columns))
            names = columns
            formats = [tbl.dtype.fields[name][0].str for name in names]
            dtype = np.dtype(list(zip(names, formats)))
            # Apply pagination    
            maxrows = int(np.floor(MAX_RESPONSE_SIZE_BYTES/dtype.itemsize))
            maxrows = min(maxrows,len(loc))
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
        maxrows = int(np.floor(MAX_RESPONSE_SIZE_BYTES/tbl.itemsize))
        maxrows = min(maxrows,len(loc))
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
    """
    Handles a POST request to create or update a table in the specified database.
    
    Parameters:
    - database (str): The name of the database.
    - period (str): The period identifier for the table.
    - source (str): The data source identifier.
    - tablename (str): The name of the table to create or update.
    - request (flask.Request): The HTTP request object containing data and query parameters.
    
    Query Parameters (all optional):
    - tablesubfolder (str): Subfolder to append to the table name.
    - overwrite (bool): Whether to overwrite existing data (default False).
    - user (str): User performing the operation (default 'master').
    - hasindex (bool): Whether the data has an index (default True).
    
    Request Data:
    - Must have Content-Encoding header set to 'lz4'.
    - The request body should contain lz4-compressed BSON data with optional keys:
      - 'names' (list): Field names.
      - 'formats' (list): Field formats.
      - 'size' (int): Size parameter for the table.
      - 'data' (bytes): Binary data representing the table contents.
      - 'meta_names' (list): Names of fields in the binary data.
      - 'meta_formats'
    """
    tablesubfolder = request.args.get('tablesubfolder')  # Optional
    overwrite = request.args.get('overwrite', 'False')  # Optional
    overwrite = overwrite=='True'
    user = request.args.get('user', 'master')  # Optional
    hasindex = request.args.get('hasindex', 'True')    
    hasindex = hasindex=='True'
    is_schemaless = request.args.get('is_schemaless', 'False')    
    is_schemaless = is_schemaless=='True'

    value = None
    if not request.data:
        raise Exception('No data provided')
    
    content_encoding = request.headers.get('Content-Encoding', "")
    if content_encoding != 'lz4':
        raise Exception('Content-Encoding must be lz4')
    
    data = lz4f.decompress(request.data)
    json_payload = bson.decode(data)
    names = None
    if 'names' in json_payload:
        names = json_payload['names']
    formats = None
    if 'formats' in json_payload:
        formats = json_payload['formats']
    size = None
    if 'size' in json_payload:
        size = json_payload['size']
        
    value = None
    if 'data' in json_payload:
        meta_names = json_payload['meta_names']
        meta_formats = json_payload['meta_formats']
        dtype = np.dtype(list(zip(meta_names, meta_formats)))
        value = np.frombuffer(json_payload['data'], dtype=dtype).copy()

    elif 'dict_list' in json_payload:
        value = json_payload['dict_list']
                
    if tablesubfolder is not None:
        tablename = tablename+'/'+tablesubfolder
            
    if names is None or formats is None:
        tbl = shdata.table(database, period, source, tablename,
                        names=names, formats=formats, size=size,
                        overwrite=overwrite, user=user, value=value, 
                        hasindex=hasindex, is_schemaless=is_schemaless)
    else:
        tbl = shdata.table(database, period, source, tablename,
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
            tbl = shdata.table(database, period, source, tablename,
                names=names, formats=formats, size=size,
                overwrite=overwrite, user=user, 
                hasindex=hasindex, is_schemaless=is_schemaless)
            
    response = Response(status=201)
    response.headers['Content-Length'] = 0
    return response

def delete_table(database, period, source, tablename, request):
    """
    Deletes a specified table from the given database, period, and source.
    
    Parameters:
        database (str): The name of the database.
        period (str): The time period associated with the table.
        source (str): The source identifier of the table.
        tablename (str): The name of the table to delete.
        request (flask.Request): The HTTP request object containing optional query parameters.
    
    Optional Query Parameters in request.args:
        tablesubfolder (str): An optional subfolder appended to the tablename.
        user (str): The user performing the deletion; defaults to 'master' if not provided.
    
    Returns:
        flask.Response: HTTP 204 No Content if deletion is successful,
                        HTTP 404 Not Found if the table does not exist or deletion fails.
    """
    tablesubfolder = request.args.get('tablesubfolder')  # Optional    
    user = request.args.get('user', 'master')  # Optional
    if tablesubfolder is not None:
        tablename = tablename+'/'+tablesubfolder
    success = shdata.delete_table(database, period, source, tablename, user=user)
    if success:
        return Response(status=204)
    else:
        return Response(status=404)
