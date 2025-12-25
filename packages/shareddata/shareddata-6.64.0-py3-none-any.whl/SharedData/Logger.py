import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
import glob
import pandas as pd
import numpy as np
from io import StringIO
from filelock import FileLock
from queue import Queue
from bson import ObjectId
import hashlib
import threading

import SharedData.Defaults
from pythonjsonlogger.jsonlogger import JsonFormatter
import boto3
import json
import requests
import lz4

from SharedData.IO.LogHandlerAPI import LogHandlerAPI


class BufferedLogHandler(logging.Handler):
    """Handler that stores logs in a circular buffer for display in dashboards/UIs"""
    def __init__(self, buffer_list, max_size=500):
        super().__init__()
        self.buffer = buffer_list
        self.max_size = max_size
    
    def emit(self, record):
        try:
            from datetime import datetime, timezone
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': self.format(record)
            }
            self.buffer.append(log_entry)
            # Keep only the most recent logs
            if len(self.buffer) > self.max_size:
                self.buffer.pop(0)
        except Exception:
            self.handleError(record)

        
class Logger:

    """
    Logger class for managing and processing application logs.
    
    This class provides static methods and attributes to connect to a logging source,
    read and aggregate logs from current and previous days, handle heartbeat messages,
    and extract status updates from log messages. It supports logging to multiple
    destinations including console, file, API, with configurable log levels.
    
    Attributes:
        log (logging.Logger or None): The main logger instance.
        user (str): Current user name for logging context.
        source (str): Source identifier for the logger.
        last_day_read (bool): Flag indicating if the previous day's logs have been read.
        dflogs (pd.DataFrame): DataFrame holding all aggregated log entries.
        dfstarted (pd.DataFrame): DataFrame holding logs indicating routine start events.
        dfheartbeats (pd.DataFrame): DataFrame holding the latest heartbeat logs per user/logger.
        dfcompleted (pd.DataFrame): DataFrame holding logs indicating routine completion.
        dferror (pd.DataFrame): DataFrame holding logs indicating routine errors.
        dflast (pd.DataFrame): DataFrame holding the most recent log entry per user/logger.
        dfrun (pd.DataFrame): DataFrame holding logs related to command run events.
        logfilepath
    """
    log = None
    log_queue = Queue()
    log_writer_thread = None
    lock = threading.Lock()
    user = 'guest'
    source = 'unknown'
    last_day_read = False
    
    # Log buffer for optional in-memory storage
    log_buffer = []
    buffered_handler = None

    dflogs = pd.DataFrame(
        [],
        columns=['shardid', 'sequence_number', 'user_name',
                  'asctime', 'logger_name', 'level', 'message']
    )
    dfstarted = pd.DataFrame([])
    dfheartbeats = pd.DataFrame([])
    dfcompleted = pd.DataFrame([])
    dferror = pd.DataFrame([])    
    dflast = pd.DataFrame([])
    dfrun = pd.DataFrame([])

    logfilepath = Path('')
    _logfileposition=0
    _sorted_until = 0
    _max_asctime =  pd.Timestamp('1970-01-01 00:00:00',tz='UTC')


    @staticmethod
    def connect(source, user=None, buffer_logs=False, buffer_max_size=500):
        """
        '''
        Initializes and configures the Logger instance for a specified source module.
        
        This static method sets up the logging environment by normalizing the source path,
        determining the logging level from environment variables, and attaching multiple
        handlers based on configuration flags. Supported handlers include console output,
        API logging, file logging.
        
        Parameters:
            source (str): The file path or module name to be used as the logger's source identifier.
            user (str, optional): An optional user identifier to associate with the logger.
            buffer_logs (bool, optional): If True, enables in-memory log buffering for dashboard/UI display. Defaults to False.
            buffer_max_size (int, optional): Maximum number of log entries to keep in the buffer. Defaults to 500.
        
        Behavior:
        - Normalizes the source path by removing common base paths and formatting it.
        - Sets the logging level to DEBUG if the environment variable LOG_LEVEL is 'DEBUG', otherwise INFO.
        - Creates a logger with the normalized source name.
        - Adds a stream handler for console logging.
        - Optionally adds handlers for API logging and file logging based on environment variables.
        - If buffer_logs is True, adds a BufferedLogHandler to store logs in memory.
        - Uses custom formatters that include user computer information and timestamps.
        
        Environment Variables Used:
        - SOURCE_FOLDER, USERPROFILE: Used for path normalization.
        - LOG_LEVEL: Determines logging verbosity ('DEBUG' or other).
        - USER_COMPUTER: Included in log message formatting.
        - LOG_API: Enables API logging if set to 'TRUE'.
        - LOG_FILE:
        """
        if Logger.log is None:
            if 'SOURCE_FOLDER' in os.environ:
                try:
                    commonpath = os.path.commonpath(
                        [source, os.environ['SOURCE_FOLDER']])
                    source = source.replace(commonpath, '')
                except:
                    pass
            elif 'USERPROFILE' in os.environ:
                try:
                    commonpath = os.path.commonpath(
                        [source, os.environ['USERPROFILE']])
                    source = source.replace(commonpath, '')
                except:
                    pass

            finds = 'site-packages'
            if finds in source:
                cutid = source.find(finds) + len(finds) + 1
                source = source[cutid:]                        
            source = source.replace('\\','/')
            source = source.lstrip('/')
            source = source.replace('.py', '')
            Logger.source = source

            if not user is None:
                Logger.user = user
            
            loglevel = logging.INFO
            if 'LOG_LEVEL' in os.environ:
                if os.environ['LOG_LEVEL'] == 'DEBUG':
                    loglevel = logging.DEBUG                
                
            # Create Logger
            Logger.log = logging.getLogger(source)
            Logger.log.setLevel(logging.DEBUG)
            # formatter = logging.Formatter(os.environ['USER_COMPUTER'] +
            #                               ';%(asctime)s;%(name)s;%(levelname)s;%(message)s',
            #                               datefmt='%Y-%m-%dT%H:%M:%S%z')
            formatter = logging.Formatter(os.environ['USER_COMPUTER'] +
                                          ';%(asctime)s;%(name)s;%(levelname)s;%(message)s',
                                          datefmt='%H:%M:%S')
            # log screen
            handler = logging.StreamHandler()
            handler.setLevel(loglevel)
            handler.setFormatter(formatter)
            Logger.log.addHandler(handler)

            # log to API (only if SHAREDDATA_ENDPOINT and TOKEN are available)
            if str(os.environ['LOG_API']).upper()=='TRUE':
                Logger.add_api_handler_if_configured()

            # log to file
            if str(os.environ['LOG_FILE']).upper()=='TRUE':
                path = Path(os.environ['DATABASE_FOLDER'])
                path = path / 'Logs'
                path = path / datetime.now().strftime('%Y%m%d')
                path = path / (os.environ['USERNAME'] +
                            '@'+os.environ['COMPUTERNAME'])
                path = path / (source+'.log')
                path.mkdir(parents=True, exist_ok=True)
                fhandler = logging.FileHandler(str(path), mode='a')
                fhandler.setLevel(loglevel)
                fhandler.setFormatter(formatter)
                Logger.log.addHandler(fhandler)
                                    
            # log to in-memory buffer for dashboards/UIs
            if buffer_logs:
                Logger.buffered_handler = BufferedLogHandler(Logger.log_buffer, max_size=buffer_max_size)
                Logger.buffered_handler.setLevel(logging.DEBUG)
                buffer_formatter = logging.Formatter('%(message)s')
                Logger.buffered_handler.setFormatter(buffer_formatter)
                Logger.log.addHandler(Logger.buffered_handler)

    @staticmethod
    def add_api_handler_if_configured():
        """
        Adds API handler to the logger if SHAREDDATA_ENDPOINT and SHAREDDATA_TOKEN are configured.
        This method can be called dynamically when the environment variables become available.
        """
        if (Logger.log is not None and 
            'SHAREDDATA_ENDPOINT' in os.environ and os.environ['SHAREDDATA_ENDPOINT'] and
            'SHAREDDATA_TOKEN' in os.environ and os.environ['SHAREDDATA_TOKEN']):
            
            # Check if API handler is already added to avoid duplicates
            for handler in Logger.log.handlers:
                if isinstance(handler, LogHandlerAPI):
                    return  # API handler already exists
                    
            try:
                apihandler = LogHandlerAPI()
                apihandler.setLevel(logging.DEBUG)
                jsonformatter = JsonFormatter(os.environ['USER_COMPUTER']+
                                            ';%(asctime)s;%(name)s;%(levelname)s;%(message)s',
                                            datefmt='%Y-%m-%dT%H:%M:%S%z')
                apihandler.setFormatter(jsonformatter)
                Logger.log.addHandler(apihandler)
                # print(f"INFO: API logging handler added for endpoint: {os.environ['SHAREDDATA_ENDPOINT']}")
            except Exception as e:
                Logger.log.error(f"WARNING: Failed to add API handler: {e}")

    @staticmethod
    def get_buffered_logs(lines=100):
        """
        Retrieve recent logs from the in-memory buffer.
        
        Parameters:
            lines (int): Maximum number of recent log entries to return. Defaults to 100.
        
        Returns:
            list: List of dictionaries containing log entries with keys:
                  'timestamp', 'level', 'logger', 'message'
                  Returns empty list if buffering is not enabled.
        """
        if not Logger.log_buffer:
            return []
        
        # Get the most recent logs from buffer
        recent_logs = Logger.log_buffer[-lines:] if len(Logger.log_buffer) > lines else Logger.log_buffer
        return recent_logs
    
    @staticmethod
    def clear_buffered_logs():
        """
        Clear all logs from the in-memory buffer.
        """
        Logger.log_buffer.clear()

    @staticmethod
    def read_last_day_logs():
        """
        Reads the log file from the previous day, appends its contents to the existing logs DataFrame, and updates the log status.
        
        This static method performs the following steps:
        - Sets the flag `last_day_read` to True.
        - Constructs the file path for the log file corresponding to the previous day based on the `DATABASE_FOLDER` environment variable.
        - Checks if the log file exists.
        - If the file exists, reads the log data into a DataFrame, assigning appropriate column names.
        - Concatenates the newly read logs with the existing logs stored in `Logger.dflogs`.
        - Calls `Logger.getLastLog` and `Logger.getStatus` to update log-related information.
        - If an error occurs during reading or processing, prints an error message.
        
        Assumes:
        - `Logger.dflogs` is a pandas DataFrame storing log entries.
        - `Logger.getLastLog` and `Logger.getStatus` are methods that process the logs DataFrame.
        - The log file is a semicolon-separated CSV without headers.
        """
        Logger.last_day_read = True
        lastlogfilepath = Path(os.environ['DATABASE_FOLDER']) / 'Logs'
        lastlogfilepath = lastlogfilepath / \
            ((pd.Timestamp.utcnow() + timedelta(days=-1)).strftime('%Y%m%d')+'.log')        
        if lastlogfilepath.is_file():
            try:
                _dflogs = pd.read_csv(lastlogfilepath, header=None, sep=';',
                                      engine='python', on_bad_lines='skip')
                _dflogs.columns = ['shardid', 'sequence_number',
                                   'user_name', 'asctime', 'logger_name', 'level', 'message']
                Logger.dflogs = pd.concat([_dflogs, Logger.dflogs], axis=0, ignore_index=True)
                Logger.getLastLog(Logger.dflogs)
                Logger.getStatus(Logger.dflogs)                
            except Exception as e:
                print(f'Error reading last day logs: {e}')

    @staticmethod
    def getLogs(keep_latest_heartbeat=300):
        """
        Retrieve and process log entries, updating the internal log DataFrame.
        
        This static method reads new log lines, updates the last log entry and status,
        handles heartbeat entries by keeping only those within the specified time window,
        and returns the updated DataFrame of logs.
        
        Parameters:
            keep_latest_heartbeat (int): The time window in seconds to retain the latest heartbeat logs. Defaults to 300 seconds.
        
        Returns:
            pandas.DataFrame: The updated DataFrame containing processed log entries.
        """
        dfnewlines_sorted = Logger.readLogs()
        if dfnewlines_sorted is None or len(dfnewlines_sorted) == 0:
            return Logger.dflogs
        
        Logger.getLastLog(dfnewlines_sorted)
        Logger.getStatus(dfnewlines_sorted)
        Logger.handleHeartbeats(keep_latest_heartbeat)
        return Logger.dflogs
    
    @staticmethod
    def readLogs():
        """
        Reads new log entries from the current day's log file into a DataFrame.
        
        This static method reads log lines appended since the last read position from a log file named with the current UTC date
        located in the directory specified by the 'DATABASE_FOLDER' environment variable under 'Logs'. It parses the log entries,
        handles multi-column messages by merging them, and converts timestamps to datetime objects.
        
        The method maintains and updates internal Logger class state including:
        - The last read file position to avoid re-reading old entries.
        - The cached maximum timestamp seen to determine if a full sort of logs is needed.
        - The combined DataFrame of all logs read so far, sorted by timestamp and sequence number.
        
        Returns:
            pd.DataFrame: A DataFrame containing the newly read and sorted log entries with columns:
                          ['shardid', 'sequence_number', 'user_name', 'asctime', 'logger_name', 'level', 'message'].
                          Returns an empty DataFrame with these columns if no new logs are found or the log file does not exist.
        """
        dfnewlines = pd.DataFrame(
            [], columns=['shardid', 'sequence_number', 'user_name', 
                         'asctime', 'logger_name', 'level', 'message']
            )
        if not Logger.last_day_read:
            Logger.read_last_day_logs()

        _logfilepath = Path(os.environ['DATABASE_FOLDER']) / 'Logs'
        _logfilepath = _logfilepath / \
            (pd.Timestamp.utcnow().strftime('%Y%m%d')+'.log')
        if Logger.logfilepath != _logfilepath:
            Logger._logfileposition = 0
            Logger.logfilepath = _logfilepath

        if Logger.logfilepath.is_file():
            
            with open(Logger.logfilepath, 'r') as file:
                file.seek(Logger._logfileposition)
                newlines = '\n'.join(file.readlines())
                if not newlines.strip():   # fix: prevent pd.read_csv crash on empty string
                    return dfnewlines
                dfnewlines = pd.read_csv(StringIO(newlines), header=None, sep=';',
                                            engine='python', on_bad_lines='skip')
                if dfnewlines.shape[1] > 7:
                    # Merge all columns from 6 onward into a single message
                    message = dfnewlines.iloc[:, 6:].apply(lambda x: ';'.join(x.dropna().astype(str)), axis=1)
                    dfnewlines = dfnewlines.iloc[:, :7]
                    dfnewlines.iloc[:, 6] = message 
                
                dfnewlines.columns = [
                    'shardid', 'sequence_number', 'user_name', 'asctime', 'logger_name', 'level', 'message'
                ]
                dfnewlines = dfnewlines[dfnewlines['asctime'].notna()]
                if dfnewlines.empty:
                    return dfnewlines
                                    
                dfnewlines['asctime'] = pd.to_datetime(dfnewlines['asctime'],format='mixed', errors='coerce')
                
                # Use cached max asctime
                max_asctime = Logger._max_asctime

                need_full_sort = False
                if Logger._sorted_until == 0 or max_asctime is None:
                    need_full_sort = True
                elif (dfnewlines['asctime'].min() - max_asctime).total_seconds() <=  -15:
                    need_full_sort = True

                dfnewlines_sorted = dfnewlines.sort_values(['asctime', 'sequence_number'])
                if need_full_sort:
                    Logger.dflogs = pd.concat([Logger.dflogs, dfnewlines_sorted], ignore_index=True)
                    Logger.dflogs['asctime'] = pd.to_datetime(Logger.dflogs['asctime'])
                    Logger.dflogs = Logger.dflogs.sort_values(['asctime', 'sequence_number'], ignore_index=True)
                    Logger._sorted_until = len(Logger.dflogs)                                            
                    Logger._max_asctime = pd.to_datetime(Logger.dflogs['asctime']).max()
                else:
                    # Append new lines and sort only the new part
                    Logger.dflogs = pd.concat([Logger.dflogs, dfnewlines_sorted], ignore_index=True)
                    Logger._sorted_until = len(Logger.dflogs)                        
                    Logger._max_asctime = max(
                        max_asctime,
                        dfnewlines_sorted['asctime'].iloc[-1]
                    )                    
                Logger._logfileposition = file.tell()                        
                    
                                                        
                return dfnewlines_sorted
        
        return dfnewlines

    @staticmethod
    def handleHeartbeats(keep_latest=500):
        """
        Processes heartbeat messages in the log DataFrame by retaining only the latest heartbeat entry per user and logger, updating the heartbeat DataFrame accordingly, and limiting the number of stored heartbeat messages to a specified maximum.
        
        Parameters:
            keep_latest (int): The maximum number of latest heartbeat messages to keep in the logs. Defaults to 500.
        
        Effects:
            - Updates Logger.dfheartbeats with the most recent heartbeat entries grouped by 'user_name' and 'logger_name'.
            - Filters Logger.dflogs to retain all non-heartbeat messages and only the latest 'keep_latest' heartbeat messages.
        """
        df = Logger.dflogs
        idxhb = np.array(['#heartbeat#' in s for s in df['message'].astype(str)])
        dflasthb = df[idxhb].groupby(['user_name','logger_name']).last()
        newidx = dflasthb.index.union(Logger.dfheartbeats.index)
        Logger.dfheartbeats = Logger.dfheartbeats.reindex(newidx)
        Logger.dfheartbeats.index.names = ['user_name','logger_name']
        Logger.dfheartbeats.loc[dflasthb.index,dflasthb.columns] = dflasthb.values
        idshb = np.where(idxhb)[0]
        if len(idshb) > keep_latest:
            idshb = idshb[-keep_latest:]
        ids = np.where(~idxhb)[0]
        ids = np.sort([*ids, *idshb])
        df = df.iloc[ids, :]
        Logger.dflogs = df

    @staticmethod
    def getLastLog(df: pd.DataFrame) -> pd.DataFrame:
        """
        Update and return the most recent log entries per (user_name, logger_name) group from the given DataFrame.
        
        This static method compares the provided DataFrame's latest logs with the existing stored logs (`Logger.dflast`) and updates them based on recency criteria:
        - If the 'asctime' timestamp is newer, the log entry is updated.
        - If the 'asctime' timestamps are equal, the 'sequence_number' is used to determine which log is more recent.
        
        Args:
            df (pd.DataFrame): DataFrame containing log entries with columns including 'user_name', 'logger_name', 'asctime', and 'sequence_number'.
        
        Returns:
            pd.DataFrame: DataFrame containing the updated last log entries for the affected (user_name, logger_name) groups.
        """
        _dflast = df.groupby(['user_name', 'logger_name']).last()
        _dflast['asctime'] = pd.to_datetime(_dflast['asctime'])

        notinidx = _dflast.index.difference(Logger.dflast.index)
        Logger.dflast = Logger.dflast.reindex(_dflast.index.union(Logger.dflast.index))
        Logger.dflast.index.names = ['user_name', 'logger_name']
        Logger.dflast.loc[notinidx, _dflast.columns] = _dflast.loc[notinidx].values

        idx = _dflast.index
        asctime_newer = _dflast['asctime'] > Logger.dflast.loc[idx, 'asctime']
        asctime_equal = _dflast['asctime'] == Logger.dflast.loc[idx, 'asctime']
        sequence_higher = _dflast['sequence_number'].astype(str) > Logger.dflast.loc[idx, 'sequence_number'].astype(str)

        idxnew = _dflast.index[asctime_newer | (asctime_equal & sequence_higher)]
        Logger.dflast.loc[idxnew, _dflast.columns] = _dflast.loc[idxnew].values

        idxnew = idxnew.union(notinidx)

        return Logger.dflast.loc[idxnew]
                
    @staticmethod
    def getStatus(df):
        """
        Categorizes log messages from the input DataFrame and updates class-level DataFrames accordingly.
        
        Filters the provided DataFrame `df` for specific log message patterns indicating routine completion, start, errors, and commands to run. For each identified category:
        - Appends the matching rows to the corresponding class attribute DataFrame (`dfcompleted`, `dfstarted`, `dferror`, or `dfrun`).
        - For "Command to run" messages, extracts additional details such as routine name, user name, and logger name, adding these as new columns before appending.
        
        Assumes the class has pandas DataFrame attributes named `dfcompleted`, `dfstarted`, `dferror`, and `dfrun`.
        
        Parameters:
            df (pandas.DataFrame): DataFrame containing a 'message' column with log entries as strings.
        
        Returns:
            None
        """
        idx = np.array(['ROUTINE COMPLETED!' in s for s in df['message'].astype(str)])
        if any(idx):
            _df = df[idx]
            Logger.dfcompleted = pd.concat([Logger.dfcompleted,_df],ignore_index=True)

        idx = np.array(['ROUTINE STARTED!' in s for s in df['message'].astype(str)])
        if any(idx):
            _df = df[idx]
            Logger.dfstarted = pd.concat([Logger.dfstarted,_df],ignore_index=True)

        idx = np.array(['ROUTINE ERROR!' in s for s in df['message'].astype(str)])
        if any(idx):
            _df = df[idx]
            Logger.dferror = pd.concat([Logger.dferror,_df],ignore_index=True)

        idx = np.array(['Command to run ' in s for s in df['message'].astype(str)])
        if any(idx):
            _df = df[idx].copy()
            idx = ['<-' in s for s in _df['message']]
            if any(idx):
                _df.loc[idx,'message'] = _df.loc[idx,'message'].apply(lambda x: x.split(',')[-1])
            # get the routine name
            _df['routine'] = _df['message'].apply(lambda x: x.replace('Command to run ','').split(' ')[0])
            _df['user_name'] = _df['routine'].apply(lambda x: x.split(':')[0])
            _df['logger_name'] = _df['routine'].apply(lambda x: x.split(':')[1] if ':' in x else '')
            Logger.dfrun = pd.concat([Logger.dfrun,_df],ignore_index=True)

    @staticmethod
    def log_writer(shdata: SharedData):
        """
        '''
        Continuously processes log records from a global queue, writes them to daily log files with file locking, and inserts them into MongoDB collections.
        
        This static method performs the following steps in an infinite loop:
        - Retrieves a log record from the global `log_queue`.
        - Generates a unique ObjectId for the log entry.
        - Formats and writes the log entry to a daily log file located under the directory specified by the `DATABASE_FOLDER` environment variable, ensuring thread-safe access using a file lock.
        - Parses the log timestamp and determines if the log is a heartbeat message.
        - Inserts non-heartbeat logs into a time-series MongoDB collection partitioned by date.
        - Inserts heartbeat logs into a dedicated MongoDB heartbeat collection, using a SHA-256 hash as the document ID.
        - Handles and prints exceptions that occur during MongoDB insertions.
        
        Environment variables used:
        - `USER_COMPUTER`: Identifier for the source machine, used as shard ID and in log entries.
        - `DATABASE_FOLDER`: Base directory path for storing log files.
        
        Dependencies:
        - `log_queue`: A global queue providing log records.
        - `SharedData`: Provides access to MongoDB collections.
        - `FileLock`: Ensures exclusive access to log files during writes.
        - `ObjectId`: Generates unique identifiers
        """
        
        while True:
            rec = Logger.log_queue.get()

            # Parse asctime string to datetime with timezone info
            asctime_str = rec['asctime']
            asctime = datetime.strptime(asctime_str, '%Y-%m-%dT%H:%M:%S%z')
                                                                    
            # Generate ObjectId at the client
            # and write to log file
            _id = ObjectId()
            Logger._log_writer_file(rec, _id)            

            # logger unique hash key
            hbkey = rec['user_name'].replace('\\', '/')
            hbkey += ":"+rec['logger_name'].replace('\\', '/')
            loghash = hashlib.sha256(hbkey.encode('utf-8')).hexdigest()
            
            # Insert into logs table            
            isheartbeat = '#heartbeat#' in rec['message']            
            if isheartbeat:
                Logger._log_writer_heartbeats(shdata, rec, asctime, loghash)
            else: # not heartbeat
                # extend realtime logs table
                Logger._log_writer_extend(shdata, rec, asctime, _id)
                # upsert into daily logs table
                Logger._log_writer_upsert(shdata, rec, asctime, loghash)
                                
    def _log_writer_file(rec, _id):
        """
        Writes a log record to a daily log file with file locking.
        Parameters:
            rec (dict): A dictionary containing log record fields.
            _id (ObjectId): The unique identifier for the log entry.
        """

        line = '%s;%s;%s;%s;%s;%s;%s' % (
            os.environ['USER_COMPUTER'],
            str(_id),
            rec['user_name'],
            rec['asctime'],
            rec['logger_name'],
            rec['level'],
            str(rec['message']).replace(';', ',')
        )
        dt = datetime.strptime(
            rec['asctime'][:-5], '%Y-%m-%dT%H:%M:%S')

        logfilepath = Path(os.environ['DATABASE_FOLDER']) / 'Logs'
        logfilepath = logfilepath / (dt.strftime('%Y%m%d')+'.log')
        if not logfilepath.parents[0].is_dir():
            os.makedirs(logfilepath.parents[0])
        lock_path = str(logfilepath) + ".lock"
        with FileLock(lock_path):
            with open(logfilepath, 'a+', encoding='utf-8') as f:
                f.write(line.replace('\n', ' ').replace('\r', ' ')+'\n')
                f.flush()

    def _log_writer_extend(shdata, rec, asctime, _id):
        """
        Inserts a log record into a time-series MongoDB collection partitioned by date.
        Parameters:
            shdata: The shared data instance for database operations.
            rec (dict): A dictionary containing log record fields.
            asctime (datetime): The timestamp of the log record.
            _id (ObjectId): The unique identifier for the log entry.
        """
        # save all non heartbeat logs
        document = {            
            "hash" : str(_id),
            "asctime": asctime,            
            "user_name": rec['user_name'].replace('\\', '/'),
            "logger_name": rec['logger_name'].replace('\\', '/'),
            "level": rec['level'],    
            "message": rec['message'],
            "shard_id": os.environ['USER_COMPUTER']
        }
        try:
            logcoll = shdata.table('Hashs','RT','LOGGER','LOGS/'+asctime.strftime('%Y%m%d'), 
                names = ['hash','mtime'],
                formats = ['|S16','<M8[ns]'],
                hasindex=False,is_schemaless=True,size=0)
            logcoll = logcoll.extend(document)                    
        except Exception as e:
            print(f"An error occurred inserting a log to table: {e}")                    

    def _log_writer_upsert(shdata, rec, asctime, loghash):
        
        # upsert daily routine state logs
        routine_states = {
            'Command to run ': 'STARTED',
            'ROUTINE STARTED!':'RUNNING',
            'ROUTINE COMPLETED!':'COMPLETED',
            'ROUTINE ERROR!':'ERROR',
        }
        
        document = {
            "date" : asctime,
            "hash" : str(loghash),
            "asctime": asctime,            
            "user_name": rec['user_name'].replace('\\', '/'),
            "logger_name": rec['logger_name'].replace('\\', '/'),
            "level": rec['level'],
            "message": rec['message'],
            "shard_id": os.environ['USER_COMPUTER']
        }

        try:
            # check for routine state messages            
            for state_msg, state in routine_states.items():
                if state_msg in rec['message']:                    
                    logtbl = shdata.table(
                        'Text','D1','WORKERPOOL',state,
                        names = ['date','hash','mtime'],
                        formats = ['<M8[ns]','|S64','<M8[ns]'],
                        size=1e6,
                        is_schemaless=True
                    )
                    if state_msg == 'Command to run ':
                        # extract routine name
                        
                        if '<-' in document['message']:
                            document['message'] = document['message'].split(',')[-1]
                        # get the routine name
                        routine = document['message'].replace('Command to run ','').split(' ')[0]
                        document['user_name'] = routine.split(':')[0]
                        document['logger_name'] = routine.split(':')[1] if ':' in routine else ''
                        hash_str = document['user_name'] + ':' + document['logger_name']
                        document['hash'] = str(hashlib.sha256(hash_str.encode('utf-8')).hexdigest())
                    
                    logtbl.upsert(document)
                    break
            
            logtbl = shdata.table(
                'Text','D1','LOGGER','LOGS',
                names = ['date','hash','mtime'],
                formats = ['<M8[ns]','|S64','<M8[ns]'],
                size=1e6,
                is_schemaless=True
            )
            logtbl.upsert(document)

        except Exception as e:
            print(f"An error occurred inserting a heartbeat to table: {e}")

    def _log_writer_heartbeats(shdata, rec, asctime, loghash):
        # Insert into daily heartbeat table for realtime monitoring        
        document = {
            "date" : asctime,
            "hash" : str(loghash),
            "asctime": asctime,            
            "user_name": rec['user_name'].replace('\\', '/'),
            "logger_name": rec['logger_name'].replace('\\', '/'),
            "level": rec['level'],
            "message": rec['message'],
            "shard_id": os.environ['USER_COMPUTER']
        }
        try:                    
            logtbl = shdata.table(
                'Text','D1','WORKERPOOL','HEARTBEATS',
                names = ['date','hash','mtime'],
                formats = ['<M8[ns]','|S64','<M8[ns]'],
                size=1e6,
                is_schemaless=True
            )
            logtbl.upsert(document)

            logtbl = shdata.table(
                'Text','D1','LOGGER','LOGS',
                names = ['date','hash','mtime'],
                formats = ['<M8[ns]','|S64','<M8[ns]'],
                size=1e6,
                is_schemaless=True
            )
            logtbl.upsert(document)
        except Exception as e:
            print(f"An error occurred inserting a heartbeat to table: {e}")