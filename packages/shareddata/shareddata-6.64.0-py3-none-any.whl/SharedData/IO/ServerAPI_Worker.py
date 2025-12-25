
# Import all common variables, functions, and the Flask app
from SharedData.IO.ServerAPI_Common import *
from SharedData.Utils import get_hash

@app.route('/api/workerpool', methods=['GET','POST'])
def workerpool():
    """
    Handle HTTP requests for the '/api/workerpool' endpoint supporting GET and POST methods.
    
    - POST: Processes the request by calling post_workerpool(request) to create or update workerpool data.
    - GET: Processes the request by calling get_workerpool(request) to retrieve workerpool data.
    
    If an exception occurs during processing, the function waits for 1 second before returning a 500 Internal Server Error response with the error message included in the response headers.
    """
    try:        
        if request.method == 'POST':
            return post_workerpool(request)
        elif request.method == 'GET':
            return get_workerpool(request)

    except Exception as e:
        time.sleep(1)  # Sleep for 1 second before returning the error        
        response = Response(status=500)                
        response.headers['Error-Message'] = str(e).replace('\n', ' ')
        return response

def post_workerpool(request):
    """
    Handles POST requests to create a new job in the worker pool.
    
    This function authenticates the incoming request, decompresses and decodes the BSON-encoded data,
    validates required fields ('sender', 'target', 'job'), and processes the job record by setting its status,
    timestamp, and hash if not present. It then inserts or updates the job record in the worker pool database collection.
    
    Args:
        request (flask.Request): The incoming HTTP request containing compressed BSON data.
    
    Returns:
        flask.Response: A response object indicating the result of the operation.
            - 201 Created if the job is successfully added.
            - 401 Unauthorized if authentication fails.
    
    Raises:
        Exception: If any of the required fields ('sender', 'target', 'job') are missing in the decoded record.
    """
    if not authenticate(request):
        return jsonify({'error': 'unauthorized'}), 401
    
    bson_data = lz4f.decompress(request.data)
    records = bson.decode(bson_data)
    if 'commands' in records:        
        commands = records['commands']
    else:
        commands = [records]

    if len(commands)>0:
        WorkerPool.post_commands(shdata, commands) 

    if 'batch_jobs' in records:
        batch_jobs = records['batch_jobs']
        if len(batch_jobs)>0:
            WorkerPool.post_batch_jobs(shdata, batch_jobs)
            
    return Response(status=201)
 
def get_workerpool(request):
    """
    Handles a request to retrieve jobs from the worker pool for a specified worker.
    
    Parameters:
        request (flask.Request): The incoming HTTP request object.
    
    Process:
        - Authenticates the request; returns 401 Unauthorized if authentication fails.
        - Extracts the 'workername' parameter from the query string; returns 400 Bad Request if missing.
        - Retrieves existing jobs for the worker from the worker pool.
        - Optionally fetches additional jobs if 'fetch_jobs' parameter is provided, extending the job list.
        - If no jobs are found, returns a 204 No Content response.
        - Otherwise, encodes the jobs in BSON format, compresses the data using LZ4, and returns it with appropriate headers.
    
    Returns:
        flask.Response: HTTP response containing compressed job data or an error/status code.
    """
    if not authenticate(request):
        return jsonify({'error': 'unauthorized'}), 401
    workername = request.args.get('workername')
    if workername is None:
        return jsonify({'error': 'workername is required'}), 400
    jobs = WorkerPool.get_commands(shdata, workername)

    fetch_jobs = request.args.get('fetch_jobs')
    if fetch_jobs is not None:
        batch_jobs = WorkerPool.fetch_batch_jobs(shdata, workername, int(fetch_jobs))
        jobs.extend(batch_jobs)

    if len(jobs)==0:
        return Response(status=204)
    else:
        bson_data = bson.encode({'jobs':jobs})
        compressed = lz4f.compress(bson_data)
        return Response(
            compressed, 
            mimetype='application/octet-stream', 
            headers={'Content-Encoding': 'lz4'}
        )        

