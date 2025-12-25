# Import all common variables, functions, and the Flask app
from SharedData.IO.ServerAPI_Common import *

@app.route('/api/timeseries', methods=['GET'])
def list_timeseries():
    """
    GET /api/timeseries
    
    Returns a JSON list of timeseries metadata filtered by optional query parameters.
    
    Query Parameters:
    - keyword (str, optional): Filter timeseries names containing this keyword. Defaults to empty string (no filter).
    - user (str, optional): Username to filter timeseries by owner. Defaults to 'master'.
    
    Responses:
    - 200 OK: JSON array of timeseries objects with their metadata.
    - 204 No Content: No timeseries found matching the criteria.
    - 401 Unauthorized: Authentication failed.
    - 500 Internal Server Error: An unexpected error occurred.
    
    Each timeseries object contains fields from the underlying DataFrame, with datetime fields ISO formatted and NaN values replaced by null.
    """
    try:
        if not authenticate(request):
            return jsonify({'error': 'unauthorized'}), 401
        keyword = request.args.get('keyword', '')
        user = request.args.get('user', 'master')
        
        # Get timeseries list from SharedData
        timeseries_df = shdata.list_timeseries(keyword=keyword, user=user)
        
        if len(timeseries_df) == 0:
            return Response(status=204)
        
        # Convert DataFrame to list of dictionaries for JSON serialization
        timeseries_list = timeseries_df.reset_index().to_dict('records')
        
        # Clean up datetime serialization for JSON
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

@app.route('/api/timeseries/<database>/<period>/<source>', methods=['HEAD'])
def head_timeseries_source(database, period, source):
    """
    Check if a timeseries container exists and return metadata about its tags.
    HEAD requests should return metadata in headers, not in the response body.
    """
    try:
        if not authenticate(request):
            return Response(status=401)
        
        user = request.args.get('user', 'master')        
                            
        # Load timeseries 
        ts = shdata.timeseries(database, period, source, user=user)
        ts.load()
        tags = list(ts.tags.keys())
        
        # Return metadata in headers (HEAD requests have no body)
        response = Response(status=200)
        response.headers['Timeseries-Tags'] = ','.join(tags)
        response.headers['Timeseries-Database'] = database
        response.headers['Timeseries-Period'] = period
        response.headers['Timeseries-Source'] = source
        return response
        
    except Exception as e:
        return Response(status=404)
    
@app.route('/api/timeseries/<database>/<period>/<source>', methods=['POST'])
def create_timeseries_source(database, period, source):
    """
    Create a timeseries container for a specified database, period, and source.
    
    This POST endpoint initializes a new timeseries container similar to invoking shdata.timeseries() directly.
    It supports optional query parameters for user identification and start date filtering.
    
    Parameters:
    - database (str): Name of the database.
    - period (str): Time period identifier (e.g., D1, M15, M1).
    - source (str): Source identifier.
    
    Query Parameters:
    - user (str, optional): User identifier; defaults to 'master' if not provided.
    - startdate (str, optional): ISO formatted start date to filter the timeseries.
    - columns (str, optional): Comma-separated list of column names (currently unused in the function).
    
    Returns:
    - 201 Created with JSON containing status and details on success.
    - 401 Unauthorized if authentication fails.
    - 500 Internal Server Error with error details if an exception occurs.
    """
    try:
        if not authenticate(request):
            return jsonify({'error': 'unauthorized'}), 401
        
        user = request.args.get('user', 'master')
        startdate = request.args.get('startdate')        
        
        # Parse optional parameters
        startdate_obj = None
        if startdate:
            startdate_obj = pd.Timestamp(startdate)
                    
        # Create timeseries container using shdata interface
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
        error_data = json.dumps({'error': str(e)}).encode('utf-8')
        response = Response(error_data, status=500, mimetype='application/json')
        response.headers['Content-Length'] = len(error_data)
        return response

