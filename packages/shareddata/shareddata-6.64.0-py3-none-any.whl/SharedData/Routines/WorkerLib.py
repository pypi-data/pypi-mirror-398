# SharedData/Routines/WorkerLib.py

# implements a decentralized routines worker
# connects to worker pool
# broadcast heartbeat
# listen to commands

import os
import sys
import psutil
import time
import subprocess
import threading
from subprocess import DEVNULL
from threading import Thread
import signal


import pandas as pd
import numpy as np
from pathlib import Path

from SharedData.Logger import Logger
from SharedData.IO.ClientAPI import ClientAPI


def get_environment_file_path() -> Path:
    """
    Get the path to the SharedData environment file.
    
    Returns:
        Path: Path to ~/.shareddata.env
    """
    return Path.home() / '.shareddata.env'


def load_environment_file():
    """
    Load persisted environment variables from ~/.shareddata.env into os.environ.
    
    Note: This is also called automatically by Defaults.py via load_dotenv().
    This function exists for explicit calls and uses dotenv for consistency.
    """
    from dotenv import load_dotenv
    env_file = get_environment_file_path()
    if env_file.is_file():
        load_dotenv(env_file, override=False)


def persist_environment_variable(name: str, value: str):
    """
    Persist an environment variable to the appropriate location based on OS.
    
    Linux/macOS: Writes 'NAME=value' to ~/.shareddata.env (dotenv format)
    Windows: Uses 'setx' command for permanent user-level persistence
    
    Args:
        name: Environment variable name
        value: Environment variable value
    """
    if os.name == 'posix':
        # Linux/macOS: Update ~/.shareddata.env file (dotenv format)
        env_file = get_environment_file_path()
        
        # Read existing content
        existing_lines = []
        if env_file.is_file():
            with env_file.open('r') as f:
                existing_lines = f.readlines()
        
        # Check if variable already exists and update it
        var_prefix = f'{name}='
        updated = False
        new_lines = []
        
        for line in existing_lines:
            stripped = line.strip()
            # Handle both 'NAME=' and 'export NAME=' formats
            if stripped.startswith(var_prefix) or stripped.startswith(f'export {var_prefix}'):
                # Replace existing line with dotenv format (no export prefix)
                new_lines.append(f'{name}="{value}"\n')
                updated = True
            else:
                new_lines.append(line)
        
        # Append if not found
        if not updated:
            # Ensure newline before new entry if file doesn't end with one
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines.append('\n')
            new_lines.append(f'{name}="{value}"\n')
        
        # Write atomically
        tmp_file = env_file.with_suffix('.env.tmp')
        with tmp_file.open('w') as f:
            f.writelines(new_lines)
        tmp_file.replace(env_file)
        
    elif os.name == 'nt':
        # Windows: Use setx for permanent user-level persistence
        try:
            subprocess.run(
                ['setx', name, value],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f'Failed to persist env var {name} via setx: {e.stderr}')


def compare_routines(routine1,routine2):
    """
    Compares two routines by hashing them and determining if their hashes are equal.
    
    Parameters:
        routine1: The first routine to compare.
        routine2: The second routine to compare.
    
    Returns:
        bool: True if both routines have the same hash (indicating they are equal), False otherwise.
    """
    hash1 = hash_routine(routine1)
    hash2 = hash_routine(routine2)

    return hash1 == hash2

def hash_routine(routine):
    """
    Generate a string representation of a routine dictionary by concatenating specific key values.
    
    The function builds a string by appending the values of the keys 'repo', 'branch', 'routine', and 'args'
    from the input dictionary `routine` in a specific format:
    - 'repo' value (if present)
    - '#' followed by 'branch' value (if present)
    - '/' followed by 'routine' value (if present)
    - a space followed by 'args' value (if present)
    
    Parameters:
        routine (dict): A dictionary that may contain the keys 'repo', 'branch', 'routine', and 'args'.
    
    Returns:
        str: A concatenated string representing the routine hash.
    """
    rhash = ''
    if ('repo' in routine):
        rhash = routine['repo']
    if ('branch' in routine):
        rhash += '#' + routine['branch']
    if ('routine' in routine):
        rhash += '/'+routine['routine']
    if ('args' in routine):
        rhash += ' ' + routine['args']
    return rhash

def upsert_routine(newroutine,routines):
    """
    Updates an existing routine in the routines list if a matching routine is found based on 'pid' or command comparison; otherwise, appends the new routine to the list.
    
    Parameters:
        newroutine (dict): The routine dictionary to be inserted or used for updating.
        routines (list): A list of routine dictionaries to be searched and potentially updated.
    
    Behavior:
        - If a routine with the same 'pid' as newroutine exists, it updates that routine with newroutine's data.
        - If no 'pid' match is found, it uses the compare_routines function to find a matching routine by command and updates it.
        - If no matching routine is found by either method, newroutine is appended to the routines list.
    """
    updated = False
    for routine in routines:
        if ('pid' in routine):
            if newroutine['pid'] == routine['pid']:
                routine.update(newroutine)
                updated = True
        elif compare_routines(newroutine,routine['command']):
            routine.update(newroutine)
            updated = True

    if not updated:
        routines.append(newroutine)

def get_workerpool_jobs(batch_jobs):
    fetch_jobs = 0
    running_batch_jobs = len(batch_jobs)
    if running_batch_jobs < int(os.environ['MAX_BATCH_JOBS']):
        fetch_jobs = int(os.environ['MAX_BATCH_JOBS']) - running_batch_jobs
    jobs = []    
    try:
        jobs = ClientAPI.get_workerpool(fetch_jobs=fetch_jobs)
    except Exception as e:
        Logger.log.error(f'Error fetching jobs: {e}')
        time.sleep(15)

    return jobs

