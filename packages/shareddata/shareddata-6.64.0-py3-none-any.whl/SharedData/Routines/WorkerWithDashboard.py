# SharedData/Routines/WorkerWithDashboard.py

# implements a decentralized routines worker with Flask dashboard for configuration
# connects to worker pool
# broadcast heartbeat
# listen to commands
# includes Flask dashboard for setting environment variables

import os
import subprocess
import time
import sys
import threading
import numpy as np
import importlib.metadata
import argparse
import psutil
from flask import Flask, request, jsonify, render_template_string

# Import SharedData Logger
from SharedData.Logger import Logger

# Global variables for environment state
isconfigured = 'SHAREDDATA_ENDPOINT' in os.environ and 'SHAREDDATA_TOKEN' in os.environ

# Initialize ENV_STATE with current environment variables (excluding system vars)
system_vars = [
    'PATH', 'HOME', 'USER', 'SHELL', 'PWD', 'LANG', 'LC_ALL', 'TERM',
    'PYTHONPATH', 'VIRTUAL_ENV', 'CONDA_DEFAULT_ENV', 'FLASK_APP'
]

ENV_STATE = {
    'configured': isconfigured,
    'initial_token': os.environ.get('SHAREDDATA_TOKEN', '') if isconfigured else None
}

# Add non-system environment variables to state
for key, value in os.environ.items():
    if key not in system_vars and not key.startswith('_'):
        ENV_STATE[key] = value

# Only import SharedData-dependent modules after env vars are set
shdata = None
ClientAPI = None
WorkerPool = None

def init_shareddata_modules():
    """Initialize SharedData modules after environment variables are set"""
    global shdata, ClientAPI, WorkerPool
    
    try:
        # Now we can safely import SharedData modules since env vars are set
        import SharedData.Routines.WorkerLib as WorkerLib
        import SharedData.IO.AWSKinesis as AWSKinesis
        from SharedData.SharedData import SharedData
        from SharedData.IO import ClientAPI as ClientAPI_module
        from SharedData.IO.ClientAPI import ClientAPI
        from SharedData.Routines.WorkerPool import WorkerPool as WorkerPool_module            
        
        # Make WorkerLib functions available globally
        globals().update({name: getattr(WorkerLib, name) for name in dir(WorkerLib) if not name.startswith('_')})
        globals().update({name: getattr(AWSKinesis, name) for name in dir(AWSKinesis) if not name.startswith('_')})
        
        shdata = SharedData('SharedData.Routines.WorkerWithDashboard')
        # ClientAPI is now the class, not the module
        WorkerPool = WorkerPool_module
        
        # Now that environment variables are set, try to add API handler for logging
        Logger.add_api_handler_if_configured()
        
        ENV_STATE['configured'] = True
        Logger.log.info("SharedData modules initialized successfully")
        return True
    except Exception as e:
        Logger.log.error(f"ERROR: Failed to initialize SharedData modules: {e}")
        ENV_STATE['configured'] = False
        return False

# Flask app for dashboard
app = Flask(__name__)