@app.route('/api/timeseries/<database>/<period>/<source>/write', methods=['PATCH'])
def write_timeseries_source(database: str, period: str, source: str):
    """
    Triggers a write operation to persist all timeseries data for a specified source container.
    
    This PATCH endpoint invokes the write() method on the timeseries container identified by the given
    database, period, and source parameters, optionally filtered by a start date. It flushes all relevant
    data to persistent storage.
    
    Parameters:
        database (str): The name of the database containing the timeseries.
        period (str): The time period associated with the timeseries data.
        source (str): The identifier for the source container of the timeseries.
    
    Optional Query Parameters:
        user (str): The user initiating the write operation; defaults to 'master' if not specified.
        startdate (str): An optional ISO-formatted start date to limit the write operation.
    
    Returns:
        flask.Response: A JSON response with HTTP status codes:
            - 200 OK: Write operation succeeded, includes operation details.
            - 401 Unauthorized: Authentication failed.
            - 404 Not Found: Timeseries source does not exist.
            - 500 Internal Server Error: Write operation failed due to an exception.
    """
    try:
        if not authenticate(request):
            return jsonify({'error': 'unauthorized'}), 401
            
        user = request.args.get('user', 'master')
        startdate = request.args.get('startdate')

        
        # Parse optional startdate parameter
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
        error_data = json.dumps({'error': str(e)}).encode('utf-8')
        response = Response(error_data, status=500, mimetype='application/json')
        response.headers['Content-Length'] = len(error_data)
        return response

@app.route('/api/timeseries/<database>/<period>/<source>', methods=['DELETE'])
def delete_timeseries_source(database, period, source):
    """
    Delete all timeseries data for a specified database, period, and source.
    
    This endpoint requires authentication and attempts to delete timeseries entries
    using the provided database name, period identifier, and source identifier.
    
    Parameters:
    - database (str): The name of the database from which to delete timeseries data.
    - period (str): The period identifier (e.g., D1, M15, M1) specifying the timeseries granularity.
    - source (str): The source identifier for the timeseries data to be deleted.
    
    Returns:
    - 204 No Content if the deletion is successful.
    - 404 Not Found if no matching timeseries data is found.
    - 401 Unauthorized if authentication fails.
    - 500 Internal Server Error with an error message header if an exception occurs during processing.
    """
    try:
        if not authenticate(request):
            return jsonify({'error': 'unauthorized'}), 401
        
        user = request.args.get('user', 'master')
        
        # Use shdata.delete_timeseries for deletion at source level
        success = shdata.delete_timeseries(database, period, source, user=user)
        
        if success:
            return Response(status=204)
        else:
            return Response(status=404)
            
    except Exception as e:
        time.sleep(1)  # Sleep for 1 second before returning the error        
        response = Response(status=500)                
        response.headers['Error-Message'] = str(e).replace('\n', ' ')
        return response