def update_routines(routines):

    """
    Scan currently running processes to identify and update routines related to a specific source folder.
    
    This function inspects all active processes to find those whose command line arguments reference the source folder specified by the environment variable 'SOURCE_FOLDER'. It extracts routine information such as process ID, repository, branch, routine name, and arguments, then updates the provided routines dictionary using the `upsert_routine` function.
    
    Parameters:
        routines (dict): A dictionary to be updated with information about detected routines.
    
    Notes:
    - Handles differences in Python executable paths between POSIX and non-POSIX systems.
    - Safely ignores processes that no longer exist or cannot be accessed.
    - Uses numpy for command line argument analysis.
    """
    source_path = Path(os.environ['SOURCE_FOLDER'])
    if os.name == 'posix':
        python_path = 'venv/bin/python'
    else:
        python_path = 'venv/Scripts/python.exe'

    processes = []
    for processes in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
        try:
            if processes.info['cmdline'] and processes.info['cmdline'][0].startswith(str(source_path)):
                proc = processes.info
                if len(proc['cmdline']) >= 2:
                    idx = np.array(proc['cmdline']) == '-m'
                    if np.any(idx):
                        i = np.argmax(idx)
                        if 'SharedData' in proc['cmdline'][i+1]:
                            routine = {}
                            routine['pid'] = proc['pid']
                            routine['process'] = psutil.Process(routine['pid'])
                            routine['command'] = {}
                            routine['command']['repo'] = 'SharedData'
                            routine['command']['routine'] = proc['cmdline'][i+1].replace('SharedData.', '')
                            if len(proc['cmdline']) >= i+3:
                                routine['command']['args'] = ' '.join(proc['cmdline'][i+2:])
                            upsert_routine(routine,routines)
                    else:
                        idx = [str(source_path) in s for s in proc['cmdline']]
                        if np.any(idx):
                            i = np.argmax(idx)
                            for cmd in proc['cmdline'][i+1:]:
                                i=i+1
                                if str(source_path) in cmd:
                                    cmd = ' '.join(proc['cmdline'][i:])                                    
                                    routinestr = cmd.replace(str(source_path), '')
                                    if routinestr.startswith(os.sep):
                                        routinestr = routinestr[1:]
                                    cmdsplit = routinestr.split(os.sep)
                                    routine = {}
                                    routine['pid'] = proc['pid']
                                    routine['process'] = psutil.Process(routine['pid'])
                                    routine['command'] = {}
                                    if '#' in cmdsplit[0]:                                        
                                        routine['command']['repo'] = cmdsplit[0].split('#')[0]
                                        routine['command']['branch'] = cmdsplit[0].split('#')[1]
                                    else:
                                        routine['command']['repo'] = cmdsplit[0]
                                    
                                    scriptstr = os.sep.join(cmdsplit[1:])
                                    scriptsplit = scriptstr.split(' ')
                                    routine['command']['routine'] = scriptsplit[0]
                                    if len(scriptsplit) > 1:
                                        routine['command']['args'] = ' '.join(scriptsplit[1:])
                                    upsert_routine(routine,routines)
                                    break

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def validate_command(command):
    """
    Sanitizes and validates the input command dictionary by cleaning specific keys.
    
    - Removes the 'args' key if its value is an empty string, the string 'nan' (case-insensitive), or a NaN float.
    - Converts the 'args' value to a string if it is neither a string nor a dictionary.
    - Removes the 'branch' key if its value is an empty string.
    - Returns the cleaned command dictionary.
    """
    # Sanitize 'args'
    if 'args' in command:
        # Remove 'args' if it's empty, 'nan' (str), or actual NaN (float from pandas)
        val = command['args']
        if (val == '') or (str(val).lower() == 'nan'):
            del command['args']
        elif isinstance(val, float) and np.isnan(val):
            del command['args']
        elif not isinstance(val, (str, dict)):
            # If it's not a string or dict (e.g. list), convert to string
            command['args'] = str(val)
                
    # Add default values or cleanup others as needed
    if 'branch' in command and command['branch'] == '':
        del command['branch']  # remove empty branch if not used

    return command

