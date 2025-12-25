# SharedData/Routines/Worker.py

# implements a decentralized routines worker
# connects to worker pool
# broadcast heartbeat
# listen to commands
# environment variables:
# SOURCE_FOLDER
# WORKERPOOL_STREAM
# GIT_SERVER
# GIT_USER
# GIT_ACRONYM
# GIT_TOKEN

import os
import time
import sys
import numpy as np
import importlib.metadata
import argparse
import psutil

# Note: ~/.shareddata.env is loaded automatically by Defaults.py via load_dotenv()
# when SharedData modules are imported below

from SharedData.Routines.WorkerLib import *
from SharedData.SharedData import SharedData
shdata = SharedData('SharedData.Routines.Worker',quiet=True)
from SharedData.Logger import Logger
from SharedData.Routines.WorkerPool import WorkerPool
from SharedData.Users import get_master_user

parser = argparse.ArgumentParser(description="Worker configuration")
parser.add_argument('--schedules', default='', help='Schedules to start')
parser.add_argument('--server', type=bool, default=False, help='Server port number')
parser.add_argument('--port', type=int, default=8002, help='Server port number')
parser.add_argument('--nproc', type=int, default=4, help='Number of server processes')
parser.add_argument('--nthreads', type=int, default=8, help='Number of server threads')
parser.add_argument('--batchjobs', type=int, default=0, help='Max number of jobs to fetch')
parser.add_argument('--sleep', type=int, default=5, help='Sleep time between fetches')
args = parser.parse_args()

if args.server:
    # INITIALIZE WORKER POOL SERVER COMMAND AND JOBS TABLE
    cmd_table = WorkerPool.get_command_table(shdata)
    jobs_table = WorkerPool.get_job_table(shdata)
    # SET ENVIRONMENT VARIABLE FOR THE SERVER TO CONNECT TO THE WORKERPOOL
    os.environ['SHAREDDATA_ENDPOINT'] = f'http://localhost:{args.port}'
    # CHECK IF THE MASTER USER IS PRESENT
    master_user = get_master_user(shdata)
    # START THE SERVER API
    start_server(args.port, args.nproc,args.nthreads)
    # START THE WORKERPOOL JOBS STATUS UPDATE THREAD
    update_jobs_status_thread = threading.Thread(
        target=WorkerPool.update_active_jobs,
        args=(shdata,),
        daemon=True
    )
    update_jobs_status_thread.start()

os.environ['MAX_BATCH_JOBS'] = str(int(args.batchjobs))
    
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

cpu_model = get_cpu_model()
mem = psutil.virtual_memory()
mem_total_gb = mem.total / (1024 ** 3)

if args.server:
    time.sleep(15)  # wait for server to start

Logger.log.info(
    "ROUTINE STARTED!"
    f"{cpu_model} {mem_total_gb:.1f} RAM"
)

routines = []
batch_jobs = []
completed_batch_jobs = 0
error_batch_jobs = 0

while True:

    jobs = get_workerpool_jobs(batch_jobs)    
    update_routines(routines)
    for command in jobs:           
        if ('job' in command) & ('target' in command):
            if ((command['target'].upper() == os.environ['USER_COMPUTER'].upper())
                    | (command['target'] == 'ALL')):                
                update_routines(routines)
                command = validate_command(command)
                process_command(command,routines,batch_jobs)
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

        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        mem_total_gb = mem.total / (1024 ** 3)        

        Logger.log.debug(
            f"#heartbeat# {SHAREDDATA_VERSION},"
            f"{nroutines}routines,"
            f"{len(batch_jobs)}/{int(os.environ['MAX_BATCH_JOBS'])}jobs,"
            f"{completed_batch_jobs}completed,"
            f"{error_batch_jobs}errors,"
            f"cpu={cpu_percent:.1f}%,"
            f"mem={mem_percent:.1f}%"            
        )
        # Logger.log.debug(f'#heartbeat# {nroutines}routines,{running_batch_jobs}/{MAX_BATCH_JOBS}jobs,{completed_batch_jobs}completed,{error_batch_jobs}errors,{SHAREDDATA_VERSION}')
    
    time.sleep(SLEEP_TIME * np.random.rand())