@app.route('/api/installworker')
def installworker():
    """
    Generate and return a shell script to install and configure the SharedData worker service on the client machine.
    
    This endpoint requires authentication via the `authenticate` function. It accepts the following query parameters:
    - `token` (str): Authentication token to be embedded in the environment file.
    - `batchjobs` (int, optional): Number of batch jobs to run; defaults to 0 if not provided.
    
    The generated script performs the following actions:
    - Creates an environment file with SharedData and Git configuration variables.
    - Installs necessary system dependencies including OpenJDK 21, Git, Python 3, and related development packages.
    - Configures Git with user credentials and disables pull rebase.
    - Sets up a Python virtual environment and installs the SharedData Python package.
    - Creates and enables a systemd service to run the SharedData worker with the specified batch jobs.
    - Starts the service and tails its logs.
    
    Returns:
        Response: A Flask Response object containing the shell script with MIME type 'text/x-sh' on success,
                  or a JSON error message with status 401 if unauthorized,
                  or status 500 if an exception occurs.
    """
    try:        
        if not authenticate(request):
            return jsonify({'error': 'unauthorized'}), 401        
        token = request.args.get('token')
        batchjobs = int(request.args.get('batchjobs', '0'))
        endpoint = str('https://'+request.host).rstrip('/')
        

        script = f"""\
#!/bin/bash
USERNAME=$(whoami)

cd /home/$USERNAME

# CREATE ENVIRONMENT FILE
cat > /home/$USERNAME/shareddata-worker.env <<EOF
SHAREDDATA_TOKEN={token}
SHAREDDATA_ENDPOINT={endpoint}
GIT_USER={os.environ['GIT_USER']}
GIT_EMAIL={os.environ['GIT_EMAIL']}
GIT_TOKEN={os.environ['GIT_TOKEN']}
GIT_ACRONYM={os.environ['GIT_ACRONYM']}
GIT_SERVER={os.environ['GIT_SERVER']}
GIT_PROTOCOL={os.environ['GIT_PROTOCOL']}
EOF

export GIT_USER="{os.environ['GIT_USER']}"
export GIT_EMAIL="{os.environ['GIT_EMAIL']}"
export GIT_TOKEN="{os.environ['GIT_TOKEN']}"

# INSTALL DEPENDENCIES
sudo apt update -y
sudo apt install openjdk-21-jre-headless -y

# INSTALL GIT
sudo apt install git -y
git config --global user.name "$GIT_USER"
git config --global user.email "$GIT_EMAIL"
git config --global credential.helper "!f() {{ echo username=\\$GIT_USER; echo password=\\$GIT_TOKEN; }};f"
git config --global pull.rebase false

# INSTALL PYTHON DEPENDENCIES
sudo apt install python-is-python3 -y
sudo apt install python3-venv -y
sudo apt-get install python3-dev -y
sudo apt-get install build-essential -y
sudo apt-get install libffi-dev -y
sudo apt-get install -y libxml2-dev libxslt-dev

# CREATE SOURCE FOLDER
SOURCE_FOLDER="${{SOURCE_FOLDER:-$HOME/src}}"
mkdir -p "$SOURCE_FOLDER"
cd "$SOURCE_FOLDER"

# Setup Python virtual environment
python -m venv venv
. venv/bin/activate
pip install shareddata --upgrade

# CREATE SYSTEMD SERVICE
sudo bash -c 'cat > /etc/systemd/system/shareddata-worker.service <<EOF
[Unit]
Description=SharedData Worker
After=network.target

[Service]
User={os.environ['USER']}
WorkingDirectory={os.environ.get('SOURCE_FOLDER', '$HOME/src')}
ExecStart={os.environ.get('SOURCE_FOLDER', '$HOME/src')}/venv/bin/python -m SharedData.Routines.Worker --batchjobs {batchjobs}
EnvironmentFile=/home/{os.environ['USER']}/shareddata-worker.env
LimitNOFILE=65536
Restart=on-failure
RestartSec=15

[Install]
WantedBy=multi-user.target
EOF'

sudo systemctl daemon-reload
sudo systemctl enable shareddata-worker
sudo systemctl restart shareddata-worker
sudo journalctl -f -u shareddata-worker
"""
        return Response(script, mimetype='text/x-sh')
    except Exception as e:
        error_data = json.dumps({'error': str(e)}).encode('utf-8')
        response = Response(error_data, status=500, mimetype='application/json')
        response.headers['Content-Length'] = len(error_data)
        return response