last_restart = {}
def process_command(command,routines,batch_jobs):

    """
    Process a given command by dispatching it to the appropriate handler based on the job type.
    
    This function manages various job types including batch jobs, commands, installations, routines,
    killing, restarting, stopping, status reporting, resetting, upgrading, and ping-pong communication.
    It uses threading to run routines and commands asynchronously, maintains job and routine lists,
    and ensures that routines are not restarted too frequently.
    
    Parameters:
        command (dict): A dictionary containing the job details and parameters. Must include a 'job' key.
        routines (list): A list to keep track of currently running routine dictionaries.
        batch_jobs (list): A list to keep track of batch job dictionaries.
    
    Job types handled:
        - 'batch': Starts a batch job in a new thread.
        - 'command': Sends a command asynchronously.
        - 'install': Installs a repository if not already running.
        - 'routine': Runs a routine script, avoiding frequent restarts.
        - 'kill': Kills a running routine.
        - 'restart': Restarts a routine, ensuring no rapid duplicates.
        - 'stop': Placeholder for stopping a routine (not implemented).
        - 'status': Logs the status of all running routines.
        - 'reset': Resets the program
    """
    if command['job'] == 'batch':
        start_time = time.time()
        job = command
        job.update({            
            'thread': None,
            'process': None,
            'subprocess': None,
            'start_time': start_time,
        })
        thread = Thread(target=run_routine,
                        args=(job['command'], job, True))
        job['thread'] = thread
        batch_jobs.append(job)
        thread.start()        
        return

    elif command['job'] == 'command':
        start_time = time.time()
        routine = {
            'command': command,
            'thread': None,
            'process': None,
            'subprocess': None,
            'start_time': start_time,
        }
        thread = Thread(target=send_command,args=(command['command'],))
        routine['thread'] = thread
        routines.append(routine)
        thread.start()

    elif command['job'] == 'install':
        if not isrunning(command,routines):
            start_time = time.time()
            routine = {
                'command': command,
                'thread': None,
                'start_time': start_time,
            }
            thread = Thread(target=install_repo,args=(command,False))
            routine['thread'] = thread
            routines.append(routine)
            thread.start()
        else:
            Logger.log.info('Already installing %s!\n' % (str(command)))

    elif command['job'] == 'routine':
        # expects command:
        # command = {
        #     "sender" : "MASTER",
        #     "target" : user,
        #     "job" : "routine",
        #     "repo" : routine.split('/')[0],
        #     "routine" : '/'.join(routine.split('/')[1:])+'.py',
        #     "branch" : branch,
        # }
        restart = True
        rhash = hash_routine(command)
        if rhash in last_restart.keys():
            if time.time()-last_restart[rhash] < 30:
                restart = False
        
        if restart:
            last_restart[rhash] = time.time()
            if not isrunning(command,routines):
                start_time = time.time()
                routine = {
                    'command': command,
                    'thread': None,
                    'process': None,
                    'subprocess': None,
                    'start_time': start_time,
                }
                thread = Thread(target=run_routine,
                                args=(command, routine))
                routine['thread'] = thread
                routines.append(routine)
                thread.start()
            else:
                Logger.log.info('Already running %s!\n' %
                                (str(command)))

    elif command['job'] == 'kill':
        kill_routine(command,routines)

    elif command['job'] == 'restart':
        #TODO: if called multiple times in a row it dupicates the routine        
        restart = True
        rhash = hash_routine(command)
        if rhash in last_restart.keys():
            if time.time()-last_restart[rhash] < 30:
                restart = False
        
        if restart:
            last_restart[rhash] = time.time()
            kill_routine(command,routines)
            routines = remove_finished_routines(routines)
            if not isrunning(command,routines):
                start_time = time.time()
                routine = {
                    'command': command,
                    'thread': None,
                    'process': None,
                    'subprocess': None,
                    'start_time': start_time,
                }
                thread = Thread(target=run_routine,
                                args=(command, routine))
                routine['thread'] = thread
                routines.append(routine)
                thread.start()

    elif command['job'] == 'stop':
        # TODO: implement a stop command
        pass

    elif command['job'] == 'status':

        Logger.log.info('Status: %i process' % (len(routines)))
        n = 0
        for routine in routines:
            n += 1
            rhash = hash_routine(routine['command'])            
            statusstr = 'Status %i: running %s' % (n, rhash)            
            if 'start_time' in routine:
                statusstr = '%s %.2fs' % (
                    statusstr, time.time()-routine['start_time'])
            Logger.log.info(statusstr)

    elif command['job'] == 'reset':
        reset_program(command.get('reset_nginx', False))
    
    elif command['job'] == 'upgrade':
        Logger.log.info(f'Upgrading Worker {command.get("version", "latest")}...')
        if os.name == 'nt':
            if not 'version' in command:
                send_command(r'venv\Scripts\python.exe -m pip install shareddata --upgrade')
            else:
                send_command(r'venv\Scripts\python.exe -m pip install shareddata==%s' % command['version'])
        elif os.name == 'posix':
            if not 'version' in command:
                send_command('venv/bin/python -m pip install shareddata --upgrade ')
            else:
                send_command('venv/bin/python -m pip install shareddata==%s' % command['version'])

        reset_program(True)

    elif command['job'] == 'ping':
        Logger.log.info('pong')

    elif command['job'] == 'pong':
        Logger.log.info('ping')

    elif command['job'] == 'setenv':
        # Set environment variables on this worker
        # Supports single var: env_name, env_value
        # Or bulk mode: env_vars = {KEY1: val1, KEY2: val2}
        persist = command.get('persist', True)
        restart = command.get('restart', False)
        
        env_vars = {}
        if 'env_vars' in command and isinstance(command['env_vars'], dict):
            env_vars = command['env_vars']
        elif 'env_name' in command and 'env_value' in command:
            env_vars[command['env_name']] = command['env_value']
        
        if not env_vars:
            Logger.log.warning('setenv command received but no variables specified')
            return
        
        for name, value in env_vars.items():
            # Set in current process immediately
            os.environ[name] = str(value)
            Logger.log.info(f'Set environment variable {name}=***')
            
            # Persist if requested
            if persist:
                try:
                    persist_environment_variable(name, str(value))
                    Logger.log.info(f'Persisted environment variable {name}')
                except Exception as e:
                    Logger.log.error(f'Failed to persist {name}: {e}')
            
            if name == 'GIT_USER':
                subprocess.run(
                    ['git', 'config', '--global', 'user.name', str(value)],
                    check=False,
                    stdout=DEVNULL,
                    stderr=DEVNULL
                )
            elif name == 'GIT_EMAIL':
                subprocess.run(
                    ['git', 'config', '--global', 'user.email', str(value)],
                    check=False,
                    stdout=DEVNULL,
                    stderr=DEVNULL
                )
            elif name == 'GIT_TOKEN':
                # Configure git to use credential.helper store
                subprocess.run(
                    ['git', 'config', '--global', 'credential.helper', 'store'],
                    check=False,
                    stdout=DEVNULL,
                    stderr=DEVNULL
                )                
                # Write credentials to ~/.git-credentials file
                git_server = os.environ.get('GIT_SERVER', '')
                git_user = os.environ.get('GIT_USER', '')
                git_protocol = os.environ.get('GIT_PROTOCOL', 'https')
                credential_line = f'{git_protocol}://{git_user}:{str(value)}@{git_server}\n'
                git_credentials_file = Path.home() / '.git-credentials'
                
                # Read existing credentials and update/add the entry
                existing_lines = []
                if git_credentials_file.is_file():
                    existing_lines = git_credentials_file.read_text().splitlines()
                
                # Remove any existing entry for this server
                new_lines = [line for line in existing_lines if git_server not in line]
                new_lines.append(credential_line.strip())
                
                # Write back atomically
                git_credentials_file.write_text('\n'.join(new_lines) + '\n')
                Logger.log.info(f'Stored git credentials for {git_server}')
        
        # Restart worker if requested (to reload all modules with new env)
        if restart:
            Logger.log.info('Restarting worker to apply environment changes...')
            reset_program()

import hashlib
from pathlib import Path
import sys, json

def hash_file(path: Path, block_size: int = 1 << 16) -> str:
    """
    Compute and return the SHA-256 hash of the file at the given path.
    
    Reads the file in chunks of size `block_size` to efficiently handle large files.
    If the specified path does not point to a valid file, returns None.
    
    Args:
        path (Path): The file system path to the file to be hashed.
        block_size (int, optional): The size of each read chunk in bytes. Defaults to 65536 (64 KiB).
    
    Returns:
        str or None: The hexadecimal SHA-256 digest of the file contents, or None if the file does not exist.
    """
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(block_size), b""):
            h.update(chunk)
    return h.hexdigest()

def load_last_hash(venv_root: Path) -> str | None:
    """
    Load the stored requirements hash from the .last_requirements_hash file in the specified virtual environment root directory.
    
    This function attempts to read the file as a JSON object and extract the 'req_hash' key. If the file does not exist, it returns None.
    If the file contents are not valid JSON (e.g., due to legacy format or corruption), it falls back to returning the raw file content as a stripped string.
    
    Args:
        venv_root (Path): The root directory of the virtual environment.
    
    Returns:
        str | None: The stored requirements hash if available, otherwise None.
    """
    f = venv_root / ".last_requirements_hash"
    if not f.is_file():
        return None
    try:
        blob = json.loads(f.read_text())
        return blob.get("req_hash")
    except Exception:
        # legacy / corrupted file?  fall back to raw text
        return f.read_text().strip()
    
