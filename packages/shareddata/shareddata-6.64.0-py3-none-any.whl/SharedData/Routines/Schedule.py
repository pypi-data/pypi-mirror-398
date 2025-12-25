import json
import os
import glob
import subprocess
import pytz
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
from tzlocal import get_localzone
local_tz = pytz.timezone(str(get_localzone()))
import requests
import lz4
import threading

from SharedData.Logger import Logger
from SharedData.Metadata import Metadata
from SharedData.Metadata import isnan
from SharedData.Routines.WorkerPool import WorkerPool
from SharedData.IO.ClientAPI import ClientAPI

class Schedule:

    """
    Class to manage and execute scheduled routines, handling both batch and realtime jobs.
    
    Attributes:
        schedule_name (str): Name of the schedule to load.
        lastschedule (list): Last saved schedule snapshot.
        schedule (pd.DataFrame): Current schedule with routines and their statuses.
        batch (pd.DataFrame): Subset of schedule for batch (non-realtime) routines.
        realtime (pd.DataFrame): Subset of schedule for realtime routines.
    
    Methods:
        __init__(schedule_name):
            Initializes the Schedule object, loads the schedule data.
    
        load():
            Loads and processes the schedule metadata, resolving runtimes, dependencies,
            and initial statuses, preparing the execution sequence.
    
        update():
            Updates the schedule by refreshing logs and statuses for batch and realtime routines.
    
        UpdateLogs():
            Retrieves and processes log data to update routine statuses and timestamps.
    
        UpdateBatchStatus():
            Updates the status of batch routines based on runtime, completion, errors,
            dependencies, and external flags.
    
        UpdateRealtimeStatus():
            Updates the status of realtime routines based on heartbeat, start, run messages,
            dependencies, and external flags.
    
        run():
            Sends commands to start pending or restarting routines, updating their statuses accordingly.
    
        save():
            Saves
    """
    def __init__(self, schedule_name):
        """
        Initializes the object with a schedule name and prepares data structures for managing the schedule.
        
        Parameters:
            schedule_name (str): The name of the schedule to be used.
        
        Attributes initialized:
            schedule_name (str): Stores the provided schedule name.
            lastschedule (list): List to hold the last schedule data.
            schedule (list): List to hold the current schedule data.
            batch (pd.DataFrame): DataFrame to hold batch data.
            realtime (pd.DataFrame): DataFrame to hold real-time data.
        
        Calls the load() method to initialize or load necessary data.
        """
        self.schedule_name = schedule_name        
        self.lastschedule = []
        self.schedule = []        
        self.batch = pd.DataFrame([])
        self.realtime = pd.DataFrame([])
        
        self.load()

    def load(self):
        
        """
        Load and process the schedule data for the current date, initializing runtime information, dependencies, and statuses.
        
        This method performs the following steps:
        - Retrieves the current date and extracts year, month, and day.
        - Loads the schedule metadata for the specified schedule name.
        - Raises an exception if the schedule is not found.
        - Parses and localizes runtimes for each scheduled routine, defaulting to midnight if no runtimes are specified.
        - Cleans and formats routine paths, computer names, script names, and dependencies.
        - Initializes status-related columns including last message info, run message flags, and real-time indicators.
        - Sorts the schedule by runtimes and routine names.
        - Iteratively updates the status of each routine based on dependencies and runtime conditions:
          - Marks routines as 'WAITING DEPENDENCIES' if dependencies are not yet completed.
          - Marks routines as 'PENDING' if ready to run.
          - Marks expired routines as 'EXPIRED'.
          - Marks completed routines as 'COMPLETED' after processing.
        - Stores the finalized schedule with execution sequence in the instance attribute `self.schedule`.
        
        Raises:
            Exception: If the schedule is not found or if a dependency is missing from the schedule.
        """
        today = datetime.now().date()
        year = today.timetuple()[0]
        month = today.timetuple()[1]
        day = today.timetuple()[2]

        _sched = Metadata('SCHEDULES/'+self.schedule_name).static.reset_index()
        if _sched.empty:
            errmsg = 'Schedule %s not found!' % (self.schedule_name)
            Logger.log.error(errmsg)
            raise Exception(errmsg)
        sched = pd.DataFrame(columns=_sched.columns)
        for i, s in _sched.iterrows():
            if not isnan(s['runtimes']):
                runtimes = s['runtimes'].split(',')
                if len(runtimes) > 1:
                    runtimes = runtimes[0]
                for t in runtimes:
                    hour = int(t.split(':')[0])
                    minute = int(t.split(':')[1])
                    dttm = local_tz.localize(
                        datetime(year, month, day, hour, minute))
                    s['runtimes'] = dttm
                    # sched = sched.reindex(columns=s.index.union(sched.columns))
                    sched = pd.concat([sched, pd.DataFrame(s).T])
            else:
                hour = int(0)
                minute = int(0)
                dttm = local_tz.localize(
                    datetime(year, month, day, hour, minute))
                s['runtimes'] = dttm
                # sched = sched.reindex(columns=s.index.union(sched.columns))
                sched = pd.concat([sched, pd.DataFrame(s).T])

        sched = sched.sort_values(
            by=['runtimes', 'name']).reset_index(drop=True)
        sched['routine'] = [s.replace('\\', '/') for s in sched['routine']]
        sched['computer'] = [s.split(':')[0] for s in sched['routine']]
        sched['script'] = [s.split(':')[-1] for s in sched['routine']]

        sched.loc[sched['dependencies'].isnull(), 'dependencies'] = ''
        sched['dependencies'] = [s.replace('\\', '/')
                                 for s in sched['dependencies']]

        sched['lastmsg'] = 'nan'
        sched['lastmsgts'] = pd.NaT
        sched['lastmsgage'] = np.nan

        sched['runmsgsent'] = False
        sched['runmsgts'] = pd.NaT
        sched['runmsgage'] = np.nan

        if not 'isrealtime' in sched.columns:
            sched['isrealtime'] = False

        sched['status'] = 'nan'
        sched['status'] = sched['status'].astype(str)

        # SAVE ROUTINES SCHEDULE IN EXECUTION SEQUENCE
        uruntimes = sched['runtimes'].unique()
        runtime = uruntimes[0]
        sched_sort = pd.DataFrame(columns=sched.columns)
        for runtime in uruntimes:
            # mark pending routines
            while True:
                idx = runtime.astimezone(tz=local_tz) >= sched['runtimes']
                idx = (idx) & ((sched['status'] == 'nan')
                               | (sched['status'] == 'WAITING DEPENDENCIES'))

                dfpending = sched[idx]
                expiredidx = dfpending.duplicated(['routine'], keep='last')
                if expiredidx.any():
                    expiredids = expiredidx.index[expiredidx]
                    sched.loc[expiredids, 'status'] = 'EXPIRED'
                dfpending = dfpending[~expiredidx]
                i = 0
                for i in dfpending.index:
                    r = dfpending.loc[i]

                    if not isnan(r['dependencies']):
                        run = True
                        sched.loc[i, 'status'] = 'WAITING DEPENDENCIES'
                        dependencies = r['dependencies'].replace(
                            '\n', '').split(',')
                        for dep in dependencies:
                            idx = sched['routine'] == dep
                            idx = (idx) & (
                                sched['runtimes'] <= runtime.astimezone(tz=local_tz))
                            ids = sched.index[idx]
                            if len(ids) == 0:
                                Logger.log.error(
                                    'Dependency not scheduled for '+r['routine'])
                                raise Exception(
                                    'Dependency not scheduled for '+r['routine'])
                            else:
                                if not str(sched.loc[ids[-1], 'status']) == 'COMPLETED':
                                    run = False
                        if run:
                            sched.loc[i, 'status'] = 'PENDING'
                    else:
                        sched.loc[i, 'status'] = 'PENDING'

                idx = sched['status'] == 'PENDING'
                if idx.any():
                    sched_sort = pd.concat([sched_sort, sched[idx]])
                    sched_sort['status'] = 'nan'
                    sched.loc[idx, 'status'] = 'COMPLETED'
                else:
                    break

        sched_sort.index.name = 'sequence'
        self.schedule = sched_sort        
        self.schedule = self.schedule.reset_index(drop=True)

    def update(self):
        """
        Updates the object's logs, batch status, and realtime status, then merges the realtime and batch DataFrames into a single schedule DataFrame with a reset index.
        """
        self.UpdateLogs()
        self.UpdateBatchStatus()
        self.UpdateRealtimeStatus()
        self.schedule = pd.concat([self.realtime,self.batch]).reset_index()

    def UpdateLogs(self):
        """
        Updates the instance's schedule DataFrame with the latest log timestamps and message ages from various Logger log DataFrames.
        
        For each routine in the schedule, this method:
        - Retrieves the most recent entries from Logger's run, started, error, completed, last, and heartbeat log DataFrames.
        - Filters these entries to include only those occurring at or after the scheduled runtimes.
        - Updates the schedule with timestamps of these log events.
        - Calculates the age in seconds of the most recent messages relative to the current local time.
        - Fills missing age values with 1000.0 to indicate absence of recent messages.
        
        The schedule DataFrame must contain a 'routine' column used to match log entries. After processing, the updated schedule replaces the existing one in the instance.
        """
        Logger.getLogs()

        local_tz = pytz.timezone(str(get_localzone()))
        now = datetime.now().astimezone(tz=local_tz)

        dfsched = self.schedule.copy().set_index('routine')

        # RUN TIME        
        if not Logger.dfrun.empty:
            df = Logger.dfrun.copy()
            df['routine'] = df['user_name']+':'+df['logger_name']
            df['asctime'] = pd.to_datetime(df['asctime'])
            df = df.sort_values('asctime')
            df = df.groupby('routine').last()
            idisin = dfsched.index[dfsched.index.isin(df.index)]
            idx = df.loc[idisin,'asctime']>=dfsched.loc[idisin,'runtimes']
            idisin = idisin[idx]
            dfsched.loc[idisin,'runmsgts'] = df.loc[idisin,'asctime']
            dfsched.loc[idisin,'runmsgsent'] = True
            dfsched.loc[idisin,'runmsgage'] = (now - dfsched.loc[idisin,'runmsgts']).apply(lambda x: x.total_seconds())
            dfsched['runmsgage'] = dfsched['runmsgage'].fillna(1000.0)

        # STARTED TIME        
        if not Logger.dfstarted.empty:
            df = Logger.dfstarted.copy()
            df['routine'] = df['user_name']+':'+df['logger_name']
            df['asctime'] = pd.to_datetime(df['asctime'])
            df = df.sort_values('asctime')
            df = df.groupby('routine').last()        
            idisin = dfsched.index[dfsched.index.isin(df.index)]
            idx = df.loc[idisin,'asctime']>=dfsched.loc[idisin,'runtimes']
            idisin = idisin[idx]
            dfsched.loc[idisin,'startedmsgts'] = df.loc[idisin,'asctime']
            dfsched.loc[idisin,'startedmsgage'] = (now - dfsched.loc[idisin,'startedmsgts']).apply(lambda x: x.total_seconds())
            dfsched['startedmsgage'] = dfsched['startedmsgage'].fillna(1000.0)
            
        # ERROR TIME
        if not Logger.dferror.empty:
            df = Logger.dferror.copy()
            df['routine'] = df['user_name']+':'+df['logger_name']
            df['asctime'] = pd.to_datetime(df['asctime'])
            df = df.sort_values('asctime')
            df = df.groupby('routine').last()
            idisin = dfsched.index[dfsched.index.isin(df.index)]
            idx = df.loc[idisin,'asctime']>=dfsched.loc[idisin,'runtimes']
            idisin = idisin[idx]
            dfsched.loc[idisin,'errormsgts'] = df.loc[idisin,'asctime']

        # COMPLETED TIME
        if not Logger.dfcompleted.empty:
            df = Logger.dfcompleted.copy()
            df['routine'] = df['user_name']+':'+df['logger_name']
            df['asctime'] = pd.to_datetime(df['asctime'])
            df = df.sort_values('asctime')
            df = df.groupby('routine').last()
            idisin = dfsched.index[dfsched.index.isin(df.index)]
            idx = df.loc[idisin,'asctime']>=dfsched.loc[idisin,'runtimes']
            idisin = idisin[idx]
            dfsched.loc[idisin,'completedmsgts'] = df.loc[idisin,'asctime']

        # LAST MESSAGE
        if not Logger.dflast.empty:
            df = Logger.dflast.copy().reset_index()
            df['routine'] = df['user_name']+':'+df['logger_name']
            df['asctime'] = pd.to_datetime(df['asctime'])
            df = df.sort_values('asctime')
            df = df.groupby('routine').last()
            idisin = dfsched.index[dfsched.index.isin(df.index)]
            idx = df.loc[idisin,'asctime']>=dfsched.loc[idisin,'runtimes']
            idisin = idisin[idx]
            dfsched.loc[idisin,'lastmsg'] = df.loc[idisin,'message']
            dfsched.loc[idisin,'lastmsgts'] = df.loc[idisin,'asctime']
            dfsched.loc[idisin,'lastmsgage'] = (now - dfsched.loc[idisin,'lastmsgts']).apply(lambda x: x.total_seconds())
            dfsched['lastmsgage'] = dfsched['lastmsgage'].fillna(1000.0)

        # HEARTBEAT TIME
        if not Logger.dfheartbeats.empty:
            df = Logger.dfheartbeats.copy().reset_index()
            df['routine'] = df['user_name']+':'+df['logger_name']
            df['asctime'] = pd.to_datetime(df['asctime'])
            df = df.sort_values('asctime')
            df = df.groupby('routine').last()
            idisin = dfsched.index[dfsched.index.isin(df.index)]            
            dfsched.loc[idisin,'heartbeatmsgts'] = df.loc[idisin,'asctime']
            dfsched.loc[idisin,'heartbeatmsgage'] = (now - dfsched.loc[idisin,'heartbeatmsgts']).apply(lambda x: x.total_seconds())
            dfsched['heartbeatmsgage'] = dfsched['heartbeatmsgage'].fillna(1000.0)

        self.schedule = dfsched.reset_index()

    def UpdateBatchStatus(self):
        """
        Update the status of each non-realtime batch routine in the schedule based on current time, message timestamps, and dependencies.
        
        This method performs a state machine update on the 'schedule' DataFrame's non-realtime entries by:
        - Setting status to 'SCHEDULED' if the runtime is in the future.
        - Marking batches as 'COMPLETED', 'ERROR', 'RUNNING', 'STARTING', or 'DELAYED' based on the presence and recency of various timestamp columns.
        - Identifying 'PENDING' batches whose runtimes have passed but are not yet started, considering dependencies on other batches.
        - Marking batches as 'WAITING DEPENDENCIES' if they are pending but have incomplete dependencies.
        - Appending ' EXTERNAL' to the status of batches marked as external.
        
        The updated batch statuses are stored in the instance attribute 'self.batch'.
        """
        local_tz = pytz.timezone(str(get_localzone()))
        now = datetime.now().astimezone(tz=local_tz)
        batch = self.schedule[self.schedule['isrealtime']==False].set_index('routine')        

        # STATE MACHINE
        scheduledidx = batch['runtimes'] > now
        batch.loc[scheduledidx,'status'] = 'SCHEDULED'

        completedidx = batch['status']=='COMPLETED'
        if 'completedmsgts' in batch.columns:
            completedidx = batch['completedmsgts'].notnull()
            batch.loc[completedidx,'status'] = 'COMPLETED'

        erroridx = batch['status']=='ERROR'
        if 'errormsgts' in batch.columns:
            erroridx = (batch['errormsgts'].notnull()) & (~completedidx)
            batch.loc[erroridx,'status'] = 'ERROR'

        runningidx = batch['status']=='RUNNING'
        if 'startedmsgts' in batch.columns:
            runningidx = (batch['startedmsgts'].notnull()) & (~completedidx) & (~erroridx)
            batch.loc[runningidx,'status'] = 'RUNNING'

        startingidx = batch['status']=='STARTING'
        if 'runmsgts' in batch.columns:
            startingidx = (batch['runmsgts'].notnull()) & (~runningidx) & (~completedidx) & (~erroridx)
            batch.loc[startingidx,'status'] = 'STARTING'

        delayedidx = batch['status']=='DELAYED'
        if ('lastmsgage' in batch.columns) & ((batch['lastmsgage'] != pd.Timestamp(0)).any()):
            delayedidx = startingidx & (batch['lastmsgage']>300)
            batch.loc[delayedidx,'status'] = 'DELAYED'
        
        pendingidx = (batch['runtimes']<=now) & (~startingidx) & (~runningidx) & (~completedidx) & (~erroridx)
        waitingidx = pendingidx.copy()
        waitingidx[:] = False
        # check dependencies
        pendingids = batch.index[pendingidx]
        for pid in pendingids:
            dependencies = batch.loc[pid,'dependencies'].split(',')
            for dep in dependencies:
                if dep in batch.index:
                    if batch.loc[dep,'status'] not in ['COMPLETED']:
                        pendingidx[pid] = False
                        waitingidx[pid] = True
                        break
        if pendingidx.any():
            batch.loc[pendingidx,'status'] = 'PENDING'
        
        if waitingidx.any():
            batch.loc[waitingidx,'status'] = 'WAITING DEPENDENCIES'

        externalidx = batch['isexternal']==True
        externalidx = externalidx & (batch['status'].astype(str)!='nan')
        batch.loc[externalidx,'status'] += ' EXTERNAL'

        self.batch = batch
    
    def UpdateRealtimeStatus(self):       
        """
        Update the real-time status of scheduled routines based on message ages, run times, and dependencies.
        
        This method filters routines marked as real-time from `self.schedule` and evaluates their current status using a state machine logic. It assigns statuses such as:
        - 'RUNNING' if the heartbeat message is recent,
        - 'STARTED' if the start message is recent and precedes the run message,
        - 'STARTING' if the run message is recent but not started or running,
        - 'RESTART' if the routine is scheduled to run but not started or running and dependencies are met,
        - 'WAITING DEPENDENCIES' if dependencies are not currently running.
        
        Routines marked as external have ' EXTERNAL' appended to their status. The updated statuses are stored in `self.realtime`.
        """
        local_tz = pytz.timezone(str(get_localzone()))
        now = datetime.now().astimezone(tz=local_tz) 
        realtime = self.schedule[self.schedule['isrealtime']==True].set_index('routine')

        # STATE MACHINE
        runningidx = pd.Series(False,index=realtime.index)
        if 'heartbeatmsgage' in realtime.columns:
            runningidx = (realtime['heartbeatmsgage']<=45)
            realtime.loc[runningidx,'status'] = 'RUNNING'
        
        startedidx = pd.Series(False,index=realtime.index)
        startingidx = pd.Series(False,index=realtime.index)
        if ('startedmsgage' in realtime.columns) and ('runmsgage' in realtime.columns):
            startedidx = (realtime['startedmsgage'] <= 300) & (realtime['startedmsgage']<realtime['runmsgage']) & (~runningidx)
            realtime.loc[startedidx,'status'] = 'STARTED'
                
            startingidx =  (realtime['runmsgage'] <= 60) & (~startedidx) & (~runningidx)
            realtime.loc[startingidx,'status'] = 'STARTING'

        pendingidx = pd.Series(False,index=realtime.index)
        if 'runtimes' in realtime.columns:
            pendingidx = (realtime['runtimes']<=now) & (~startedidx) & (~startingidx) & (~runningidx)

        waitingidx = pendingidx.copy()
        waitingidx[:] = False
        # check dependencies
        pendingids = realtime.index[pendingidx]
        for pid in pendingids:
            dependencies = realtime.loc[pid,'dependencies'].split(',')
            for dep in dependencies:
                if dep in realtime.index:
                    if realtime.loc[dep,'status'] not in ['RUNNING']:
                        pendingidx[pid] = False
                        waitingidx[pid] = True
                        break
        if pendingidx.any():
            realtime.loc[pendingidx,'status'] = 'RESTART'
        
        if waitingidx.any():
            realtime.loc[waitingidx,'status'] = 'WAITING DEPENDENCIES'

        externalidx = realtime['isexternal']==True
        realtime.loc[externalidx,'status'] += ' EXTERNAL'

        self.realtime = realtime

    def run(self):
        """
        Processes scheduled routines with statuses 'PENDING', 'START', or 'RESTART' by constructing and sending command messages to initiate or restart them.
        
        For each applicable routine, this method extracts details such as the target computer, repository, routine script, optional branch, and arguments. It sends a command message via the client API to the 'command' channel, updates the routine's status to 'STARTING', logs the dispatch time and message, and records the event in the logger. If sending the command fails, an error is logged.
        
        Returns:
            pandas.DataFrame: The updated schedule DataFrame with modified statuses, timestamps, and message flags.
        """
        newcommand = False
        sched = self.schedule

        # Run pending routines
        idx = sched['status'] == 'PENDING'
        idx = (idx) | (sched['status'] == 'START')
        idx = (idx) | (sched['status'] == 'RESTART')
        dfpending = sched[idx]
        for i in dfpending.index:
            r = dfpending.loc[i].copy()
            if (str(r['lastmsg']) == 'nan') | (r['status'] == 'RESTART'):
                newcommand = True
                target = r['computer']

                if 'SharedData' in r['script']:
                    repo = r['script'].split('.')[0]
                    routine = '.'.join(r['script'].split('.')[1:])
                    branch = ''
                else:
                    if '#' in r['script']:  # has branch
                        branch = r['script'].split('/')[0].split('#')[-1]
                        repo = r['script'].split('/')[0].split('#')[0]
                        routine = r['script'].replace(repo, '').\
                            replace('#', '').replace(branch, '')[1:]+'.py'
                    else:
                        branch = ''
                        repo = r['script'].split('/')[0]
                        routine = r['script'].replace(repo, '')[1:]+'.py'

                job = "routine"
                if r['status'] == 'RESTART':
                    job = "restart"

                data = {
                    "sender": "MASTER",
                    "job": job,
                    "target": target,
                    "repo": repo,
                    "routine": routine
                }

                if (branch != '') & (branch != 'nan'):
                    data['branch'] = branch

                if 'args' in r:
                    r['args'] = str(r['args'])
                    if (r['args'] != '') & (r['args'] != 'nan'):
                        data['args'] = r['args']

                try:
                    ClientAPI.post_workerpool(data)
                    sched.loc[r.name, 'status'] = 'STARTING'
                    now = datetime.now().astimezone(tz=local_tz)
                    sched.loc[r.name, 'runmsgsent'] = True
                    sched.loc[r.name, 'runmsgts'] = now
                    sched.loc[r.name, 'lastmsg'] = 'Command to run sent...'
                    sched.loc[r.name, 'lastmsgts'] = now
                    sched.loc[r.name, 'lastmsgage'] = 0
                    Logger.log.info('Command to run %s:%s sent...' %
                                    (target, r['script']))
                except Exception as e:
                    Logger.log.error('Error sending command to run %s:%s on %s: %s' %
                                    (target, r['script'], target, str(e)))

        self.schedule = sched        
        return sched

    def save(self):
        """
        Saves the current schedule if it has changed since the last save.
        
        Checks if `self.schedule` differs from `self.lastschedule`. If so, updates `self.lastschedule` to the current schedule, creates a `Metadata` object for today's date within the schedule's directory, and saves a copy of the schedule there. Before saving, it processes the 'runtimes' column by removing timezone information from datetime entries to ensure consistency.
        
        Assumptions:
        - `self.schedule` and `self.lastschedule` are pandas DataFrames.
        - `self.schedule_name` is a string representing the schedule's name.
        - `Metadata` is a class responsible for handling metadata storage.
        - The 'runtimes' column contains datetime objects or comparable string values.
        """
        if not self.schedule.equals(self.lastschedule):
            self.lastschedule = self.schedule.copy()            
            today = pd.Timestamp(pd.Timestamp.now().date())
            todaystr = today.strftime('%Y%m%d')
            md = Metadata('SCHEDULES/'+self.schedule_name+'/'+todaystr)
            md.static = self.schedule.copy()
            idx = md.static['runtimes'] != 'nan'
            md.static.loc[idx, 'runtimes'] = [d.replace(tzinfo=None) 
                                            for d in md.static['runtimes'][idx]]
            # md.static.loc[idx, 'runtimes'] = [d.tz_localize(
            #     None) for d in md.static['runtimes'][idx]]
            md.save()