# Dashboard HTML template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SharedData Worker Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            background-color: #121212;
            color: #e0e0e0;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: #1e1e1e;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            border: 1px solid #333;
        }
        h1 { 
            color: #ffffff; 
            text-align: center;
            margin-bottom: 30px;
        }
        .status {
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-weight: bold;
        }
        .status.configured { background-color: #1b5e20; color: #a5d6a7; border: 1px solid #2e7d32; }
        .status.not-configured { background-color: #b71c1c; color: #ef9a9a; border: 1px solid #d32f2f; }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #b0b0b0;
        }
        input[type="text"], input[type="url"], input[type="email"], input[type="password"], select, textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #444;
            border-radius: 4px;
            font-size: 14px;
            box-sizing: border-box;
            background-color: #2a2a2a;
            color: #e0e0e0;
            font-family: 'Courier New', monospace;
        }
        input[type="text"]:focus, input[type="url"]:focus, input[type="email"]:focus, input[type="password"]:focus, select:focus, textarea:focus {
            border-color: #007bff;
            outline: none;
            box-shadow: 0 0 5px rgba(0, 123, 255, 0.3);
        }
        textarea {
            resize: vertical;
            min-height: 200px;
            white-space: pre;
            font-family: 'Courier New', monospace;
        }
        button {
            background-color: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
            transition: background-color 0.2s;
        }
        button:hover { background-color: #0056b3; }
        button.danger { background-color: #dc3545; }
        button.danger:hover { background-color: #c82333; }
        .env-display {
            background-color: #2a2a2a;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            border-left: 4px solid #007bff;
            border: 1px solid #444;
        }
        .env-var {
            margin-bottom: 10px;
        }
        .env-var strong {
            color: #ffffff;
        }
        .message {
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 20px;
            border: 1px solid;
        }
        .message.success { background-color: #1b5e20; color: #a5d6a7; border-color: #2e7d32; }
        .message.error { background-color: #b71c1c; color: #ef9a9a; border-color: #d32f2f; }
        .actions {
            text-align: center;
            margin-top: 30px;
        }
        h3 {
            color: #ffffff;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>SharedData Worker Configuration Dashboard</h1>
        
        <div class="status {{ 'configured' if status.configured else 'not-configured' }}">
            Status: {{ 'Configured and Running' if status.configured else 'Waiting for Configuration' }}
        </div>
        
        {% if message %}
        <div class="message {{ message.type }}">
            {{ message.text }}
        </div>
        {% endif %}
        
        <div class="env-display">
            <h3>Current Environment Variables:</h3>
            {% for key, value in env_vars.items() %}
                {% if key not in ['configured', 'initial_token'] %}
                <div class="env-var">
                    <strong>{{ key }}:</strong> 
                    {% if key in ['SHAREDDATA_TOKEN', 'GIT_TOKEN'] %}
                        {{ '(set)' if value else '(not set)' }}
                    {% else %}
                        {{ value or '(not set)' }}
                    {% endif %}
                </div>
                {% endif %}
            {% endfor %}
        </div>
        
        <form method="POST" action="/configure">
            {% if env_vars.initial_token %}
            <div class="form-group">
                <label for="auth_token">Authorization Token (required for changes):</label>
                <input type="password" id="auth_token" name="auth_token" 
                       placeholder="Enter initial token for authorization" required>
            </div>
            {% endif %}
            
            <div class="form-group">
                <label for="env_vars">Environment Variables (KEY=VALUE format, one per line):</label>
                <textarea id="env_vars" name="env_vars" rows="15" 
                          placeholder="SHAREDDATA_ENDPOINT=https://api.shareddata.com
SHAREDDATA_TOKEN=your-api-token
GIT_USER=your-git-username
GIT_EMAIL=your-email@example.com
GIT_TOKEN=your-git-token
GIT_ACRONYM=your-acronym
GIT_SERVER=github.com
GIT_PROTOCOL=https
USERNAME=your-username
COMPUTERNAME=YOUR-COMPUTER-NAME
USER_COMPUTER=username@COMPUTERNAME" required>{% for key, value in env_vars.items() %}{% if key not in ['configured', 'initial_token'] and value %}{{ key }}={{ value }}
{% endif %}{% endfor %}</textarea>
            </div>
            
            <div class="actions">
                <button type="submit">Configure & Start Worker</button>
                <button type="button" class="danger" onclick="resetConfig()">Reset Configuration</button>
            </div>
        </form>
    </div>
    
    <script>
        function resetConfig() {
            if (confirm('Are you sure you want to reset the configuration?')) {
                fetch('/reset', { method: 'POST' })
                    .then(() => location.reload());
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    message = request.args.get('message')
    message_type = request.args.get('type', 'info')
    
    message_obj = None
    if message:
        message_obj = {'text': message, 'type': message_type}
    
    return render_template_string(DASHBOARD_HTML, 
                                env_vars=ENV_STATE,
                                status=ENV_STATE,
                                message=message_obj)

@app.route('/configure', methods=['POST'])
def configure():
    global ENV_STATE
    try:
        # Check authorization if initial token exists
        if ENV_STATE.get('initial_token'):
            auth_token = request.form.get('auth_token', '').strip()
            if not auth_token or auth_token != ENV_STATE.get('initial_token'):
                return dashboard() + "?message=Invalid authorization token&type=error"
        
        # Parse environment variables from multi-line input
        env_vars_text = request.form.get('env_vars', '').strip()
        if not env_vars_text:
            return dashboard() + "?message=Environment variables are required&type=error"
        
        # Parse KEY=VALUE pairs
        parsed_vars = {}
        for line in env_vars_text.split('\n'):
            line = line.strip()
            if line and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Remove surrounding quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                if key and value:
                    parsed_vars[key] = value
        
        # Check for required variables
        required_vars = [
            'SHAREDDATA_ENDPOINT', 'SHAREDDATA_TOKEN', 'GIT_USER', 
            'GIT_EMAIL', 'GIT_TOKEN', 'GIT_ACRONYM'
        ]
        
        missing_vars = [var for var in required_vars if var not in parsed_vars or not parsed_vars[var]]
        if missing_vars:
            return dashboard() + f"?message=Missing required variables: {', '.join(missing_vars)}&type=error"
        
        # Set all parsed environment variables
        for key, value in parsed_vars.items():
            os.environ[key] = value
            ENV_STATE[key] = value
        
        # Persist environment variables in Docker container
        try:
            # Also write to /etc/environment for system-wide persistence
            with open('/etc/environment', 'a') as f:
                for key, value in parsed_vars.items():
                    f.write(f"{key}={value}\n")
        except Exception as e:
            Logger.log.warning(f"Failed to persist environment variables to file: {e}")
        
        # Set default values for common variables if not provided
        default_vars = {
            'GIT_SERVER': 'github.com',
            'GIT_PROTOCOL': 'https'
        }
        
        for key, default_value in default_vars.items():
            if key not in parsed_vars:
                os.environ[key] = default_value
                ENV_STATE[key] = default_value
        
        # Auto-generate USER_COMPUTER if USERNAME and COMPUTERNAME are provided
        if 'USERNAME' in parsed_vars and 'COMPUTERNAME' in parsed_vars:
            user_computer = f"{parsed_vars['USERNAME']}@{parsed_vars['COMPUTERNAME'].upper()}"
            os.environ['USER_COMPUTER'] = user_computer
            ENV_STATE['USER_COMPUTER'] = user_computer
            
        git_config()
        
        ENV_STATE['configured'] = True
        
        # Set initial token if this is the first configuration
        if not ENV_STATE.get('initial_token'):
            ENV_STATE['initial_token'] = parsed_vars.get('SHAREDDATA_TOKEN')
        
        Logger.log.info(f"INFO: Worker configured with {len(parsed_vars)} environment variables")
        return dashboard() + "?message=Configuration saved successfully! Worker is now running.&type=success"
            
    except Exception as e:
        Logger.log.error(f"ERROR: Failed to configure: {e}")
        return dashboard() + f"?message=Configuration failed: {str(e)}&type=error"

def git_config():
    # Configure git with error handling
    git_configs = [
        ("user.name", os.environ['GIT_USER']),
        ("user.email", os.environ['GIT_EMAIL']),
        ("credential.helper", "!f() {{ echo username=\\$GIT_USER; echo password=\\$GIT_TOKEN; }};f"),
        ("pull.rebase", "false")
    ]
    
    for config_key, config_value in git_configs:
        try:
            result = subprocess.run(
                ["git", "config", "--global", config_key, config_value],
                check=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            Logger.log.debug(f"Git config set: {config_key}")
        except subprocess.CalledProcessError as e:
            Logger.log.error(f"Failed to set git config {config_key}: {e.stderr}")
            return dashboard() + f"?message=Git configuration failed for {config_key}: {e.stderr}&type=error"
        except subprocess.TimeoutExpired:
            Logger.log.error(f"Timeout setting git config {config_key}")
            return dashboard() + f"?message=Git configuration timed out for {config_key}&type=error"
        except Exception as e:
            Logger.log.error(f"Unexpected error setting git config {config_key}: {e}")
            return dashboard() + f"?message=Unexpected error in git configuration: {e}&type=error"

@app.route('/reset', methods=['POST'])
def reset():
    global ENV_STATE
    try:
        # Clear all non-system environment variables that were set by the dashboard
        vars_to_preserve = [
            'PATH', 'HOME', 'USER', 'SHELL', 'PWD', 'LANG', 'LC_ALL', 'TERM',
            'PYTHONPATH', 'VIRTUAL_ENV', 'CONDA_DEFAULT_ENV', 'FLASK_APP'
        ]
        
        # Get list of variables to clear (exclude system vars)
        vars_to_clear = []
        for key in list(os.environ.keys()):
            if key not in vars_to_preserve and not key.startswith('_'):
                vars_to_clear.append(key)
        
        # Clear environment variables
        for var in vars_to_clear:
            if var in os.environ:
                del os.environ[var]
        
        # Reset global state to initial values
        ENV_STATE.clear()
        ENV_STATE.update({
            'configured': False,
            'initial_token': None
        })
        
        Logger.log.info("INFO: Configuration reset - all environment variables cleared")
        return jsonify({'status': 'success', 'message': 'Configuration reset'})
        
    except Exception as e:
        Logger.log.error(f"ERROR: Failed to reset configuration: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/status')
def status():
    return jsonify({
        'configured': ENV_STATE.get('configured', False),
        'has_initial_token': bool(ENV_STATE.get('initial_token')),
        'environment_variables': {k: v for k, v in ENV_STATE.items() 
                                if k not in ['configured', 'initial_token']},
        'total_vars_count': len([k for k in ENV_STATE.keys() 
                               if k not in ['configured', 'initial_token']])
    })

# Worker logic (runs in separate thread)
def worker_main(dashboard_args):
    """Main worker loop that runs after configuration"""
    # Create new parser that includes dashboard args
    parser = argparse.ArgumentParser(description="Worker configuration")
    parser.add_argument('--schedules', default='', help='Schedules to start')
    parser.add_argument('--server', type=bool, default=False, help='Server port number')
    parser.add_argument('--port', type=int, default=8002, help='Server port number')
    parser.add_argument('--nproc', type=int, default=4, help='Number of server processes')
    parser.add_argument('--nthreads', type=int, default=8, help='Number of server threads')
    parser.add_argument('--batchjobs', type=int, default=0, help='Max number of jobs to fetch')
    parser.add_argument('--sleep', type=int, default=5, help='Sleep time between fetches')
    # Add dashboard args
    parser.add_argument('--dashboard-port', type=int, default=8080, help='Dashboard port number')
    parser.add_argument('--dashboard-host', default='0.0.0.0', help='Dashboard host')
    
    # Parse only the worker-specific args
    worker_args = []
    skip_next = False
    for i, arg in enumerate(sys.argv[1:]):
        if skip_next:
            skip_next = False
            continue
        if arg.startswith('--dashboard-'):
            if '=' not in arg and i + 1 < len(sys.argv[1:]):
                skip_next = True
            continue
        worker_args.append(arg)
    
    args = parser.parse_args(worker_args)

    # Check if already configured or wait for configuration
    if ENV_STATE['configured']:
        Logger.log.info("INFO: Environment variables already set, starting worker immediately...")
    else:
        Logger.log.info("INFO: Worker waiting for configuration via dashboard...")
        while not ENV_STATE['configured']:
            time.sleep(5)
    
    # Initialize SharedData modules now that we have configuration
    if not init_shareddata_modules():
        Logger.log.error("ERROR: Failed to initialize SharedData modules, exiting...")
        return
        
    Logger.log.info("Worker configuration detected, starting worker logic...")
    
    try:
        # Import worker-specific modules
        import SharedData.Routines.WorkerLib as WorkerLib
        
        # Make functions available locally
        start_server = WorkerLib.start_server
        start_logger = WorkerLib.start_logger
        start_schedules = WorkerLib.start_schedules
        update_routines = WorkerLib.update_routines
        validate_command = WorkerLib.validate_command
        process_command = WorkerLib.process_command
        remove_finished_routines = WorkerLib.remove_finished_routines
        remove_finished_batch_jobs = WorkerLib.remove_finished_batch_jobs
        
        if args.server:
            coll = shdata.collection('Text','RT','WORKERPOOL','COMMANDS')
            coll = shdata.collection('Text','RT','WORKERPOOL','JOBS')    
            WorkerPool.create_indexes()
            start_server(args.port, args.nproc, args.nthreads)    
            start_logger()
            update_jobs_status_thread = threading.Thread(target=WorkerPool.update_jobs_status, daemon=True)
            update_jobs_status_thread.start()
            
        SCHEDULE_NAMES = args.schedules
        if SCHEDULE_NAMES != '':
            Logger.log.info('SharedData Worker schedules:%s STARTED!' % (SCHEDULE_NAMES))
            start_schedules(SCHEDULE_NAMES)    

        lastheartbeat = time.time()
        SLEEP_TIME = int(args.sleep)
        SHAREDDATA_VERSION = ''
        
        try:
            SHAREDDATA_VERSION = importlib.metadata.version("shareddata")    
        except:
            pass    

        cpu_model = WorkerPool.get_cpu_model()
        mem = psutil.virtual_memory()
        mem_total_gb = mem.total / (1024 ** 3)     
        Logger.log.info(
            "ROUTINE STARTED!"
            f"{cpu_model} {mem_total_gb:.1f} RAM"
        )

        batch_jobs = []
        MAX_BATCH_JOBS = int(args.batchjobs)
        completed_batch_jobs = 0
        error_batch_jobs = 0
        routines = []
        
        # Main worker loop
        while ENV_STATE['configured']:
            fetch_jobs = 0
            running_batch_jobs = len(batch_jobs)
            if running_batch_jobs < MAX_BATCH_JOBS:
                fetch_jobs = MAX_BATCH_JOBS - running_batch_jobs

            jobs = []
            try:
                jobs = ClientAPI.get_workerpool(fetch_jobs=fetch_jobs)
            except Exception as e:
                Logger.log.error(f'Error fetching jobs: {e}')
                time.sleep(15)
            
            update_routines(routines)
            for command in jobs:           
                if ('job' in command) & ('target' in command):
                    if ((command['target'].upper() == os.environ.get('USER_COMPUTER', '').upper())
                            | (command['target'] == 'ALL')):                
                        update_routines(routines)
                        command = validate_command(command)
                        process_command(command, routines, batch_jobs)
                        routines = remove_finished_routines(routines)

            routines = remove_finished_routines(routines)
            batch_jobs, nfinished, nerror = remove_finished_batch_jobs(batch_jobs)
            completed_batch_jobs += nfinished
            error_batch_jobs += nerror    

            if (time.time()-lastheartbeat > 15):
                lastheartbeat = time.time()
                nroutines = len(routines)
                # Fetch CPU and memory usage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory()
                mem_percent = mem.percent
                mem_total_gb = mem.total / (1024 ** 3)        

                Logger.log.debug(
                    f"#heartbeat# {SHAREDDATA_VERSION},"
                    f"{nroutines}routines,"
                    f"{running_batch_jobs}/{MAX_BATCH_JOBS}jobs,"
                    f"{completed_batch_jobs}completed,"
                    f"{error_batch_jobs}errors,"
                    f"cpu={cpu_percent:.1f}%,"
                    f"mem={mem_percent:.1f}%"            
                )
            
            time.sleep(SLEEP_TIME * np.random.rand())
            
    except Exception as e:
        Logger.log.error(f"Worker error: {e}")
        ENV_STATE['configured'] = False

if __name__ == '__main__':

    # Connect the Logger to SharedData system
    Logger.connect('SharedData.Routines.WorkerWithDashboard')

    # Parse arguments for dashboard
    parser = argparse.ArgumentParser(description="Worker with Dashboard")
    parser.add_argument('--dashboard-port', type=int, default=8080, help='Dashboard port number')
    parser.add_argument('--dashboard-host', default='0.0.0.0', help='Dashboard host')
    args, unknown = parser.parse_known_args()
    
    Logger.log.info(f"Starting SharedData Worker with Dashboard on {args.dashboard_host}:{args.dashboard_port}")
    Logger.log.info("Access the configuration dashboard in your browser")

    # Note: SharedData modules will be initialized when needed (either immediately if env vars are set,
    # or after configuration via dashboard)
    
    # Start worker in separate thread
    worker_thread = threading.Thread(target=worker_main, args=(args,), daemon=True)
    worker_thread.start()
    
    # Start Flask dashboard
    app.run(host=args.dashboard_host, port=args.dashboard_port, debug=False)