def save_last_hash(venv_root: Path, new_hash: str):
    """
    Save the given hash string atomically to a file named '.last_requirements_hash' inside the specified virtual environment root directory.
    
    This function ensures the target directory exists, writes the hash as JSON to a temporary file, and then atomically replaces the existing hash file with the temporary file to avoid partial writes.
    
    Args:
        venv_root (Path): The root directory of the virtual environment where the hash file will be saved.
        new_hash (str): The new hash string to be saved.
    """
    venv_root.mkdir(parents=True, exist_ok=True)          # ensure dir exists
    tmp = venv_root / ".last_requirements_hash.tmp"
    dst = venv_root / ".last_requirements_hash"
    tmp.write_text(json.dumps({"req_hash": new_hash}))
    tmp.replace(dst)                                      # atomic on POSIX


installed_repos = {}
install_lock = threading.Lock()

def install_repo(command, quiet=False):

    """
    Installs or updates a Git repository specified by the `command` dictionary.
    
    This function manages concurrent installations using a lock and tracks installation status to prevent duplicate installs.
    It supports cloning a new repository or pulling updates from an existing one, optionally checking out a specified branch.
    It also handles creating a Python virtual environment and installing required packages from a `requirements.txt` file if present.
    
    Parameters:
        command (dict): A dictionary containing repository installation parameters, including:
            - 'repo' (str): The name of the repository.
            - 'branch' (str, optional): The branch to checkout and pull.
        quiet (bool, optional): If True, suppresses informational logging. Defaults to False.
    
    Returns:
        bool: True if the repository was successfully installed or updated, False otherwise.
    
    Notes:
    - Requires environment variables `GIT_PROTOCOL`, `GIT_SERVER`, and `GIT_ACRONYM` to construct the Git URL.
    - Requires `GIT_USER` and `GIT_TOKEN` environment variables for authentication; logs an error if missing.
    - Uses external functions and variables such as `installed_repos`, `install_lock`, `Logger`, `get_env`, `send_command`, `hash_file`, `load_last_hash`, and `save_last_hash
    """
    install = False
    if not command['repo'] in installed_repos:
        with install_lock:
            installed_repos[command['repo']] = {}
            installed_repo = installed_repos[command['repo']]
            installed_repo['isinstalling'] = True            
            install = True
    else:
        with install_lock:
            installed_repo = installed_repos[command['repo']]            
        while True:
            with install_lock:
                if not installed_repo['isinstalling']:
                   break
            time.sleep(1)
        
        with install_lock:
            installage = time.time() - installed_repo['ts']
            if installage > 5*60:
                installed_repo['isinstalling'] = True
                install = True

    if not install:
        return True
    
    if install:
        with install_lock:
            installed_repo['ts'] = time.time()

        if not quiet:
            Logger.log.info('Installing %s...' % (command['repo']))
        runroutine = False
        if ('GIT_USER' not in os.environ) or ('GIT_TOKEN' not in os.environ) or ('GIT_ACRONYM' not in os.environ):
            Logger.log.error('Installing repo %s ERROR missing git parameters'
                             % (command['repo']))
        else:

            hasbranch, requirements_path, repo_path, python_path, env = get_env(command)

            repo_exists = repo_path.is_dir()
            venv_exists = python_path.is_file()            

            # GIT_URL=os.environ['GIT_PROTOCOL']+'://'+os.environ['GIT_USER']+':'+os.environ['GIT_TOKEN']+'@'\
            #     +os.environ['GIT_SERVER']+'/'+os.environ['GIT_ACRONYM']+'/'+command['repo']
            GIT_URL = os.environ['GIT_PROTOCOL']+'://'+os.environ['GIT_SERVER']+'/' +\
                os.environ['GIT_ACRONYM']+'/'+command['repo']

            # GIT PULL OR GIT CLONE
            if repo_exists:
                if not quiet:
                    Logger.log.info('Pulling repo %s' % (command['repo']))
                requirements_lastmod = 0
                if requirements_path.is_file():
                    requirements_lastmod = os.path.getmtime(
                        str(requirements_path))

                # Checkout branch before pulling
                if hasbranch:
                    checkout_cmd = ['git', '-C', str(repo_path), 'checkout', command['branch']]
                    if not send_command(checkout_cmd):
                        Logger.log.error(f'Checking out branch {command["branch"]} FAILED!')
                        runroutine = False
                    else:
                        Logger.log.info(f'Checked out branch {command["branch"]}')
                else:
                    # Checkout main branch if no branch specified
                    checkout_cmd = ['git', '-C', str(repo_path), 'checkout', 'main']
                    if not send_command(checkout_cmd):
                        Logger.log.error(f'Checking out branch main FAILED!')
                        runroutine = False
                    else:
                        Logger.log.info(f'Checked out branch main')

                # pull existing repo
                if hasbranch:
                    cmd = ['git', '-C', str(repo_path),'pull', GIT_URL, command['branch']]
                else:
                    cmd = ['git', '-C', str(repo_path), 'pull', GIT_URL, 'main']

                pull_trials = 0
                max_trials = 10
                while pull_trials < max_trials:
                    if not send_command(cmd):
                        pull_trials += 1
                        if pull_trials<max_trials:
                            Logger.log.warning(f'Pulling repo {command["repo"]} FAILED! Retrying {pull_trials}/{max_trials}...')
                        else:
                            Logger.log.error(f'Pulling repo {command["repo"]} ERROR!')
                        runroutine = False
                        time.sleep(15)
                    else:
                        runroutine = True
                        break
                
                if (runroutine) and (requirements_path.is_file()):
                    venv_root     = repo_path / "venv"
                    new_hash      = hash_file(requirements_path)
                    stored_hash   = load_last_hash(venv_root)
                    install_requirements = (
                        not venv_exists or
                        new_hash is None or
                        stored_hash is None or
                        new_hash != stored_hash                        
                    )                    
                    runroutine = True
                    if not quiet:
                        Logger.log.info('Pulling repo %s DONE!' %
                                        (command['repo']))
                else:
                    install_requirements = False
                    runroutine = False                    
                    Logger.log.error(
                        'Pulling repo %s ERROR: requirements.txt not found!' % (command['repo']))

            else:
                if not quiet:
                    Logger.log.info('Cloning repo %s...' % (command['repo']))
                if hasbranch:
                    cmd = ['git', '-C', str(repo_path.parents[0]), 'clone',
                           '-b', command['branch'], GIT_URL, str(repo_path)]
                else:
                    cmd = ['git', '-C',
                           str(repo_path.parents[0]), 'clone', GIT_URL]
                if not send_command(cmd):
                    Logger.log.error('Cloning repo %s ERROR!' %
                                     (command['repo']))
                    runroutine = False
                else:
                    runroutine = True
                    if requirements_path.is_file():
                        install_requirements = True
                        if not quiet:
                            Logger.log.info('Cloning repo %s DONE!' %
                                            (command['repo']))
                    else:
                        install_requirements = False
                        Logger.log.error(
                            'Cloning repo %s ERROR: requirements.txt not found!' % (command['repo']))

            # TODO: ALLOW FOR PYTHON VERSION SPECIFICATION
            # CREATE VENV
            if (runroutine) and (not venv_exists):
                if not quiet:
                    Logger.log.info('Creating venv %s...' % (command['repo']))
                if not send_command(['python', '-m', 'venv', str(repo_path/'venv')]):
                    Logger.log.error('Creating venv %s ERROR!' %
                                     (command['repo']))
                    runroutine = False
                else:
                    runroutine = True
                    if requirements_path.is_file():
                        install_requirements = True
                        if not quiet:
                            Logger.log.info('Creating venv %s DONE!' %
                                            (command['repo']))
                    else:
                        install_requirements = False
                        Logger.log.error(
                            'Creating venv %s ERROR: requirements.txt not found!' % (command['repo']))

            # INSTALL REQUIREMENTS
            if (runroutine) and (install_requirements):
                if not quiet:
                    Logger.log.info('Installing requirements %s...' %
                                    (command['repo']))
                if not send_command([str(python_path), '-m', 'pip', 'install', '-r', str(requirements_path)], env=env):
                    Logger.log.error(
                        'Installing requirements %s ERROR!' % (command['repo']))
                    runroutine = False
                else:
                    runroutine = True
                    if not quiet:
                        Logger.log.info('Installing requirements %s DONE!' %
                                        (command['repo']))                        

        if runroutine:
            if install_requirements:
                venv_root = repo_path / "venv"
                new_hash = hash_file(requirements_path)
                save_last_hash(venv_root, new_hash)
            if not quiet:
                Logger.log.info('Installing %s DONE!' % (command['repo']))
        else:
            Logger.log.error('Installing %s ERROR!' % (command['repo']))

        with install_lock:
            if runroutine:
                installed_repo['ts'] = time.time()
            else:
                installed_repo['ts'] = time.time() - 5*60
            installed_repo['isinstalling'] = False
            
        return runroutine

