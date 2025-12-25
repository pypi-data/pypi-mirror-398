import numpy as np
import sys
import lz4.frame

import pandas as pd
import os
import threading
import json
import requests
import lz4
import bson
import hashlib
import pymongo
import time
from pymongo import ASCENDING, DESCENDING

from SharedData.IO.MongoDBClient import MongoDBClient
from SharedData.Logger import Logger
from SharedData.IO.ClientAPI import ClientAPI
from SharedData.CollectionMongoDB import CollectionMongoDB
from SharedData.Utils import get_hash


class WorkerPool:

    """
    Manages a pool of worker jobs with support for job creation, reservation, and status updates.
    
    This class interfaces with MongoDB collections to coordinate job distribution and processing among workers. It supports atomic fetching and reservation of jobs, broadcasting jobs to multiple workers, and periodic status updates based on job dependencies and due dates.
    
    Key functionalities include:
    - Creating necessary MongoDB indexes for efficient querying.
    - Fetching and reserving direct and broadcast jobs for specific workers.
    - Fetching a batch of pending jobs filtered by user and computer identifiers.
    - Periodically updating job statuses from 'NEW' or 'WAITING' to 'PENDING' when due and dependencies are met.
    - Retrieving CPU model information in a cross-platform manner.
    
    All database operations are designed to be atomic to prevent job duplication or conflicts among workers.
    """
    
    @staticmethod
    def get_command_table(shdata):        
        return shdata.table(
            'Hashs','D1','WORKERPOOL','COMMANDS',
            user='master',
            names = ['hash'],formats=['|S64'],
            is_schemaless=True, size=1e4,
        )
    
    @staticmethod
    def get_job_table(shdata):
        return shdata.table(
            'Hashs','D1','WORKERPOOL','JOBS',
            user='master',
            names = ['hash','status'],formats=['|S64','|S16'],
            is_schemaless=True, size=1e6,
        )
    
    @staticmethod
    def post_commands(shdata, commands):
        tnow = pd.Timestamp.utcnow().tz_localize(None)
        errmsg = ''
        try:
            cmd_table = WorkerPool.get_command_table(shdata)
            cmd_table.acquire()
                            
            for cmd in commands:

                if not 'sender' in cmd:
                    continue
                if not 'target' in cmd:
                    continue
                if not 'job' in cmd:
                    continue
                if cmd['job'] == 'batch':
                    continue
                if not 'date' in cmd:
                    cmd['date'] = tnow
                cmd['mtime'] = tnow
                cmd['target'] = str(cmd['target']).upper()
                cmd['hash'] = get_hash(cmd)
                            
                # find worker                    
                buff = np.full((1,),dtype=cmd_table.dtype,fill_value=np.nan)
                buff['hash'][0] = cmd['target']
                loc = cmd_table.get_loc(buff, acquire=False)
                if loc[0] != -1:
                    worker = cmd_table.get_dict_list(cmd_table[loc[0]],acquire=False)[0]
                else:
                    worker = {
                        'hash': cmd['target'],
                        'commands': {},
                    }
                if isinstance(worker['commands'], list):
                    worker['commands'] = {}
                worker['commands'][cmd['hash']] = cmd
                
            
            # remove old commands
            worker['commands'] = {
                cmd_hash: cmd for cmd_hash, cmd in worker['commands'].items()
                if tnow - cmd['date'] <= pd.Timedelta(seconds=60)
            }

            cmd_table.upsert(worker, acquire=False)

        except Exception as e:
            errmsg = f'Error in post_workerpool: {str(e)}'        
        finally:
            cmd_table.release()
            if errmsg != '':
                Logger.log.error(errmsg)
                raise Exception(errmsg)

    @staticmethod
    def get_commands(shdata, workername):
        """
        Atomically fetch and reserve pending jobs for the specified worker.
        
        This method retrieves commands from the database that are not older than 60 seconds and processes them as follows:
        - Direct jobs targeted specifically at the worker (with status "NEW" and target equal to the worker's name) are marked as "SENT" to indicate they have been reserved.
        - Broadcast jobs (with status "BROADCAST" and target "ALL") are updated to include the worker in their 'fetched' list to prevent the same job from being delivered multiple times to the same worker.
        
        Parameters
        ----------
        workername : str
            Case-insensitive identifier of the requesting worker.
        
        Returns
        -------
        list of dict
            A list of job documents that have been reserved for the worker.
        """
        jobs = []
        errmsg = ''
        workername = workername.upper()
        tnow = pd.Timestamp.utcnow().tz_localize(None)
        try:
            cmd_table = WorkerPool.get_command_table(shdata)
            cmd_table.acquire()
            
            #direct commands
            buff = np.full((1,),dtype=cmd_table.dtype,fill_value=np.nan)
            buff['hash'][0] = workername
            loc = cmd_table.get_loc(buff, acquire=False)
            if loc[0] != -1:
                worker = cmd_table.get_dict_list(cmd_table[loc[0]], acquire=False)[0]
            else:
                worker = {
                    'hash': workername,
                    'commands': {},
                }
            
            if isinstance(worker['commands'], list):
                worker['commands'] = {}

            for cmd in worker['commands'].values():
                if tnow - cmd['date'] < pd.Timedelta(seconds=60):
                    jobs.append(cmd)                                
            worker['commands'] = {} # clear direct commands after fetching            
            cmd_table.upsert(worker, acquire=False)
            
            #broadcast commands
            buff = np.full((1,),dtype=cmd_table.dtype,fill_value=np.nan)
            buff['hash'][0] = 'ALL'
            loc = cmd_table.get_loc(buff, acquire=False)
            if loc[0] != -1:
                broadcast = cmd_table.get_dict_list(cmd_table[loc[0]], acquire=False)[0]
            else:
                broadcast = {
                    'hash': 'ALL',
                    'commands': {},
                }
            
            if isinstance(broadcast['commands'], list):
                broadcast['commands'] = {}
            
            cmd_to_remove = []
            for cmd in broadcast['commands'].values():
                if tnow - cmd['date'] < pd.Timedelta(seconds=60):
                    if not 'fetched_by' in cmd:
                        cmd['fetched_by'] = []
                    if not workername in cmd['fetched_by']:
                        cmd['fetched_by'].append(workername)
                        
                        _cmd = cmd.copy()
                        del _cmd['fetched_by']
                        jobs.append(_cmd)
                        
                else:
                    cmd_to_remove.append(cmd['hash'])
            
            for cmd_hash in cmd_to_remove:
                del broadcast['commands'][cmd_hash]

            cmd_table.upsert(broadcast, acquire=False)

        except Exception as e:
            errmsg = f'Error in get_commands: {str(e)}'
        finally:
            cmd_table.release()
            if errmsg != '':
                Logger.log.error(errmsg)
                raise Exception(errmsg)
            

        return jobs
           
    @staticmethod
    def post_batch_jobs(shdata, batch_jobs):
        """
        Posts a batch of jobs to the worker pool, updating existing jobs or inserting new ones as necessary.
        Jobs status sequence: NEW -> WAITING -> PENDING -> FETCHED -> RUNNING -> COMPLETED / ERROR
        """

        tnow = pd.Timestamp.utcnow().tz_localize(None)
        errmsg = ''
        try:
            job_table = WorkerPool.get_job_table(shdata)
            job_table.acquire()

            # keep track of active jobs
            buff = np.full((1,),dtype=job_table.dtype,fill_value=np.nan)
            buff['hash'][0] = 'ACTIVE_JOBS'
            loc = job_table.get_loc(buff, acquire=False)
            if loc[0] != -1:
                active_jobs = job_table.get_dict_list(job_table[loc[0]],acquire=False)[0]
            else:
                active_jobs = {
                    'hash': 'ACTIVE_JOBS',
                    'status': 'ACTIVE',
                    'jobs': {},
                }
            
            # process each job
            for job in batch_jobs:
                
                if not 'job' in job:
                    continue
                
                if 'hash' in job:
                    buff = np.full((1,),dtype=job_table.dtype,fill_value=np.nan)
                    buff['hash'][0] = job['hash']
                    loc = job_table.get_loc(buff, acquire=False)
                    if loc[0] != -1:
                        existing_job = job_table.get_dict_list(job_table[loc[0]],acquire=False)[0]
                        existing_job.update(job)
                        job = existing_job
                    else:
                        continue
                    
                else: # not 'hash' in job
                    if not 'command' in job:
                        continue
                    else:
                        if not 'repo' in job['command']:
                            continue
                        if not 'branch' in job['command']:
                            continue
                        if not 'routine' in job['command']:
                            continue
                    job['hash'] = get_hash(job['command'])
                
                if not 'status' in job:
                    job['status'] = 'NEW'
                else:
                    job['status'] = str(job['status']).upper()

                if not 'computer' in job:
                    job['computer'] = 'ANY'
                else:
                    job['computer'] = str(job['computer']).upper()

                if not 'user' in job:
                    job['user'] = 'ANY'
                else:
                    job['user'] = str(job['user']).upper()

                if not 'mtime' in job:
                    job['mtime'] = tnow

                if not 'dependencies' in job:
                    job['dependencies'] = []

                if not 'date' in job:
                    job['date'] = tnow

                job_table.upsert(job, acquire=False)
                
                if job['status'] in ['NEW', 'PENDING', 'WAITING', 'FETCHED', 'RUNNING']:
                    if job['hash'] not in active_jobs['jobs']:
                        active_jobs['jobs'][job['hash']] = job
                    else:
                        active_jobs['jobs'][job['hash']].update(job)
                elif job['status'] in ['COMPLETED','ERROR']:
                    if job['hash'] in active_jobs['jobs']:
                        del active_jobs['jobs'][job['hash']]
                else:
                    Logger.log.warning(f"Unknown job status: {job['status']} for job {job['hash']}")
            
            job_table.upsert(active_jobs, acquire=False)

        except Exception as e:
            errmsg = f'Error in post_batch_jobs: {str(e)}'        
        finally:            
            job_table.release()            
            if errmsg != '':
                Logger.log.error(errmsg)
                raise Exception(errmsg)

    @staticmethod
    def fetch_batch_jobs(shdata, workername, njobs=1):
        """
        Fetches and atomically reserves pending jobs for a worker.
        Matches fetch_jobs_mongodb: only fetches jobs already in PENDING status.
        Status transitions (NEW→PENDING) are handled by update_jobs_status_table().
        """
        if njobs < 1:
            return []
        
        user = str(workername.split('@')[0]).upper()
        computer = str(workername.split('@')[1]).upper()
        tnow = pd.Timestamp.utcnow().tz_localize(None)
        errmsg = ''
        fetched_jobs = []
        
        try:
            job_table = WorkerPool.get_job_table(shdata)
            job_table.acquire()

            # Get active jobs cache
            buff = np.full((1,), dtype=job_table.dtype, fill_value=np.nan)
            buff['hash'][0] = 'ACTIVE_JOBS'
            loc = job_table.get_loc(buff, acquire=False)
            
            if loc[0] != -1:
                active_jobs = job_table.get_dict_list(job_table[loc[0]], acquire=False)[0]
            else:                
                return []
            
            # Filter for PENDING jobs matching worker criteria
            # Do NOT change status here - that's update_active_jobs's job
            pending_jobs = []
            for job_hash, job in active_jobs['jobs'].items():
                # Match user/computer (case-insensitive via .upper())
                if not ((job['user'] in [user, 'ANY']) and (job['computer'] in [computer, 'ANY'])):
                    continue
                
                # Only fetch jobs already in PENDING status (matches fetch_jobs_mongodb)
                if job['status'] != 'PENDING':
                    continue                
                
                pending_jobs.append(job)
            
            if not pending_jobs:
                return []

            # Sort by date descending (newest first, matching MongoDB DESCENDING)
            pending_jobs.sort(key=lambda x: x['date'], reverse=True)

            # Atomically fetch requested number of jobs
            for job in pending_jobs[:njobs]:
                job['status'] = 'FETCHED'
                job['target'] = f"{user}@{computer}"
                job['mtime'] = tnow
                
                # Update individual job record in table
                job_table.upsert(job, acquire=False)
                
                # Update in-memory cache
                active_jobs['jobs'][job['hash']] = job
                
                fetched_jobs.append(job)
            
            # Save updated active_jobs cache (critical - was missing before!)
            if fetched_jobs:
                job_table.upsert(active_jobs, acquire=False)

        except Exception as e:
            errmsg = f'Error in fetch_batch_jobs: {str(e)}'
        finally:
            # Always attempt to release (safe even if already released)            
            job_table.release()            
            if errmsg:
                Logger.log.error(errmsg)
                raise Exception(errmsg)

        return fetched_jobs

    @staticmethod
    def update_active_jobs(shdata) -> None:
        """
        Table-based equivalent of update_jobs_status (MongoDB version).
        Runs periodically (every 5 seconds) in background thread to:
        1. Update NEW/WAITING → PENDING when due date passed and dependencies completed
        2. Mark FETCHED/RUNNING → ERROR after 1 hour timeout
        
        Usage:
            import threading
            shdata = SharedData(__file__, user='master')
            threading.Thread(
                target=WorkerPool.update_active_jobs,
                args=(shdata,),
                daemon=True
            ).start()
        """
        try:
            while True:
                try:
                    isacquired = False
                    tnow = pd.Timestamp.utcnow().tz_localize(None)
                    one_hour_ago = tnow - pd.Timedelta(hours=1)
                    
                    job_table = WorkerPool.get_job_table(shdata)                    
                    job_table.acquire()
                    isacquired = True

                    # Get active jobs cache
                    buff = np.full((1,), dtype=job_table.dtype, fill_value=np.nan)
                    buff['hash'][0] = 'ACTIVE_JOBS'
                    loc = job_table.get_loc(buff, acquire=False)
                    if loc[0] == -1:
                        return  # No active jobs
                        
                    
                    active_jobs = job_table.get_dict_list(job_table[loc[0]], acquire=False)[0]
                    modified = False
                    timeout_count = 0
                    pending_count = 0
                    
                    # Process each active job
                    for job_hash, job in list(active_jobs['jobs'].items()):
                        # 1. Check timeout for FETCHED/RUNNING jobs (matches MongoDB behavior)
                        if job['status'] in ['FETCHED', 'RUNNING'] and job['mtime'] < one_hour_ago:
                            job['status'] = 'ERROR'
                            job['stderr'] = 'timeout'
                            job['mtime'] = tnow
                            job_table.upsert(job, acquire=False)
                            active_jobs['jobs'][job_hash] = job
                            modified = True
                            timeout_count += 1
                            continue
                        
                        # 2. Update NEW/WAITING → PENDING if due and dependencies met
                        if job['status'] not in ['NEW', 'WAITING']:
                            continue
                        
                        # Check if job is due
                        if job['date'] > tnow:
                            continue
                        
                        # Check dependencies
                        all_deps_completed = True
                        if job.get('dependencies'):
                            ndep = len(job['dependencies'])
                            buff = np.full((ndep,), dtype=job_table.dtype, fill_value=np.nan)
                            
                            for i, dep_hash in enumerate(job['dependencies']):
                                buff['hash'][i] = dep_hash
                            
                            locs = job_table.get_loc(buff, acquire=False)
                            
                            for i in range(ndep):
                                if locs[i] != -1:
                                    dep_job = job_table.get_dict_list(job_table[locs[i]], acquire=False)[0]
                                    if dep_job['status'] != 'COMPLETED':
                                        all_deps_completed = False
                                        break
                                else:
                                    # Dependency not found - cannot proceed
                                    all_deps_completed = False
                                    break
                        
                        # Update to PENDING if all conditions met
                        if all_deps_completed:
                            job['status'] = 'PENDING'
                            job['mtime'] = tnow
                            job_table.upsert(job, acquire=False)
                            active_jobs['jobs'][job_hash] = job
                            modified = True
                            pending_count += 1
                    
                    # Save updated active_jobs cache if modified
                    if modified:
                        job_table.upsert(active_jobs, acquire=False)
                    
                    # Log warnings (matches MongoDB logging behavior)
                    if timeout_count > 0:
                        Logger.log.warning(f"Marked {timeout_count} jobs as ERROR due to timeout (>1 hour)")

                except Exception as e:
                    try:
                        Logger.log.error(f"Error in update_active_jobs: {e}")
                    except:
                        pass
                    time.sleep(60)  # Wait before retrying on error
                finally:      
                    if isacquired:          
                        job_table.release()
                    
                time.sleep(15)  # Update every 15 seconds 
                
        except Exception as e:
            Logger.log.critical(f"Critical error in update_active_jobs: {e}")
            time.sleep(60)
        