@app.route('/api/timeseries/<database>/<period>/<source>/<tag>', methods=['HEAD','GET', 'POST', 'DELETE', 'PATCH'])
@swag_from(docspath)
def timeseries(database, period, source, tag):
    """
    Handle CRUD operations on a specified timeseries within a database.
    
    This endpoint supports GET, POST, DELETE, HEAD, and PATCH HTTP methods to interact with a timeseries identified by the given database, period, source, and tag parameters.
    
    Authentication is required for all requests. If authentication fails, a 401 Unauthorized response is returned.
    
    Parameters:
    - database (str): The name of the database.
    - period (str): The period identifier (D1, M15, M1, etc.).
    - source (str): The source identifier.
    - tag (str): The name of the timeseries tag.
    
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
        time.sleep(1)  # Sleep for 1 second before returning the error        
        response = Response(status=500)                
        response.headers['Error-Message'] = str(e).replace('\n', ' ')
        return response

def head_timeseries(database: str, period: str, source: str, tag: str, request):
    """
    Handle HTTP HEAD requests to provide metadata about a specified timeseries.
    
    This function retrieves timeseries data based on the given database, period, source, and tag parameters,
    optionally appending a subfolder tag if provided in the request arguments. It returns an HTTP response
    with headers containing metadata such as column names, start and end timestamps, number of records,
    and the period of the timeseries. If the timeseries data is not found or an error occurs, it returns
    a 404 status response.
    
    Parameters:
    - database (str): The name of the database containing the timeseries.
    - period (str): The period/frequency of the timeseries data.
    - source (str): The source identifier of the timeseries.
    - tag (str): The tag identifying the specific timeseries.
    - request: The HTTP request object containing query parameters.
    
    Returns:
    - Response: An HTTP response with metadata headers for the timeseries or a 404 status if not found.
    """
    tagsubfolder = request.args.get('tagsubfolder')  # Optional
    user = request.args.get('user', 'master')
    
    if tagsubfolder is not None:
        tag = tag + '/' + tagsubfolder
    
    try:
        # Get timeseries data to extract metadata
        ts_data = shdata.timeseries(database, period, source, tag, user=user)
        
        if ts_data is None or len(ts_data) == 0:
            return Response(status=404)
        
        response = Response(status=200)
        response.headers["Timeseries-Columns"] = ",".join(ts_data.columns.tolist())
        response.headers["Timeseries-Start"] = ts_data.index.min().isoformat()
        response.headers["Timeseries-End"] = ts_data.index.max().isoformat()
        response.headers["Timeseries-Count"] = str(len(ts_data))
        response.headers["Timeseries-Period"] = period
        return response
        
    except Exception as e:
        return Response(status=404)

def get_timeseries(database: str, period: str, source: str, tag: str, request):
    """
    Retrieve a timeseries dataset from a specified database and return it in the requested format with optional filtering and compression.
    
    Parameters:
    - database (str): Name of the database to query.
    - period (str): Time period or partition within the database.
    - source (str): Identifier for the data source.
    - tag (str): Timeseries tag name to query.
    - request (flask.Request): Flask request object containing query parameters and headers.
    
    Query Parameters (via request.args):
    - tagsubfolder (str, optional): Subfolder appended to the tag for more specific querying.
    - user (str, optional): User identifier for access control; defaults to 'master'.
    - startdate (str, optional): ISO format start date to filter timeseries data.
    - enddate (str, optional): ISO format end date to filter timeseries data.
    - columns (str, optional): Comma-separated list of columns to include in the output.
    - format (str, optional): Output format; one of 'json' (default), 'csv', or 'bin'.
    - dropna (str, optional): Whether to drop rows with all NaN values; defaults to 'True'.
    
    Returns:
    - flask.Response: HTTP response containing the timeseries data in the requested format:
    """
    tagsubfolder = request.args.get('tagsubfolder')  # Optional
    user = request.args.get('user', 'master')
    startdate = request.args.get('startdate')
    enddate = request.args.get('enddate')
    columns = request.args.get('columns')
    output_format = request.args.get('format', 'bin').lower()
    dropna = request.args.get('dropna', 'True').lower() == 'true'
    accept_encoding = request.headers.get('Accept-Encoding', '')
    
    if tagsubfolder is not None:
        tag = tag + '/' + tagsubfolder
    
    try:
        # Load timeseries (creates container and path automatically)
        ts_data = shdata.timeseries(database,period,source,tag,user=user)
        
        # Check for new columns that may have been added by other processes
        path = f'{user}/{database}/{period}/{source}/timeseries'
        ts_disk = shdata.data[path].tags[tag]
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
            # Filter to only existing columns
            columns_list = [s for s in columns_list if s in ts_data.columns]
            if columns_list:
                ts_data = ts_data[columns_list].copy()
        
        # Drop rows that are all NaN (optional)
        if dropna:
            ts_data = ts_data.dropna(how='all')
        
        if len(ts_data) == 0:
            return Response(status=204)
        
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
            # Return binary format similar to tables
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
            # Reset index to include datetime in JSON
            ts_json = ts_data.reset_index()
            ts_json['date'] = ts_json['date'].dt.isoformat()
            
            response_data = {
                'tag': tag,
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
        error_data = json.dumps({'error': str(e)}).encode('utf-8')
        response = Response(error_data, status=500, mimetype='application/json')
        response.headers['Content-Length'] = len(error_data)
        return response

def post_timeseries(database: str, period: str, source: str, tag: str, request):
    """
    Handle a POST request to insert or update timeseries data in the specified database.
    
    Parameters:
    - database (str): Name of the target database.
    - period (str): Period identifier for the timeseries.
    - source (str): Source identifier of the data.
    - tag (str): Timeseries tag name.
    - request (flask.Request): Incoming HTTP request containing query parameters, headers, and data payload.
    
    Functionality:
    - Supports optional query parameters:
      - 'tagsubfolder': Appends a subfolder to the tag name.
      - 'user': Specifies the user performing the operation (default 'master').
      - 'columns': Defines columns for an empty timeseries creation.
      - 'overwrite': Boolean flag to overwrite existing data (default False).
    - Accepts input data in two formats:
      - lz4 compressed BSON binary data (with 'Content-Encoding' header set to 'lz4').
      - JSON formatted data representing DataFrame records.
    - Parses and converts input data into a pandas DataFrame with a datetime index.
    - Creates or updates the timeseries container using the shdata interface.
    - Returns HTTP responses with appropriate status codes and messages:
      - 201 Created on success.
      - 400 Bad Request for missing or invalid data.
    """
    tagsubfolder = request.args.get('tagsubfolder')  # Optional
    user = request.args.get('user', 'master')
    columns = request.args.get('columns')
    overwrite = request.args.get('overwrite', 'False') == 'True'
    
    if tagsubfolder is not None:
        tag = tag + '/' + tagsubfolder
    
    try:
        # Handle case where only columns are provided (create empty timeseries)
        if not request.data and columns:
            # Create empty timeseries with specified columns
            columns_list = columns.split(',')
            columns = pd.Index(columns_list)
            
            # Create or update the timeseries using shdata interface
            shdata.timeseries(database, period, source, tag,
                             user=user, columns=columns, overwrite=overwrite)

            response_data = json.dumps({'status': 'success', 'tag': tag, 'message': 'Empty timeseries created with columns'}).encode('utf-8')
            response = Response(response_data, status=201, mimetype='application/json')
            response.headers['Content-Length'] = str(len(response_data))
            return response
        
        # Ensure data is present if no columns specified
        if not request.data:
            return jsonify({'message': 'No data provided'}), 400
        
        # Handle input data (lz4+BSON or JSON)
        content_encoding = request.headers.get('Content-Encoding', '').lower()
        
        if content_encoding == 'lz4':
            # Decompress and decode BSON data
            decompressed = lz4f.decompress(request.data)
            data_payload = bson.decode(decompressed)
            
            if 'data' in data_payload and 'index' in data_payload and 'columns' in data_payload:
                # Binary format with separate index, columns, and data
                index_data = np.frombuffer(data_payload['index'], dtype=np.int64)
                index = pd.to_datetime(index_data)
                columns_list = data_payload['columns']
                shape = data_payload['shape']
                values = np.frombuffer(data_payload['data'], dtype=np.float64).reshape(shape)
                df = pd.DataFrame(values, index=index, columns=columns_list)
            else:
                # Standard BSON with DataFrame-like structure
                df = pd.DataFrame(data_payload)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date')
        else:
            # JSON format
            data = json.loads(request.data.decode('utf-8'))
            df = pd.DataFrame(data)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
        
        # Validate that we have a proper DataFrame with datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            return jsonify({'message': 'Data must have a datetime index'}), 400
        
        # Use shdata.timeseries to create or update the timeseries
        # For new timeseries, pass the data via the value parameter
        columns_list = df.columns.tolist() if columns is None else columns.split(',')
        columns = pd.Index(columns_list)
        
        # Create or update the timeseries using shdata interface
        ts = shdata.timeseries(database, period, source, tag,
                         user=user, columns=columns, value=df, overwrite=overwrite)

        # Check for new columns that don't exist in the timeseries
        new_columns = [col for col in df.columns if col not in ts.columns]
        appended_columns = []
        
        if new_columns:
            # Get the TimeSeriesDisk object to append columns
            path = f'{user}/{database}/{period}/{source}/timeseries'
            if path in shdata.data:
                ts_container = shdata.data[path]
                if tag in ts_container.tags:
                    ts_disk = ts_container.tags[tag]
                    # Append the new columns
                    ts_disk.append_columns(new_columns)
                    appended_columns = new_columns
                    # Reload the ts DataFrame to include new columns
                    ts = ts_disk.data
        
        # Now write data to all columns (including newly appended ones)
        icols = df.columns.intersection(ts.columns)
        iindex = df.index.intersection(ts.index)
        ts.loc[iindex, icols] = df.loc[iindex, icols].values

        response_message = 'Timeseries updated'
        if appended_columns:
            response_message += f' (appended columns: {", ".join(appended_columns)})'
        
        response_data = json.dumps({'status': 'success', 'tag': tag, 'message': response_message, 'appended_columns': appended_columns}).encode('utf-8')
        response = Response(response_data, status=201, mimetype='application/json')
        response.headers['Content-Length'] = str(len(response_data))
        return response
        
    except Exception as e:
        error_data = json.dumps({'error': str(e)}).encode('utf-8')
        response = Response(error_data, status=500, mimetype='application/json')
        response.headers['Content-Length'] = len(error_data)
        return response

def delete_timeseries(database: str, period: str, source: str, tag: str, request):
    """
    Deletes a specified timeseries or a portion of it from the given database, period, and source.
    
    Parameters:
        database (str): The name of the database.
        period (str): The time period associated with the timeseries.
        source (str): The source identifier of the timeseries.
        tag (str): The name of the timeseries tag to delete.
        request (flask.Request): The HTTP request object containing optional query parameters.
    
    Optional Query Parameters in request.args:
        tagsubfolder (str): Optional subfolder appended to the tag name.
        user (str): The user performing the deletion; defaults to 'master' if not provided.
        startdate (str): Start date for partial deletion (delete data from this date onwards).
        enddate (str): End date for partial deletion (delete data up to this date).
    
    Returns:
        flask.Response: HTTP 204 No Content if deletion is successful,
                        HTTP 404 Not Found if the timeseries does not exist or an error occurs.
    """
    tagsubfolder = request.args.get('tagsubfolder')  # Optional
    user = request.args.get('user', 'master')
    startdate = request.args.get('startdate')
    enddate = request.args.get('enddate')
    
    if tagsubfolder is not None:
        tag = tag + '/' + tagsubfolder
    
    try:
        # Use shdata.delete_timeseries for deletion
        if startdate is not None or enddate is not None:
            # For partial deletion, we need to get the data first, modify it, then update
            ts_data = shdata.timeseries(database, period, source, tag, user=user)
            
            if ts_data is None or len(ts_data) == 0:
                return Response(status=404)
            
            # Create a mask for rows to delete
            mask = pd.Series(True, index=ts_data.index)
            
            if startdate is not None:
                startdate = pd.Timestamp(startdate)
                mask = mask & (ts_data.index >= startdate)
                
            if enddate is not None:
                enddate = pd.Timestamp(enddate)
                mask = mask & (ts_data.index <= enddate)
            
            # Set selected rows to NaN (effectively deleting them)
            ts_data.loc[mask, :] = np.nan
            
            # Update the timeseries with modified data
            shdata.timeseries(database, period, source, tag, 
                             user=user, value=ts_data, overwrite=True)
            
            return Response(status=204)
        else:
            # Delete entire timeseries using SharedData delete method
            shdata.delete_timeseries(database, period, source, tag, user=user)
            return Response(status=204)
            
    except Exception as e:
        return Response(status=404)

def write_timeseries(database: str, period: str, source: str, tag: str, request):
    """
    Triggers a write operation for a specified timeseries, persisting data to disk or S3.
    
    This function invokes the write() method of the underlying timeseries container to
    flush data to persistent storage immediately. It allows forcing the persistence
    of timeseries data instead of waiting for automatic write intervals.
    
    Parameters:
        database (str): The name of the database.
        period (str): The time period associated with the timeseries.
        source (str): The source identifier of the timeseries.
        tag (str): The name of the timeseries tag to write.
        request (flask.Request): The HTTP request object containing optional query parameters.
    
    Optional Query Parameters in request.args:
        tagsubfolder (str): Optional subfolder appended to the tag name.
        user (str): The user performing the write operation; defaults to 'master' if not provided.
        startdate (str): Optional start date for the write operation in ISO format.
    
    Returns:
        flask.Response:
            - HTTP 200 OK with JSON details if the write is successful.
            - HTTP 404 Not Found if the specified timeseries container does not exist.
            - HTTP 500 Internal Server Error with error details if the write operation fails.
    """
    tagsubfolder = request.args.get('tagsubfolder')  # Optional
    user = request.args.get('user', 'master')
    startdate = request.args.get('startdate')
    
    if tagsubfolder is not None:
        tag = tag + '/' + tagsubfolder
    
    try:
        # Construct the path for the timeseries container
        path = f'{user}/{database}/{period}/{source}/timeseries'
        
        # Get the timeseries container from shdata
        if path not in shdata.data:
            return Response(status=404)
        
        ts_container = shdata.data[path]
        
        if ts_container is None:
            return Response(status=404)
        
        # Parse optional startdate parameter
        startdate_obj = None
        if startdate is not None:
            startdate_obj = pd.Timestamp(startdate)
        
        # Call the write method on the container
        ts_container.write(startDate=startdate_obj)
        
        response_data = json.dumps({
            'status': 'success',
            'message': 'Timeseries write operation completed',
            'database': database,
            'period': period,
            'source': source,
            'tag': tag,
            'user': user,
            'startdate': startdate
        }).encode('utf-8')
        
        response = Response(response_data, status=200, mimetype='application/json')
        response.headers['Content-Length'] = str(len(response_data))
        return response
        
    except Exception as e:
        error_data = json.dumps({'error': str(e)}).encode('utf-8')
        response = Response(error_data, status=500, mimetype='application/json')
        response.headers['Content-Length'] = len(error_data)
        return response