import base64
import bson

def run_routine(command, routine, quiet=False):
    """
    Executes a specified routine from a given repository command, managing environment setup, repository installation, and subprocess execution.
    
    Parameters:
        command (dict): Contains details about the routine to run, including:
            - 'repo' (str): Repository name.
            - 'routine' (str): Routine or script to execute.
            - Optional 'args' (str or dict): Arguments to pass to the routine.
        routine (dict): Stores subprocess and process information, and may include 'hash' and 'date' for status tracking.
        quiet (bool, optional): If True, suppresses logging output. Defaults to False.
    
    Behavior:
        - Logs the start of the routine unless quiet is True.
        - Installs the repository if it is not 'SharedData'.
        - Sets up the environment and constructs the command to run the routine.
        - Encodes arguments as BSON and base64 if provided as a dictionary.
        - Posts a status update if a 'hash' is present in the routine.
        - Launches the routine as a subprocess, capturing stdout and stderr in separate threads.
        - Updates the routine dictionary with subprocess, process, and threading information.
        - Logs completion or errors accordingly.
    """
    if not quiet:
        Logger.log.info('Running routine %s/%s' %
                        (command['repo'], command['routine']))

    installed = True
    if command['repo'] != 'SharedData':
        installed = install_repo(command, quiet=quiet)

    if installed:
        # RUN ROUTINE
        if not quiet:
            Logger.log.info('Starting process %s/%s...' %
                            (command['repo'], command['routine']))

        hasbranch, requirements_path, repo_path, python_path, env = get_env(
            command)

        if command['repo'] == 'SharedData':
            cmd = [str(python_path), '-m',
                   str('SharedData.'+command['routine'])]
        else:
            cmd = [str(python_path), str(repo_path/command['routine'])]

        if 'args' in command:
            if isinstance(command['args'], dict):
                bson_data = bson.BSON.encode(command['args'])
                b64_arg = base64.b64encode(bson_data).decode('ascii')
                cmd += ['--bson', b64_arg]
            else:
                _args = command['args'].split(' ')
                if isinstance(_args, (list, tuple)):
                    cmd += _args
                else:
                    cmd += [command['args']]
        
        if 'hash' in routine:
            cmd += ['--hash', routine['hash']]
            status_msg = {
                'date': routine['date'],
                'hash': routine['hash'],
                'status': 'RUNNING',
                'job' : 'batch'
            }            
            ClientAPI.post_workerpool(status_msg)

        routine['subprocess'] = subprocess.Popen(
            cmd, env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True
        )
        routine['pid'] = routine['subprocess'].pid
        routine['process'] = psutil.Process(routine['pid'])

        # read stdout and stderr in separate threads
        stdout_thread = threading.Thread(
            target=read_stdout, args=(routine['subprocess'].stdout,True))
        stderr_thread = threading.Thread(
            target=read_stderr, args=(routine['subprocess'].stderr,True, routine))
        stdout_thread.start()
        stderr_thread.start()
        routine['stdout_thread'] = stdout_thread
        routine['stderr_thread'] = stderr_thread

        if not quiet:
            Logger.log.info('Starting process %s/%s DONE!' %
                            (command['repo'], command['routine']))
    else:
        Logger.log.error(
            'Aborting routine %s, could not install repo' % (command['routine']))

def kill_routine(command, routines):    
    """
    Attempts to terminate processes associated with specified routines based on a given command.
    
    If the command's 'repo' field is 'ALL', it attempts to terminate all processes in the routines list.
    Otherwise, it terminates only those routines whose commands match the given command.
    
    Termination is attempted gracefully by sending SIGTERM and waiting up to 15 seconds.
    If the process does not terminate, a force kill (SIGKILL) is attempted with a 5-second wait.
    Logs errors if termination fails or exceptions occur.
    
    Args:
        command (dict): A dictionary containing command details, including a 'repo' key.
        routines (list): A list of routine dictionaries, each potentially containing a 'process' key with a psutil.Process object.
    
    Returns:
        bool: True if all targeted processes were successfully terminated or already stopped, False otherwise.
    """
    success = True

    def attempt_termination(proc):        
        """
        Attempt to gracefully terminate a given process, escalating to a force kill if necessary.
        
        Parameters:
            proc (psutil.Process or None): The process to terminate. If None, the function returns True immediately.
        
        Returns:
            bool: True if the process was terminated or is not running; False if termination failed.
        
        Behavior:
        - If proc is None or the process is not running, returns True.
        - Attempts to terminate the process gracefully using SIGTERM and waits up to 15 seconds.
        - If the process does not terminate in time, attempts to force kill it and waits up to 5 seconds.
        - Logs an error if the process cannot be terminated after force kill or if other exceptions occur.
        """
        try:             
            if proc is None:                
                return True                   
            if proc.is_running():
                proc.terminate()  # Send SIGTERM
                try:
                    proc.wait(timeout=15)
                    return True
                except psutil.TimeoutExpired:
                    try:
                        proc.kill()  # Force kill
                        proc.wait(timeout=5)
                        return True
                    except psutil.TimeoutExpired:
                        # Process is still running after force kill, give up
                        Logger.log.error(f"Failed to terminate process with PID {proc.pid} after force kill")
                        return False
            else:
                return True
            
        except psutil.NoSuchProcess:  # Process already terminated
            return True
        except Exception as e:
            Logger.log.error(f"Failed to terminate process with PID {proc.pid}: {str(e)}")
            return False
        
    if command['repo'] == 'ALL':
        Logger.log.info('Kill: ALL...')
        for routine in routines:
            if 'process' in routine:
                if not attempt_termination(routine['process']):
                    success = False                
        Logger.log.info('Kill: ALL DONE!')
    else:        
        for routine in routines:                        
            if compare_routines(routine['command'], command) and ('process' in routine):
                if not attempt_termination(routine['process']):
                    success = False    

    return success

def kill(pname):
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):        
        if ('cmdline' in process.info) and (process.info['cmdline']):            
            if (pname in ' '.join(process.info['cmdline'])):
                try:
                    # Kill child processes first
                    children = process.children(recursive=True)
                    for child in children:
                        try:
                            child.terminate()
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                            pass
                    try:
                        _, alive = psutil.wait_procs(children, timeout=5)
                    except Exception:
                        alive = []
                    for child in alive:
                        try:
                            child.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                            pass

                    # Kill the parent
                    process.kill()
                    Logger.log.info(f'Killed {pname} process: {process.info["pid"]}')
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                    Logger.log.error(f'Failed to kill {pname} process: {str(e)}')

def remove_finished_routines(routines):
    """
    Filters out routines that have finished execution from a list of routine dictionaries.
    
    Each routine dictionary may contain:
    - 'process': a psutil.Process object representing a running process,
    - 'subprocess': a subprocess.Popen object representing a subprocess,
    - 'thread': a threading.Thread object,
    - optionally 'stderr' and 'command' keys for error logging.
    
    The function checks if the associated process or thread is still running. If a subprocess has exited with a non-zero exit code, it logs an error message including any captured standard error output. Routines whose processes or threads have finished are removed from the returned list.
    
    Parameters:
        routines (list): A list of dictionaries, each representing a routine with process or thread information.
    
    Returns:
        list: A new list containing only the routines that are still running.
    """
    new_routines = []
    for routine in routines:
        remove_routine = False
        
        if 'process' in routine and routine['process'] is not None:
            is_running = False
            try:
                if 'subprocess' in routine:
                    exit_code = routine['subprocess'].poll()
                    if (not exit_code is None) and (exit_code != 0):
                        stderr = ''
                        if 'stderr' in routine:
                            if len(routine['stderr']) > 1:
                                stderr = '\n'.join(routine['stderr'])
                            else:
                                stderr = routine['stderr'][0]
                        Logger.log.error('Routine %s/%s exited with code %s\n STDERR: %s' %
                                         (routine['command']['repo'], routine['command']['routine'], exit_code, stderr))
                is_running = routine['process'].is_running()
            except:
                pass
            if not is_running:
                remove_routine = True

        elif 'thread' in routine and not routine['thread'].is_alive():
            remove_routine = True

        if not remove_routine:
            new_routines.append(routine)

    return new_routines

def remove_finished_batch_jobs(batch_jobs):
    
    """
    Removes finished or errored batch jobs from the provided list of batch job routines.
    
    Each routine is evaluated to determine if it has completed or encountered an error based on subprocess exit codes or thread status. For jobs that have finished or errored, a status message is sent to a remote collection via the ClientAPI. The function returns a new list excluding these completed or errored routines, along with counts of how many jobs finished successfully and how many ended with errors.
    
    Parameters:
        batch_jobs (list of dict): List of batch job routines. Each routine may include keys such as 'process', 'subprocess', 'thread', 'date', 'hash', 'stderr', and 'start_time'.
    
    Returns:
        tuple:
            - list of dict: Filtered list of batch job routines excluding those that have finished or errored.
            - int: Count of finished batch jobs.
            - int: Count of batch jobs that ended with errors.
    """
    nfinished, nerror = 0, 0
    new_routines = []
    for routine in batch_jobs:
        remove_routine = False
        
        if 'process' in routine and routine['process'] is not None:
            is_running = False
            try:
                if 'subprocess' in routine:
                    exit_code = routine['subprocess'].poll()
                    if (not exit_code is None):
                        status_message = {
                            'date':routine['date'],
                            'hash':routine['hash'],
                            'job':'batch',
                        }
                        if (exit_code != 0):
                            nerror+=1                                
                            status_message['status']='ERROR'
                            status_message['exit_code']=exit_code

                            if 'stderr' in routine:
                                if len(routine['stderr']) > 1:
                                    status_message['stderr'] = '\n'.join(routine['stderr'])
                                else:
                                    status_message['stderr'] = routine['stderr'][0]
                            
                            if 'start_time' in routine:
                                status_message['run_time'] = time.time() - routine['start_time']
                                status_message['finish_time'] = pd.Timestamp.utcnow()

                        else:
                            nfinished+=1
                            status_message['status']='COMPLETED'
                            if 'start_time' in routine:
                                status_message['run_time'] = time.time() - routine['start_time']
                                status_message['finish_time'] = pd.Timestamp.utcnow()

                        ClientAPI.post_workerpool(status_message)

                is_running = routine['process'].is_running()
            except:
                pass
            if not is_running:
                remove_routine = True

        elif 'thread' in routine and not routine['thread'].is_alive():
            remove_routine = True

        if not remove_routine:
            new_routines.append(routine)
    
    return new_routines, nfinished, nerror

def reset_program(reset_nginx=False):
    """
    Restarts the current Python program by terminating all child processes and re-executing the script.
    
    This function performs the following steps:
    1. Logs the restart attempt.
    2. Retrieves the current process and kills all its child processes recursively.
    3. Handles and logs any exceptions that occur during child process termination.
    4. Replaces the current process with a new instance of the Python interpreter running the same script with the original arguments.
    
    Note:
    - Requires the `psutil`, `os`, `sys`, and `Logger` modules to be imported and available.
    - Ensures cleanup of file descriptors and other resources by restarting the program cleanly.
    """
    Logger.log.info('restarting worker...')
    try:
        p = psutil.Process(os.getpid())
        children = p.children(recursive=True)
        for child in children:
            child.kill()

    except Exception as e:
        Logger.log.error('restarting worker ERROR!')
        Logger.log.error(e)

    if reset_nginx:
        
        Logger.log.info('restarting nginx...')
        # Kill any existing/zombie nginx - don't wait
        subprocess.Popen(['pkill', '-9', 'nginx'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        
        
        time.sleep(0.5)  # Brief pause to let processes die
        
        # Start nginx as daemon (non-blocking)
        result = subprocess.Popen(['nginx'], 
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        Logger.log.info(f'nginx started with pid {result.pid}')

    python = sys.executable
    os.execl(python, python, *sys.argv)

def read_stdout(stdout, print_to_console=False, routine=None):
    """
    Reads lines from a given stdout stream until it is exhausted.
    
    Parameters:
        stdout (file-like object): The standard output stream to read from.
        print_to_console (bool, optional): If True, prints each line to the console immediately. Defaults to False.
        routine (dict, optional): A dictionary to store the output lines under the key 'stdout'. If provided, each line read will be appended to routine['stdout'].
    
    Behavior:
        - Continuously reads lines from stdout.
        - If a line is read and 'routine' is provided, appends the line to routine['stdout'].
        - If print_to_console is True, prints the line to the console with flushing.
        - Otherwise, logs the line at debug level after stripping newline characters, ignoring empty lines.
        - Stops reading when no more lines are available.
        - Logs any exceptions encountered during reading as errors.
    """
    try:
        while True:            
            out = stdout.readline()
            if out:
                if routine is not None:
                    if 'stdout' not in routine:
                        routine['stdout'] = [] 
                    elif isinstance(routine['stdout'], str):
                        routine['stdout'] = routine['stdout'].split('\n')
                    routine['stdout'].append(out)
                    
                if print_to_console:
                   print(out, flush=True)
                else:
                    out = out.replace('\n', '')
                    if (out != ''):
                        Logger.log.debug('<-' + out)
            else:
                break
    except Exception as e:
        Logger.log.error(f"read_stdout: {str(e)}")

def read_stderr(stderr, print_to_console=False, routine=None):
    """
    Reads lines from a stderr stream, optionally printing them to the console or logging them with different severity levels.
    
    Parameters:
        stderr (file-like object): The standard error stream to read from.
        print_to_console (bool): If True, prints each line read from stderr directly to the console. Defaults to False.
        routine (dict or None): Optional dictionary to store stderr lines under the 'stderr' key.
    
    Behavior:
        - Continuously reads lines from the stderr stream until no more lines are available.
        - If a 'routine' dictionary is provided, appends each line read to the 'stderr' list within it.
        - If print_to_console is False, logs each line using the Logger with severity based on keywords in the line:
            - 'INFO' -> info level
            - 'WARNING' -> warning level
            - 'ERROR' -> error level
            - 'CRITICAL' -> critical level
            - Otherwise, logs as debug.
        - Handles exceptions by logging an error message.
    """
    try:
        while True:
            err = stderr.readline()
            if err:
                if routine is not None:
                    if 'stderr' not in routine:
                        routine['stderr'] = []   
                    elif isinstance(routine['stderr'], str):
                        routine['stderr'] = routine['stderr'].split('\n')
                    routine['stderr'].append(err)

                if print_to_console:
                    print(err, flush=True)
                else:
                    err = err.replace('\n', '')
                    if (err != ''):
                        if ('INFO' in err):
                            Logger.log.info('<-'+err)
                        elif ('WARNING' in err):
                            Logger.log.warning('<-'+err)
                        elif ('ERROR' in err):
                            Logger.log.error('<-'+err)
                        elif ('CRITICAL' in err):
                            Logger.log.critical('<-'+err)
                        else:
                            Logger.log.debug('<-'+err)                            
            else:
                break
    except Exception as e:
        Logger.log.error(f"read_stderr: {str(e)}")

def send_command(command, env=None, blocking=True):
    """
    Execute a shell command with optional environment variables and control over blocking behavior.
    
    Parameters:
        command (str or list/tuple of str): The command to execute. If a list or tuple, it will be joined into a single string.
        env (dict, optional): A dictionary of environment variables to set for the command execution. Defaults to None.
        blocking (bool, optional): If True, wait for the command to complete before returning. If False, return immediately. Defaults to True.
    
    Returns:
        bool: True if the command executed successfully (return code 0), False otherwise.
    
    This function logs the command execution process, starts separate threads to read stdout and stderr asynchronously,
    and handles environment variables if provided.
    """
    if isinstance(command, (list, tuple)):
        _command = ' '.join(command)
    else:
        _command = command
    
    Logger.log.debug('->%s' % _command)
    
    if env is None:
        process = subprocess.Popen(_command,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   universal_newlines=True, shell=True)
    else:
        process = subprocess.Popen(_command,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   universal_newlines=True, shell=True, env=env)

    stdout_thread = threading.Thread(
        target=read_stdout, args=([process.stdout]))
    stderr_thread = threading.Thread(
        target=read_stderr, args=([process.stderr]))
    stdout_thread.start()
    stderr_thread.start()

    if blocking:
        process.wait()  # block until process terminated
        stdout_thread.join()
        stderr_thread.join()
        rc = process.returncode
        success = rc == 0
    else:
        success = True
        
    if success:
        Logger.log.debug('DONE!->%s' % (_command))
        return True
    else:
        Logger.log.error('ERROR!->%s' % (_command))
        return False

def list_process():
    """
    Iterate over all running processes and return a dictionary of processes whose command line's first argument contains the path specified by the 'SOURCE_FOLDER' environment variable.
    
    Returns:
        dict: A dictionary where keys are process IDs (pids) and values are dictionaries containing:
            - 'proc': the psutil.Process object
            - 'pinfo': a dictionary of process information obtained via proc.as_dict()
    
    Notes:
        - Processes that raise NoSuchProcess, AccessDenied, or ZombieProcess exceptions during info retrieval are ignored.
        - The function relies on the 'SOURCE_FOLDER' environment variable being set to a valid path.
    """
    source_path = Path(os.environ['SOURCE_FOLDER'])
    procdict = {}
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=None)
            if len(pinfo['cmdline']) > 0:
                if str(source_path) in pinfo['cmdline'][0]:
                    procdict[proc.pid] = {'proc': proc, 'pinfo': pinfo}
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return procdict

def get_env(command):
    """
    Constructs environment-related paths and variables based on the given command dictionary.
    
    Parameters:
        command (dict): A dictionary containing keys 'repo' and optionally 'branch'.
            - 'repo' (str): The repository name.
            - 'branch' (str, optional): The branch name within the repository.
    
    Returns:
        tuple:
            hasbranch (bool): True if a non-empty 'branch' is specified in the command, else False.
            requirements_path (Path): Path to the 'requirements.txt' file inside the repository.
            repo_path (Path): Path to the repository directory, constructed based on environment variables and command.
            python_path (Path): Path to the Python executable inside the virtual environment of the repository.
            env (dict): A copy of the current environment variables updated with virtual environment settings.
    
    Notes:
        - The base source folder is obtained from the environment variable 'SOURCE_FOLDER'.
        - If 'repo' is 'SharedData', the repo_path is set directly to SOURCE_FOLDER.
        - If a branch is specified, the repo_path includes the branch name appended with a '#' separator.
        - The function sets environment variables to activate the virtual environment located in the repo_path.
        - Adjusts paths and executable names based on the operating
    """
    hasbranch = False
    if 'branch' in command:
        if command['branch'] != '':
            hasbranch = True

    if command['repo'] == 'SharedData':
        repo_path = Path(os.environ['SOURCE_FOLDER'])
    elif hasbranch:
        repo_path = Path(os.environ['SOURCE_FOLDER']) / \
            (command['repo']+'#'+command['branch'])
    else:
        repo_path = Path(os.environ['SOURCE_FOLDER'])/command['repo']

    requirements_path = repo_path/'requirements.txt'
    if os.name == 'posix':
        python_path = repo_path/'venv/bin/python'
    else:
        python_path = repo_path/'venv/Scripts/python.exe'

    env = os.environ.copy()
    env['VIRTUAL_ENV'] = str(repo_path/'venv')
    env['PATH'] = str(repo_path/'venv')+';' + \
        str(python_path.parents[0])+';'+env['PATH']
    env['PYTHONPATH'] = str(repo_path/'venv')+';'+str(python_path.parents[0])
    env['GIT_TERMINAL_PROMPT'] = "0"

    return hasbranch, requirements_path, repo_path, python_path, env

def start_server(port, nproc, nthreads):
    # run API server
    """
    Starts an API server by constructing and executing a command with the specified port, number of processes, and thread count.
    
    Parameters:
        port (int): The port number on which the server will listen.
        nproc (int): The number of processes the server should use.
        nthreads (int): The number of threads the server should use.
    
    This function builds a command dictionary containing server configuration details, records the start time,
    and initiates the server routine by calling `run_routine` with the command and routine information.
    """
    command = {
        "sender": "MASTER",
        "target": os.environ['USER_COMPUTER'],
        "job": "routine",
        "repo": "SharedData",
        "routine": "API.ServerGunicorn",
        "args": f"--port {port} --nproc {nproc} --nthreads {nthreads}"
    }
    start_time = time.time()
    routine = {
        'command': command,
        'thread': None,
        'process': None,
        'subprocess': None,
        'start_time': start_time,
    }
    run_routine(command, routine, quiet=True)

def start_schedules(schedule_names):    
    # run scheduler
    """
    Starts scheduler routines based on the provided schedule names.
    
    Constructs a command dictionary with necessary parameters and initiates the scheduler routine by calling `run_routine`. The routine's metadata, including start time and placeholders for threading and processing, is also prepared.
    
    Args:
        schedule_names (list): A list of schedule names to be passed as arguments to the scheduler routine.
    """
    command = {
        "sender": "MASTER",
        "target": os.environ['USER_COMPUTER'],
        "job": "routine",
        "repo": "SharedData",
        "routine": "Routines.Scheduler",
        "args": schedule_names,
    }
    start_time = time.time()
    routine = {
        'command': command,
        'thread': None,
        'process': None,
        'subprocess': None,
        'start_time': start_time,
    }
    run_routine(command, routine)

def isrunning(command,routines):
    """
    Check if a specified command is currently running within a list of routines.
    
    Parameters:
        command (str): The command to check for.
        routines (list): A list of routines, where each routine is a dictionary containing at least a 'command' key.
    
    Returns:
        bool: True if the command is found running in any of the routines, False otherwise.
    """
    isrunning = False
    
    for routine in routines:
        if compare_routines(routine['command'], command):
            isrunning = True
            break

    return isrunning

def get_cpu_model() -> str:
    """
    Retrieve a human-readable CPU model name in a cross-platform manner.
    
    Attempts to read the CPU model string from system-specific sources:
    - On Linux, reads from /proc/cpuinfo.
    - On macOS, uses the 'sysctl' command.
    - On other platforms (including Windows), uses the platform module.
    
    Returns:
        str: The CPU model name if detected, otherwise "UnknownCPU".
    """
    try:
        if sys.platform == "linux":
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        return line.strip().split(":", 1)[1].strip()
        elif sys.platform == "darwin":  # macOS
            import subprocess
            model = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"])
            return model.decode().strip()
        else:  # Windows or fallback
            return platform.processor() or platform.uname().processor
    except Exception:
        return "UnknownCPU"