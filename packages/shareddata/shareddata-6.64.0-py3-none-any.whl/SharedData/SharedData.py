import os
import psutil
import pandas as pd
import numpy as np
import json
import warnings
import time
import shutil
from datetime import datetime, timezone

from multiprocessing import shared_memory
from pathlib import Path
import importlib.metadata

# Ignore the "invalid value encountered in cast" warning
warnings.filterwarnings("ignore", message="invalid value encountered in cast")
# warnings.filterwarnings("ignore", category=RuntimeWarning)

import SharedData.Defaults as Defaults
from SharedData.Logger import Logger
from SharedData.TableDisk import TableDisk
from SharedData.TimeseriesContainer import TimeseriesContainer
from SharedData.TimeSeriesDisk import TimeSeriesDisk
from SharedData.Utils import datetype
from SharedData.IO.AWSS3 import S3ListFolder, S3GetSession, S3DeleteTable, S3DeleteTimeseries
from SharedData.Utils import remove_shm_from_resource_tracker, cpp
from SharedData.MultiProc import io_bound_unordered
from SharedData.IO.MongoDBClient import MongoDBClient
from SharedData.Database import DATABASE_PKEYS, PERIODS
from SharedData.CollectionMongoDB import CollectionMongoDB
from SharedData.StreamKafka import StreamKafka
from SharedData.CacheRedis import CacheRedis

class SharedData:    

    """
    Class for managing shared data resources, including tables, timeseries, dataframes, collections, streams, and caches, with support for local disk storage, in-memory storage, MongoDB collections, AWS S3 integration, and Kafka streams.
    
    Features:
    - Initialization with user credentials, AWS keys, and environment setup.
    - Methods to create, access, and manage data containers: tables, timeseries, dataframes (stub), collections, streams, and caches.
    - Shared memory management with mutex locking for process-safe access.
    - Listing and querying of local and remote data resources, including disk usage and shared memory segments.
    - Loading and deleting of tables, timeseries, collections, and streams with error handling and logging.
    - Integration with MongoDB for collection management.
    - Support for partitioning and schema initialization for efficient data handling.
    - Concurrent loading of tables with configurable parallelism.
    
    Initialization Parameters:
    - source (str): Identifier for the data source.
    - user (str, optional): Username for access; defaults to environment USERNAME or 'guest'.
    - endpoint (str, optional): Endpoint URL for shared data service.
    - token (str, optional): Authentication token for shared data service.
    - access_key_id (str, optional): AWS access key ID.
    - secret_access_key (
    """
    def __init__(self, source, user=None,
                 endpoint=None,token = None,
                 access_key_id=None,secret_access_key=None, # AWS                 
                 quiet=False, buffer_logs=False, buffer_max_size=500):
        """
        Initializes a SharedData instance by setting up environment variables, database folders, logger connection, and schema.
        
        Parameters:
        - source (str): Identifier for the data source.
        - user (str, optional): Username for access; defaults to environment variable 'USERNAME' or 'guest' if not provided.
        - endpoint (str, optional): Endpoint URL for API connection; sets 'SHAREDDATA_ENDPOINT' environment variable if provided.
        - token (str, optional): Authentication token; sets 'SHAREDDATA_TOKEN' environment variable if provided.
        - access_key_id (str, optional): AWS access key ID; sets 'AWS_ACCESS_KEY_ID' environment variable if provided.
        - secret_access_key (str, optional): AWS secret access key; sets 'AWS_SECRET_ACCESS_KEY' environment variable if provided.
        - quiet (bool, optional): If True, suppresses connection log output. Defaults to False.
        - buffer_logs (bool, optional): If True, enables in-memory log buffering for dashboard/UI display. Defaults to False.
        - buffer_max_size (int, optional): Maximum number of log entries to keep in the buffer. Defaults to 500.
        
        Raises:
        - Exception: If 'access_key_id' is provided without a corresponding 'secret_access_key'.
        """
        self.source = source
        if user is None:
            if 'USERNAME' in os.environ:
                user = os.environ['USERNAME']
            else:
                user = 'guest'
        self.user = user
        # API operation
        if not endpoint is None:
            os.environ['SHAREDDATA_ENDPOINT'] = endpoint
        if not token is None:
            os.environ['SHAREDDATA_TOKEN'] = token
        # AWS operation
        if not access_key_id is None:
            os.environ['AWS_ACCESS_KEY_ID'] = access_key_id
            if not secret_access_key is None:
                os.environ['AWS_SECRET_ACCESS_KEY'] = secret_access_key
            else:
                raise Exception('secret_access_key is None')
        
        # DATA DICTIONARY
        self.data = {}

        # MONGODB VARIABLES
        self._mongodb = None

        # LOGIN VARIABLES
        self.islogged = False
        self.source = source
        self.user = user   
        
        # Ie. "/nvme0/db,/nvme1/db,..."
        self.dbfolders = [os.environ['DATABASE_FOLDER']]
        if 'DATABASE_FOLDERS' in os.environ.keys():
            _dbfolders = os.environ['DATABASE_FOLDERS'].split(',')
            self.dbfolders = list(np.unique(list(_dbfolders)+self.dbfolders))   
        
        # CONNEC TO LOGGER
        Logger.connect(self.source, self.user, buffer_logs=buffer_logs, buffer_max_size=buffer_max_size)
        
        # REMOVES SHARED MEMORY FROM RESOURCE TRACKER
        if (os.name == 'posix'):
            remove_shm_from_resource_tracker()
        
        # INIT TABLE SCHEMA
        self.schema = None
        if len(self.dbfolders)>1:
            self.init_schema()
        
        if not self.islogged:
            self.islogged = True
            if not quiet:
                try:
                    SHAREDDATA_VERSION = importlib.metadata.version("shareddata")
                    Logger.log.info('User:%s,SharedData:%s CONNECTED!' %
                                    (self.user, SHAREDDATA_VERSION))
                except:
                    Logger.log.info('User:%s CONNECTED!' % (self.user))
        
    ###############################################
    ############# DATA CONTAINERS #################
    ###############################################
    
    ############# TABLE #################
    def table(self, database, period, source, tablename,
            names=None, formats=None, size=None, hasindex=True,\
            value=None, user='master', overwrite=False,\
            type='DISK',partitioning=None, is_schemaless=False):
                        
        """
        '''
        Create or retrieve a table object based on the specified parameters.
        
        Parameters:
        - database (str): Name of the database. Must be in DATABASE_PKEYS.
        - period (str): Time period identifier. Must be in PERIODS.
        - source (str): Source identifier. Cannot contain '/'.
        - tablename (str): Name of the table. Can contain at most one '/' to indicate partitioning.
        - names (list, optional): List of column names for the table.
        - formats (list, optional): List of data formats corresponding to the columns.
        - size (int, optional): Size parameter for the table.
        - hasindex (bool, optional): Indicates if the table has an index. Defaults to True.
        - value (optional): Initial records or data to populate the table.
        - user (str, optional): User identifier. Defaults to 'master'.
        - overwrite (bool, optional): Whether to overwrite existing data. Defaults to False.
        - type (str, optional): Storage type of the table, either 'DISK' or 'MEMORY'. Defaults to 'DISK'.
        - partitioning (str, optional): Partitioning scheme ('yearly', 'monthly', 'daily'). If not provided, inferred from tablename.
        
        Returns:
        - records:
        """
        path = f'{user}/{database}/{period}/{source}/table/{tablename}'
        if (not path in self.data.keys()) | overwrite:
            # 1. CHECK IF DATABASE IS VALID
            if not database in DATABASE_PKEYS:
                errmsg = f'Invalid database {database}'
                raise Exception(errmsg)
            # 2. CHECK IF PERIOD IS VALID
            if not period in PERIODS:
                errmsg = f'Invalid period {period}'
                raise Exception(errmsg)
            # 3. CHECK IF SOURCE IS VALID
            if '/' in source:
                errmsg = f'Invalid source cant have / {source}'
                raise Exception(errmsg)
            # 4. CHECK IF TABLENAME IS VALID
            # tablename can have only one partition /
            if not tablename.count('/') <= 1:
                errmsg = f'Invalid tablename cant have more than one / {tablename}'
                raise Exception(errmsg)
            # 5. GET PARTITIONING
            if tablename.count('/') == 1:
                partitioningstr = tablename.split('/')[1]
                if len(partitioningstr) == 4:
                    partitioning = 'yearly'
                elif len(partitioningstr) == 6:
                    partitioning = 'monthly'
                elif len(partitioningstr) == 8:
                    partitioning = 'daily'
            else:
                if hasindex:
                    if period != 'D1':
                        raise Exception(f'Please specify partitioning for {period} tables')
                
            if type == 'DISK':
                self.data[path] = TableDisk(self, database, period, source,
                                        tablename, records=value, names=names, formats=formats, size=size, hasindex=hasindex,
                                        user=user, overwrite=overwrite, partitioning=partitioning, is_schemaless=is_schemaless)
            else:
                raise Exception(f'Invalid type {type}')
        elif not value is None:
            tbl = self.data[path]
            if tbl.hdr['hasindex']==1:                
                tbl.records.upsert(value)
            else:
                tbl = tbl.records.extend(value)
            
        return self.data[path].records

    ############# TIMESERIES #################
    def timeseries(self, database, period, source, tag=None, user='master',
                   startDate=None,type='DISK',
                   columns=None, value=None, overwrite=False): # tags params
        
        # 1. CHECK IF DATABASE IS VALID
        if not database in DATABASE_PKEYS:
            """
            '''
            Retrieve or create a time series data container and access or update its tagged data.
            
            Parameters:
            - database (str): Name of the database.
            - period (str): Time period identifier.
            - source (str): Data source identifier.
            - tag (str, optional): Specific tag within the time series to access or modify. Defaults to None.
            - user (str, optional): User identifier. Defaults to 'master'.
            - startDate (optional): Start date for the time series. If provided, must match existing startDate if already set.
            - type (str, optional): Storage type for the time series, either 'DISK' or 'MEMORY'. Defaults to 'DISK'.
            - columns (optional): Columns specification for new time series data.
            - value (optional): Values for new time series data.
            - overwrite (bool, optional): Whether to overwrite existing tag data. Defaults to False.
            
            Returns:
            - The data associated with the specified tag in the time series.
            
            Raises:
            - Exception: If database or period is invalid.
            - Exception: If source contains invalid characters.
            - Exception: If tag contains more than one '/' character.
            - Exception: If startDate conflicts with an existing startDate.
            - Exception: If the specified tag does not exist and no data
            """
            errmsg = f'Invalid database {database}'
            raise Exception(errmsg)
        # 2. CHECK IF PERIOD IS VALID
        if not period in PERIODS:
            errmsg = f'Invalid period {period}'
            raise Exception(errmsg)
        # 3. CHECK IF SOURCE IS VALID
        if '/' in source:
            errmsg = f'Invalid source cant have / {source}'
            raise Exception(errmsg)
        # 4. CHECK IF TAG IS VALID
        # tag can have only one partition /
        if not tag is None:
            if tag.count('/') > 1:
                errmsg = f'Invalid tag cant have more than one / {tag}'
                raise Exception(errmsg)

        path = f'{user}/{database}/{period}/{source}/timeseries'
        if not path in self.data.keys():
            """
            Retrieve or create a time series data container and access or update its tagged data.
            
            Parameters:
            - database (str): Name of the database.
            - period (str): Time period identifier.
            - source (str): Data source identifier.
            - tag (str, optional): Specific tag within the time series to access or modify. Defaults to None.
            - user (str, optional): User identifier. Defaults to 'master'.
            - startDate (optional): Start date for the time series. If provided, must match existing startDate if already set.
            - type (str, optional): Storage type for the time series, either 'DISK' or 'MEMORY'. Defaults to 'DISK'.
            - columns (optional): Columns specification for new time series data.
            - value (optional): Values for new time series data.
            - overwrite (bool, optional): Whether to overwrite existing tag data. Defaults to False.
            
            Returns:
            - The data associated with the specified tag in the time series.
            
            Raises:
            - Exception: If startDate conflicts with an existing startDate.
            - Exception: If the specified tag does not exist and no data is provided to create it.
            - Exception: If overwrite is True for MEMORY type time series, which is unsupported.
            """
            self.data[path] = TimeseriesContainer(self, database, period, source, 
                user=user, type=type, startDate=startDate)
            
        if not startDate is None:
            if self.data[path].startDate != startDate:
                raise Exception('Timeseries startDate is already set to %s' %
                                self.data[path].startDate)
            
        if tag is None:
            if not overwrite:
                self.data[path].load()
            return self.data[path]
                    
        if (overwrite) | (not tag in self.data[path].tags.keys()):
            if (columns is None) & (value is None):
                self.data[path].load()
                if not tag in self.data[path].tags.keys():
                    errmsg = 'Tag %s/%s doesnt exist' % (path, tag)
                    Logger.log.error(errmsg)                    
                    raise Exception(errmsg)
            else:
                if self.data[path].type == 'DISK':
                    self.data[path].tags[tag] = TimeSeriesDisk(
                        self, self.data[path],database, period, source, tag,
                        value=value, columns=columns, user=user,                        
                        overwrite=overwrite)
                else:
                    raise Exception(f'Not implemented for {self.data[path].type} type')

        return self.data[path].tags[tag].data

    ############# DATAFRAME #################
    def dataframe(self, database, period, source,
                  date=None, value=None, user='master'):
        """
        Generate a DataFrame based on the specified database, period, and source.
        
        Parameters:
            database (str): The name of the database to query.
            period (str): The time period for which data is requested.
            source (str): The data source identifier.
            date (optional): Specific date or date range for filtering data. Default is None.
            value (optional): Specific value or metric to retrieve. Default is None.
            user (str): Username for authentication or access control. Default is 'master'.
        
        Returns:
            pandas.DataFrame: A DataFrame containing the requested data.
        """
        pass

    ############# COLLECTION #################
    def collection(self, database, period, source, tablename,
            names=None, formats=None, size=None, hasindex=True,\
            value=None, user='master', overwrite=False,\
            type='MONGODB', partitioning=None, create_if_not_exists = True):
                        
        """
        '''
        Create or retrieve a collection object for a specified database, period, source, and tablename.
        
        This method validates the input parameters, manages partitioning if specified in the tablename,
        and either returns an existing collection object or creates a new one using the specified backend type.
        
        Parameters:
            database (str): The name of the database. Must be in DATABASE_PKEYS.
            period (str): The time period. Must be in PERIODS.
            source (str): The data source name. Cannot contain '/'.
            tablename (str): The name of the table or collection. Can contain at most one '/' to indicate partitioning.
            names (list, optional): List of field names for the collection. Defaults to None.
            formats (list, optional): List of formats corresponding to the field names. Defaults to None.
            size (int, optional): Size parameter for the collection. Defaults to None.
            hasindex (bool, optional): Whether the collection has an index. Defaults to True.
            value (optional): Initial records or data to populate the collection. Defaults to None.
            user (str, optional): User identifier. Defaults to 'master'.
            overwrite (bool, optional): Whether to overwrite existing data. Defaults to False.
        """
        path = f'{user}/{database}/{period}/{source}/collection/{tablename}'
        if (not path in self.data.keys()) or overwrite:
            # 1. CHECK IF DATABASE IS VALID
            if not database in DATABASE_PKEYS:
                errmsg = f'Invalid database {database}'
                raise Exception(errmsg)
            # 2. CHECK IF PERIOD IS VALID
            if not period in PERIODS:
                errmsg = f'Invalid period {period}'
                raise Exception(errmsg)
            # 3. CHECK IF SOURCE IS VALID
            if '/' in source:
                errmsg = f'Invalid source cant have / {source}'
                raise Exception(errmsg)
            # 4. CHECK IF TABLENAME IS VALID
            # tablename can have only one partition /
            if not tablename.count('/') <= 1:
                errmsg = f'Invalid tablename cant have more than one / {tablename}'
                raise Exception(errmsg)
            
            if type == 'MONGODB':
                if '/' in tablename:
                    _, partition = tablename.split('/')
                    partitioning = datetype(partition)
                    if partitioning == '':
                        partitioning = None
                    
                self.data[path] = CollectionMongoDB(self, database, period, source,tablename, 
                    hasindex=hasindex, user=user, overwrite=overwrite, 
                    partitioning=partitioning,create_if_not_exists=create_if_not_exists)
            else:
                raise Exception(f'Invalid type {type}')
            
        return self.data[path]

    ############# STREAM #################
    def stream(self, database, period, source, tablename, user='master', 
               type='KAFKA',
               bootstrap_servers=None, replication=None, partitions=None, use_aiokafka=False, create_if_not_exists=True):
        """
        '''
        Initialize and return a streaming data source object for the specified database, period, source, and table.
        
        Parameters:
            database (str): The name of the database to stream from. Must be a valid database key.
            period (str): The time period for the stream. Only 'RT' (real-time) is supported.
            source (str): The data source name. Must not contain '/' characters.
            tablename (str): The name of the table to stream. Must not contain '/' characters.
            user (str, optional): The user name for the stream path. Defaults to 'master'.
            type (str, optional): The type of stream to create. Currently only 'KAFKA' is supported. Defaults to 'KAFKA'.
            bootstrap_servers (optional): Kafka bootstrap servers configuration.
            replication (optional): Replication factor for Kafka topic.
            partitions (optional): Number of partitions for Kafka topic.
            use_aiokafka (bool, optional): Whether to use aiokafka for asynchronous Kafka consumption. Defaults to False.
            create_if_not_exists (bool, optional): Whether to create the stream if it does not exist. Defaults to True.
        
        Returns:
            StreamKafka: An instance of the StreamKafka class representing the requested stream
        """
        path = f'{user}/{database}/{period}/{source}/stream/{tablename}'
        if (not path in self.data.keys()):
            # 1. CHECK IF DATABASE IS VALID
            if not database in DATABASE_PKEYS:
                errmsg = f'Invalid database {database}'
                raise Exception(errmsg)
            # 2. CHECK IF PERIOD IS VALID
            if period != 'RT':
                errmsg = f'Only RT period is supported for streams {period}'
                raise Exception(errmsg)
            # 3. CHECK IF SOURCE IS VALID
            if '/' in source:
                errmsg = f'Invalid source cant have / {source}'
                raise Exception(errmsg)
            # 4. CHECK IF TABLENAME IS VALID
            # tablename can have only one partition /
            if not tablename.count('/') <= 0:
                errmsg = f'Invalid tablename cant have  / {tablename}'
                raise Exception(errmsg)
        
            if type == 'KAFKA':
                self.data[path] = StreamKafka(self, database, period, source, tablename, user,
                                              bootstrap_servers, replication, 
                                              partitions,use_aiokafka=use_aiokafka,
                                              create_if_not_exists=create_if_not_exists)
            else:
                raise Exception(f'Invalid  stream type {type}')
        
        return self.data[path]

    ############# CACHE #################
    def cache(self, database, period, source, tablename, user='master', 
              type='REDIS'):
        """
        Initialize and retrieve a cache object for a specified database, period, source, and table name.
        
        Parameters:
            database (str): The name of the database to use. Must be a valid key in DATABASE_PKEYS.
            period (str): The time period for the cache. Only 'RT' (real-time) is supported.
            source (str): The data source identifier. Must not contain '/' characters.
            tablename (str): The name of the table to cache. Can contain at most one '/' character.
            user (str, optional): The user identifier. Defaults to 'master'.
            type (str, optional): The type of cache to create. Only 'REDIS' is supported. Defaults to 'REDIS'.
        
        Returns:
            CacheRedis: An instance of the CacheRedis class corresponding to the specified parameters.
        
        Raises:
            Exception: If the database is invalid, period is not 'RT', source contains '/',
                       tablename contains more than one '/', or the cache type is unsupported.
        """
        path = f'{user}/{database}/{period}/{source}/cache/{tablename}'
        if (not path in self.data.keys()):
            # 1. CHECK IF DATABASE IS VALID
            if not database in DATABASE_PKEYS:
                errmsg = f'Invalid database {database}'
                raise Exception(errmsg)
            # 2. CHECK IF PERIOD IS VALID
            if period != 'RT':
                errmsg = f'Only RT period is supported for cache {period}'
                raise Exception(errmsg)
            # 3. CHECK IF SOURCE IS VALID
            if '/' in source:
                errmsg = f'Invalid source cant have / {source}'
                raise Exception(errmsg)
            # 4. CHECK IF TABLENAME IS VALID
            # tablename can have only one partition /
            if not tablename.count('/') <= 1:
                errmsg = f'Invalid tablename cant have more than one / {tablename}'
                raise Exception(errmsg)
        
            if type == 'REDIS':
                self.data[path] = CacheRedis(database, period, source, tablename, user)
            else:
                raise Exception(f'Invalid  stream type {type}')
        
        return self.data[path]

    ###############################################
    ######### SHARED MEMORY MANAGEMENT ############
    ###############################################    
    def init_schema(self):        

        # DB TABLES
        """
        Initialize the database schema for the 'Symbols' table with predefined column names and data formats.
        
        This method defines the structure of the 'Symbols' table by specifying the column names and their corresponding data types,
        covering local and remote file metadata, mutex information, and additional schema metadata fields.
        The schema is linked to the current computer name obtained from the environment variable 'COMPUTERNAME'.
        
        Sets:
        - self.schema: A table schema object created with the specified names, formats, and size (100,000 entries).
        """
        names = [
            'symbol', 'mtime', 
            'last_scan_local','folder_local', 'created_local', 'last_modified_local', 'mtime_local', 'mtime_head_local', 'mtime_tail_local', 'size_local', 'files_local',
            'mutex_pid', 'mutex_type', 'mutex_isloaded',
            'last_scan_remote','folder_remote', 'last_modified_remote', 'mtime_remote', 'mtime_head_remote', 'mtime_tail_remote', 'size_remote', 'files_remote','storage_class_remote',
            'user', 'database', 'period', 'source', 'container', 'tablename','partition', 'partitioning_period',
            'names', 'formats', 'size', 'hasindex', 'type'
        ]

        formats = [
            '|S128', '<M8[ns]',  # symbol, mtime
            '<M8[ns]', '|S32', '<M8[ns]', '<M8[ns]', '<M8[ns]', '<M8[ns]', '<M8[ns]', '<f8', '<i4',  # local fields
            '<i8', '<i8', '<i8', # mutex fields
            '<M8[ns]', '|S32', '<M8[ns]', '<M8[ns]', '<M8[ns]', '<M8[ns]', '<f8', '<i4', '|S32',  # remote fields 
            '|S32', '|S32', '|S16', '|S32', '|S32', '|S64', '|S32', '|S16',  # metadata fields
            '|S256', '|S128', '<i8', '<i4', '|S16' # schema fields
        ]

        computername = os.environ['COMPUTERNAME']
        self.schema = self.table('Symbols','D1','SCHEMA',computername,
            names=names,formats=formats,size=100e3)
            
    @staticmethod
    def mutex(shm_name, pid):        
        """
        Create or attach to a shared memory mutex object and register the process ID.
        
        This static method attempts to create a shared memory segment with a specific name
        appended by '#mutex' to serve as a mutex structure containing process ID, type, and load status.
        If the shared memory segment already exists, it attaches to it instead.
        
        It then acquires the mutex using the SharedData.acquire method, registers the calling process ID
        by appending it to a CSV file located in the DATABASE_FOLDER environment path, and returns
        the shared memory object, the mutex numpy structured array, and a flag indicating whether the
        shared memory was newly created or already existed.
        
        Parameters:
            shm_name (str): The base name of the shared memory segment.
            pid (int): The process ID to register and use for mutex acquisition.
        
        Returns:
            list: A list containing:
                - shm_mutex (shared_memory.SharedMemory): The shared memory object for the mutex.
                - mutex (numpy.ndarray): The numpy structured array representing the mutex.
                - ismalloc (bool): True if the shared memory was already existing (attached),
                                   False if it was newly created.
        """
        dtype_mutex = np.dtype({'names': ['pid', 'type', 'isloaded'],\
                                'formats': ['<i8', '<i8', '<i8']})
        try:
            shm_mutex = shared_memory.SharedMemory(
                name=shm_name + '#mutex', create=True, size=dtype_mutex.itemsize)
            ismalloc = False
        except:                                            
            shm_mutex = shared_memory.SharedMemory(
                name=shm_name + '#mutex', create=False)
            ismalloc = True        
        mutex = np.ndarray((1,), dtype=dtype_mutex,buffer=shm_mutex.buf)[0]        
        SharedData.acquire(mutex, pid, shm_name)        
        # register process id access to memory
        fpath = Path(os.environ['DATABASE_FOLDER'])
        fpath = fpath/('shm/'+shm_name.replace('\\', '/')+'#mutex.csv')
        os.makedirs(fpath.parent, exist_ok=True)
        with open(fpath, "a+") as f:
            f.write(str(pid)+',')
        return [shm_mutex, mutex, ismalloc]
    
    @staticmethod
    def acquire(mutex, pid, relpath):
        """
        Attempt to acquire a process-safe mutex semaphore by atomically setting its value to the current process ID (pid).
        
        This method uses a compare-and-swap atomic operation to acquire the mutex. If the mutex is already held by another process, it waits in a loop, checking every microsecond. If the mutex remains held beyond certain time thresholds (1 second on the first check, 15 seconds thereafter), it verifies whether the locking process is still active. If the locking process has terminated, it forcibly acquires the mutex. The method logs a warning if waiting for the semaphore continues beyond the initial timeout.
        
        Parameters:
            mutex (numpy structured array): The shared semaphore object with a 'pid' field and accessible via __array_interface__.
            pid (int): The process ID attempting to acquire the mutex.
            relpath (str): A string identifier (e.g., file path) used in logging messages.
        
        Returns:
            None
        """
        tini = time.time()
        # semaphore is process safe
        telapsed = 0
        hdrptr = mutex.__array_interface__['data'][0]
        semseek = 0
        firstcheck = True
        while cpp.long_compare_and_swap(hdrptr, semseek, 0, pid) == 0:
            # check if process that locked the mutex is still running
            telapsed = time.time() - tini
            if (telapsed > 15) | ((firstcheck) & (telapsed > 1)):
                lockingpid = mutex['pid']
                if not psutil.pid_exists(lockingpid):
                    if cpp.long_compare_and_swap(hdrptr, semseek, lockingpid, pid) != 0:
                        break
                if not firstcheck:
                    Logger.log.warning('%s waiting for semaphore...' % (relpath))
                tini = time.time()
                firstcheck = False
            time.sleep(0.000001)

    @staticmethod
    def release(mutex, pid, relpath):
        """
        Release a semaphore held by a specific process.
        
        This static method attempts to release the semaphore associated with the given mutex and process ID (pid). It uses an atomic compare-and-swap operation to ensure that the semaphore is only released if it is currently held by the specified pid. If the semaphore is not held by the pid, an error is logged and an exception is raised to indicate improper release.
        
        Parameters:
            mutex (object): The semaphore object, expected to have an underlying memory interface accessible via __array_interface__.
            pid (int): The process ID attempting to release the semaphore.
            relpath (str): A relative path or identifier string used for logging error messages.
        
        Raises:
            Exception: If the semaphore is released without being acquired by the given pid.
        """
        hdrptr = mutex.__array_interface__['data'][0]
        semseek = 0
        if cpp.long_compare_and_swap(hdrptr, semseek, pid, 0) != 1:
            errmsg = '%s Tried to release semaphore without acquire!' % (relpath)
            Logger.log.error(errmsg)
            raise Exception(errmsg)

    # TODO: check free memory before allocate    
    @staticmethod
    def malloc(shm_name, create=False, size=None):
        """
        Allocate or attach to a shared memory segment by name.
        
        Parameters:
            shm_name (str): The name of the shared memory segment.
            create (bool, optional): If True, create a new shared memory segment. Defaults to False.
            size (int, optional): The size of the shared memory segment to create. Required if create is True.
        
        Returns:
            list: A list containing:
                - shared_memory.SharedMemory: The shared memory object.
                - bool: True if the shared memory was attached (already existed), False if newly created.
        
        Raises:
            Exception: If create is True but size is not provided.
        
        Side Effects:
            Registers the current process ID by appending it to a CSV file located in the DATABASE_FOLDER environment path under 'shm/{shm_name}.csv'.
        """
        ismalloc = False
        shm = None
        if not create:
            try:
                shm = shared_memory.SharedMemory(
                    name=shm_name, create=False)
                ismalloc = True
            except:
                pass            
        elif (create) & (not size is None):
            try:
                shm = shared_memory.SharedMemory(
                    name=shm_name, create=True, size=size)                
                ismalloc = False
            except:                                            
                shm = shared_memory.SharedMemory(
                    name=shm_name, create=False)
                ismalloc = True
                
        elif (create) & (size is None):
            raise Exception(
                'SharedData malloc must have a size when create=True')
        
        # register process id access to memory
        fpath = Path(os.environ['DATABASE_FOLDER'])
        fpath = fpath/('shm/'+shm_name.replace('\\', '/')+'.csv')
        os.makedirs(fpath.parent, exist_ok=True)
        pid = os.getpid()
        with open(fpath, "a+") as f:
            f.write(str(pid)+',')

        return [shm, ismalloc]

    @staticmethod
    def free(shm_name):
        """
        Releases and cleans up a POSIX shared memory segment and its associated CSV file.
        
        Parameters:
            shm_name (str): The name of the shared memory segment to be freed.
        
        This method attempts to:
        1. Access the shared memory segment with the given name.
        2. Close and unlink (remove) the shared memory segment.
        3. Construct a file path based on the 'DATABASE_FOLDER' environment variable and the shared memory name.
        4. Remove the corresponding CSV file if it exists.
        
        If any step fails, the method silently ignores the exception.
        """
        if os.name == 'posix':
            try:
                shm = shared_memory.SharedMemory(
                    name=shm_name, create=False)
                shm.close()
                shm.unlink()
                fpath = Path(os.environ['DATABASE_FOLDER'])
                fpath = fpath/('shm/'+shm_name.replace('\\', '/')+'.csv')
                if fpath.is_file():
                    os.remove(fpath)
            except:
                pass

    @staticmethod
    def freeall():
        """
        Frees all shared memory segments tracked by SharedData.
        
        This static method obtains the list of shared memory segment names from SharedData.list_memory()
        and frees each segment by calling SharedData.free() on every name.
        """
        shm_names = SharedData.list_memory()
        for shm_name in shm_names.index:
            SharedData.free(shm_name)

    ######### LIST ############    
    def list_all(self, keyword='', user='master'):
                        
        """
        Retrieve and merge metadata listings from remote, local, and collection sources into a unified pandas DataFrame.
        
        This method fetches data filtered by an optional keyword and user identifier from three different sources:
        remote, local, and collections. It then merges these datasets, standardizes the columns, fills missing
        values with appropriate defaults, converts date columns to datetime objects, and adds a derived column
        'partitioning_period' based on the 'partition' column.
        
        Parameters:
            keyword (str): Optional keyword to filter the listings. Defaults to an empty string.
            user (str): User identifier to filter the listings. Defaults to 'master'.
        
        Returns:
            pandas.DataFrame: A DataFrame containing the merged and cleaned metadata with standardized columns,
            including local and remote folder info, timestamps, sizes, file counts, storage class, user info,
            database, period, source, container, tablename, partition, and a derived partitioning period.
        """
        dfremote = self.list_remote(keyword,user=user)

        dflocal = self.list_local(keyword,user=user)

        dfcollections = self.list_collections(keyword,user=user)
                        
        ls = dfremote.copy()
        # merge local
        ls = ls.reindex(index=ls.index.union(dflocal.index),
                        columns=ls.columns.union(dflocal.columns))
        ls.loc[dflocal.index,dflocal.columns] = dflocal.values
        # merge collections
        ls = ls.reindex(index=ls.index.union(dfcollections.index),
                        columns=ls.columns.union(dfcollections.columns))
        ls.loc[dfcollections.index,dfcollections.columns] = dfcollections.values

        if len(ls)>0:
            ls = ls.reindex(columns=['folder_local', 'created_local', 'last_modified_local','size_local','files_local',
                    'folder_remote', 'last_modified_remote', 'size_remote', 'files_remote','storage_class_remote',
                    'user','database','period','source','container', 'tablename','partition'])            
            ls['partitioning_period'] = ls['partition'].apply(lambda x: datetype(x))
            # fill nans local
            ls['folder_local'] = ls['folder_local'].fillna('')
            ls['created_local'] = pd.to_datetime(ls['created_local'])
                        
            # idx = ls['last_modified_local']>datetime.now(timezone.utc)
            # ls.loc[idx,'last_modified_local'] = datetime.now(timezone.utc)

            ls['last_modified_local'] = pd.to_datetime(ls['last_modified_local'])
            ls['size_local'] = ls['size_local'].fillna(0)
            ls['files_local'] = ls['files_local'].fillna(0)
            # fill nans remote
            ls['folder_remote'] = ls['folder_remote'].fillna('')
            ls['last_modified_remote'] = pd.to_datetime(ls['last_modified_remote'])            
            ls['size_remote'] = ls['size_remote'].fillna(0)
            ls['files_remote'] = ls['files_remote'].fillna(0)
            ls['storage_class_remote'] = ls['storage_class_remote'].fillna('')
            ls['user'] = ls['user'].fillna('')
            ls['database'] = ls['database'].fillna('')
            ls['period'] = ls['period'].fillna('')
            ls['source'] = ls['source'].fillna('')
            ls['container'] = ls['container'].fillna('')
            ls['tablename'] = ls['tablename'].fillna('')
            ls['partition'] = ls['partition'].fillna('')
            ls['partitioning_period' ]= ls['partitioning_period'].fillna('')
            ls.sort_index(inplace=True)

        return ls
    
    def list_remote(self, keyword='', user='master'):
        """
        List and summarize remote S3 objects filtered by a keyword and user prefix.
        
        Connects to an S3 bucket, retrieves objects with keys starting with the specified user and keyword prefix,
        and compiles their metadata into a pandas DataFrame. The DataFrame includes detailed path parsing to extract
        user, database, period, source, container, tablename, and partition information. Special handling is applied
        for metadata and timeseries files. The resulting DataFrame is grouped by path, aggregating file counts,
        sizes, and modification dates.
        
        Parameters:
            keyword (str): Optional keyword to filter S3 object keys (default is '').
            user (str): User prefix to filter S3 object keys (default is 'master').
        
        Returns:
            pandas.DataFrame: Aggregated metadata of remote S3 objects grouped by path, including columns:
                - folder_remote: S3 bucket URL
                - last_modified_remote: Latest modification timestamp
                - size_remote: Total size of files in bytes
                - storage_class_remote: Storage class of the objects
                - user, database, period, source, container, tablename, partition: Parsed path components
                - files_remote: Number of files in the path
        """
        mdprefix = user+'/'+keyword        
        # list_remote
        s3, bucket = S3GetSession()
        arrobj = np.array([[obj.key , obj.last_modified, obj.size, obj.storage_class]
                    for obj in bucket.objects.filter(Prefix=mdprefix)])
        dfremote = pd.DataFrame()
        if arrobj.size>0:
            dfremote = pd.DataFrame(
                arrobj, 
                columns=['full_path','last_modified_remote','size_remote','storage_class_remote']
            )    
            dfremote['path'] = dfremote['full_path'].apply(lambda x: str(Path(x).parent))
            dfremote['filename_remote'] = dfremote['full_path'].apply(lambda x: str(Path(x).name))    
            dfremote['folder_remote'] = 's3://'+bucket.name        
            dfremote['size_remote'] = dfremote['size_remote'].astype(np.int64)    
            dfremote['user'] = dfremote['path'].apply(lambda x: x.split(os.sep)[0])
            dfremote['database'] = dfremote['path'].apply(lambda x: x.split(os.sep)[1])    
            dfremote['period'] = dfremote['path'].apply(lambda x: x.split(os.sep)[2] if len(x.split(os.sep))>2 else '')
            dfremote['source'] = dfremote['path'].apply(lambda x: x.split(os.sep)[3] if len(x.split(os.sep))>3 else '')
            dfremote['container'] = dfremote['path'].apply(lambda x: x.split(os.sep)[4] if len(x.split(os.sep))>4 else '')        
            dfremote['tablename'] = dfremote['path'].apply(lambda x: '/'.join(x.split(os.sep)[5:]) if len(x.split(os.sep))>5 else '')
            dfremote['partition'] = dfremote['tablename'].apply(lambda x: x.split('/')[1] if '/' in x else '')
            dfremote['tablename'] = dfremote['tablename'].apply(lambda x: x.split('/')[0])        
            dfremote['files_remote'] = 1
            # change path for metadata
            metadataidx = dfremote['database' ]=='Metadata'
            dfremote.loc[metadataidx,'path'] = dfremote.loc[metadataidx,'full_path'].apply(lambda x: x.rstrip('.bin.gzip'))        
            dfremote.loc[metadataidx,'container'] = 'metadata'
            dfremote.loc[metadataidx,'period'] = ''
            dfremote.loc[metadataidx,'source'] = ''
            dfremote.loc[metadataidx,'tablename'] = ''
            dfremote.loc[metadataidx,'partition'] = ''
            # change path for timeseries
            timeseriesidx = dfremote['filename_remote'].apply(lambda x: x.startswith('timeseries_'))
            dfremote.loc[timeseriesidx,'container'] = 'timeseries'
            # group by path
            dfremote = dfremote.groupby('path').agg(
                    {               
                        'folder_remote':'first',
                        'last_modified_remote':'max',
                        'size_remote':'sum',                
                        'storage_class_remote':'first',                
                        'user':'first',
                        'database':'first',
                        'period':'first',
                        'source':'first',
                        'container':'first',
                        'tablename':'first',
                        'partition':'first',
                        'files_remote':'sum'
                    }
                )
            
        return dfremote
    
    def list_local(self, keyword='', user='master'):
        """
        Scan local database directories for binary files matching the specified user and keyword, and return a summarized pandas DataFrame with metadata.
        
        Parameters:
            keyword (str): Optional keyword to filter the search path. Defaults to an empty string.
            user (str): User name to filter the search path. Defaults to 'master'.
        
        Returns:
            pd.DataFrame: A DataFrame containing aggregated information about the found binary files, including file paths, creation and modification times (in UTC), sizes, and parsed path components such as user, database, period, source, container, tablename, and partition. The DataFrame groups files by their path and summarizes file counts and sizes.
        """
        mdprefix = user+'/'+keyword
        dflocal = pd.DataFrame()
        records = []
        for dbfolder in self.dbfolders:
            localpath = Path(dbfolder) / Path(mdprefix)    
            for root, dirs, files in os.walk(localpath):
                for name in files:
                    if name.endswith((".bin")):
                        full_path = os.path.join(root, name)
                        modified_time_local = datetime.fromtimestamp(os.path.getmtime(full_path)).astimezone(timezone.utc)
                        created_time_local = datetime.fromtimestamp(os.path.getctime(full_path)).astimezone(timezone.utc)
                        size = np.int64(os.path.getsize(full_path))
                        records.append({
                            'full_path': full_path,
                            'path': root.replace(dbfolder,'').replace('\\','/').rstrip('/').lstrip('/'),
                            'filename_local': name,
                            'folder_local' : dbfolder,
                            'created_local' : created_time_local,
                            'last_modified_local': modified_time_local,
                            'size_local': size
                        })
        if len(records)>0:
            dflocal = pd.DataFrame(records)
            dflocal['user'] = dflocal['path'].apply(lambda x: x.split(os.sep)[0])            
            dflocal['database'] = dflocal['path'].apply(lambda x: x.split(os.sep)[1])
            dflocal['period'] = dflocal['path'].apply(lambda x: x.split(os.sep)[2] if len(x.split(os.sep))>2 else '')
            dflocal['source'] = dflocal['path'].apply(lambda x: x.split(os.sep)[3] if len(x.split(os.sep))>3 else '')
            dflocal['container'] = dflocal['path'].apply(lambda x: x.split(os.sep)[4] if len(x.split(os.sep))>4 else '')
            dflocal['tablename'] = dflocal['path'].apply(lambda x: '/'.join(x.split(os.sep)[5:]) if len(x.split(os.sep))>5 else '')
            dflocal['partition'] = dflocal['tablename'].apply(lambda x: x.split('/')[1] if '/' in x else '')
            dflocal['tablename'] = dflocal['tablename'].apply(lambda x: x.split('/')[0])        
            dflocal['files_local'] = 1
            # change path for metadata
            metadataidx = dflocal['database' ]=='Metadata'
            dflocal.loc[metadataidx,'path'] += '/'+dflocal.loc[metadataidx,'filename_local'].apply(lambda x: x.rstrip('.bin'))
            dflocal.loc[metadataidx,'container'] = 'metadata'
            dflocal.loc[metadataidx,'period'] = ''
            dflocal.loc[metadataidx,'source'] = ''
            dflocal.loc[metadataidx,'tablename'] = ''
            dflocal.loc[metadataidx,'partition'] = ''
            # change path for timeseries
            timeseriesidx = dflocal['container']=='timeseries'
            dflocal.loc[timeseriesidx,'path'] += '/'+dflocal.loc[timeseriesidx,'filename_local'].apply(lambda x: x.rstrip('.bin'))    
            dflocal = dflocal.groupby('path').agg(
                    {               
                        'folder_local':'first',
                        'created_local':'min',
                        'last_modified_local':'max',
                        'size_local':'sum',
                        'user':'first',
                        'database':'first',
                        'period':'first',
                        'source':'first',
                        'container':'first',
                        'tablename':'first',
                        'partition':'first',
                        'files_local':'sum'
                    }
                )    
                                
        return dflocal
    
    def list_tables(self, keyword='', user='master'):
                        
        """
        Retrieve and merge table metadata from remote and local sources filtered by keyword and user.
        
        This method fetches listings from both remote and local sources, merges them into a single DataFrame,
        standardizes column order, fills missing values, converts date columns to datetime, and filters the
        results to include only entries where the container type is 'table'. It also computes a 'partitioning_period'
        column based on the 'partition' column.
        
        Parameters:
            keyword (str): Optional keyword to filter the listings. Defaults to an empty string.
            user (str): User identifier to filter the listings. Defaults to 'master'.
        
        Returns:
            pandas.DataFrame: A cleaned and merged DataFrame containing metadata for tables from remote and local sources.
        """
        dfremote = self.list_remote(keyword,user=user)

        dflocal = self.list_local(keyword,user=user)        
                        
        ls = dfremote.copy()
        # merge local
        ls = ls.reindex(index=ls.index.union(dflocal.index),
                        columns=ls.columns.union(dflocal.columns))
        ls.loc[dflocal.index,dflocal.columns] = dflocal.values
        
        if len(ls)>0:
            ls = ls.reindex(columns=['folder_local', 'created_local', 'last_modified_local','size_local','files_local',
                    'folder_remote', 'last_modified_remote', 'size_remote', 'files_remote','storage_class_remote',
                    'user','database','period','source','container', 'tablename','partition'])            
            ls['partitioning_period'] = ls['partition'].apply(lambda x: datetype(x))
            # fill nans local
            ls['folder_local'] = ls['folder_local'].fillna('')
            ls['created_local'] = pd.to_datetime(ls['created_local'])
                        
            # idx = ls['last_modified_local']>datetime.now(timezone.utc)
            # ls.loc[idx,'last_modified_local'] = datetime.now(timezone.utc)

            ls['last_modified_local'] = pd.to_datetime(ls['last_modified_local'])
            ls['size_local'] = ls['size_local'].fillna(0)
            ls['files_local'] = ls['files_local'].fillna(0)
            # fill nans remote
            ls['folder_remote'] = ls['folder_remote'].fillna('')
            ls['last_modified_remote'] = pd.to_datetime(ls['last_modified_remote'])            
            ls['size_remote'] = ls['size_remote'].fillna(0)
            ls['files_remote'] = ls['files_remote'].fillna(0)
            ls['storage_class_remote'] = ls['storage_class_remote'].fillna('')
            ls['user'] = ls['user'].fillna('')
            ls['database'] = ls['database'].fillna('')
            ls['period'] = ls['period'].fillna('')
            ls['source'] = ls['source'].fillna('')
            ls['container'] = ls['container'].fillna('')
            ls['tablename'] = ls['tablename'].fillna('')
            ls['partition'] = ls['partition'].fillna('')
            ls['partitioning_period' ]= ls['partitioning_period'].fillna('')
            ls.sort_index(inplace=True)
            ls = ls[ls['container']=='table']

        return ls

    def list_timeseries(self, keyword='', user='master'):
        """
        Retrieve and merge timeseries metadata from remote and local sources into a single cleaned DataFrame.
        
        This method fetches listings filtered by an optional keyword and user identifier from both remote and local data sources,
        merges them to create a unified view, standardizes column order, fills missing values with appropriate defaults,
        converts date columns to datetime objects, and filters the results to include only entries classified as timeseries containers.
        
        Parameters:
            keyword (str): Optional keyword to filter the timeseries listings. Defaults to an empty string.
            user (str): User identifier to filter the listings. Defaults to 'master'.
        
        Returns:
            pandas.DataFrame: A DataFrame containing merged, cleaned, and filtered metadata for timeseries data,
            with standardized columns and appropriate data types.
        """
        dfremote = self.list_remote(keyword, user=user)
        dflocal = self.list_local(keyword, user=user)        
                        
        ls = dfremote.copy()
        # merge local
        ls = ls.reindex(index=ls.index.union(dflocal.index),
                        columns=ls.columns.union(dflocal.columns))
        ls.loc[dflocal.index, dflocal.columns] = dflocal.values
        
        if len(ls) > 0:
            ls = ls.reindex(columns=['folder_local', 'created_local', 'last_modified_local','size_local','files_local',
                    'folder_remote', 'last_modified_remote', 'size_remote', 'files_remote','storage_class_remote',
                    'user','database','period','source','container', 'tablename','partition'])            
            ls['partitioning_period'] = ls['partition'].apply(lambda x: datetype(x))
            # fill nans local
            ls['folder_local'] = ls['folder_local'].fillna('')
            ls['created_local'] = pd.to_datetime(ls['created_local'])
                        
            ls['last_modified_local'] = pd.to_datetime(ls['last_modified_local'])
            ls['size_local'] = ls['size_local'].fillna(0)
            ls['files_local'] = ls['files_local'].fillna(0)
            # fill nans remote
            ls['folder_remote'] = ls['folder_remote'].fillna('')
            ls['last_modified_remote'] = pd.to_datetime(ls['last_modified_remote'])            
            ls['size_remote'] = ls['size_remote'].fillna(0)
            ls['files_remote'] = ls['files_remote'].fillna(0)
            ls['storage_class_remote'] = ls['storage_class_remote'].fillna('')
            ls['user'] = ls['user'].fillna('')
            ls['database'] = ls['database'].fillna('')
            ls['period'] = ls['period'].fillna('')
            ls['source'] = ls['source'].fillna('')
            ls['container'] = ls['container'].fillna('')
            ls['tablename'] = ls['tablename'].fillna('')
            ls['partition'] = ls['partition'].fillna('')
            ls['partitioning_period'] = ls['partitioning_period'].fillna('')
            ls.sort_index(inplace=True)
            ls = ls[ls['container']=='timeseries']

        return ls
    
    def list_collections(self, keyword='', user='master'):        
        """
        Retrieve and return a DataFrame containing metadata about MongoDB collections for a specified user, filtered by an optional keyword prefix.
        
        Parameters:
            keyword (str): Optional prefix to filter collection names. Defaults to an empty string (no filtering).
            user (str): The MongoDB user/database name to query collections from. Defaults to 'master'.
        
        Returns:
            pd.DataFrame: A DataFrame indexed by collection path with columns:
                - size_remote: Total size of the collection in bytes.
                - container: The container type, extracted from the collection path or set as 'collection'.
                - storage_class_remote: Storage class, fixed as 'mongodb'.
                - user: Extracted user from the collection path.
                - database: Extracted database from the collection path.
                - period: Extracted period segment from the collection path if present, else empty string.
                - source: Extracted source segment from the collection path if present, else empty string.
                - tablename: Extracted table name from the collection path.
                - partition: Extracted partition from the tablename if present, else empty string.
        
        If no collections match the keyword, returns an empty DataFrame.
        """
        collections = self.mongodb.client[user].list_collection_names()
        collections = [s for s in collections if s.startswith(keyword)]
        if len(collections)==0:
            return pd.DataFrame()
        
        collection_size = []
        for icollection,collection in enumerate(collections):
            stats = self.mongodb.client[user].command("collStats", collection)
            collection_size.append(stats['totalSize'])

        collections_path = [user+'/'+s for s in collections]
        dfcollections = pd.DataFrame(collections_path,columns=['path'])
        dfcollections['size_remote'] = collection_size
        dfcollections['container'] = 'collection'
        dfcollections['storage_class_remote'] = 'mongodb'
        dfcollections['user'] = dfcollections['path'].apply(lambda x: x.split(os.sep)[0])
        dfcollections['database'] = dfcollections['path'].apply(lambda x: x.split(os.sep)[1])
        dfcollections['period'] = dfcollections['path'].apply(lambda x: x.split(os.sep)[2] if len(x.split(os.sep))>2 else '')
        dfcollections['source'] = dfcollections['path'].apply(lambda x: x.split(os.sep)[3] if len(x.split(os.sep))>3 else '')
        dfcollections['container'] = dfcollections['path'].apply(lambda x: x.split(os.sep)[4] if len(x.split(os.sep))>4 else '')
        dfcollections['tablename'] = dfcollections['path'].apply(lambda x: '/'.join(x.split(os.sep)[5:]) if len(x.split(os.sep))>5 else '')
        dfcollections['partition'] = dfcollections['tablename'].apply(lambda x: x.split('/')[1] if '/' in x else '')
        dfcollections['tablename'] = dfcollections['tablename'].apply(lambda x: x.split('/')[0])
        dfcollections.set_index('path',inplace=True)
        dfcollections.sort_index(inplace=True)
        
        return dfcollections

    def list_disks(self):
        """
        Calculate and return disk usage statistics for each directory in self.dbfolders.
        
        For each directory, ensures it exists by creating it if necessary, then retrieves
        disk usage information including total, used, and free space in gigabytes, as well
        as the percentage of used space. The results are compiled into a pandas DataFrame,
        sorted by the percentage of disk space used in ascending order.
        
        Returns:
            pandas.DataFrame: A DataFrame indexed by directory paths with columns:
                - total (int): Total disk space in GB.
                - used (int): Used disk space in GB.
                - free (int): Free disk space in GB.
                - percent_used (float): Percentage of disk space used.
        """
        disk_usage = {}
        for directory in self.dbfolders:
            if not os.path.exists(directory):
                Path(directory).mkdir(parents=True, exist_ok=True)
            # Get disk usage statistics
            os.sync()
            time.sleep(0.001)
            total, used, free = shutil.disk_usage(directory)            
            disk_usage[directory] = {
                "total": total // (2**30),  # Convert bytes to GB
                "used": used // (2**30),
                "free": free // (2**30),
                "percent_used": (used / total) * 100,
            }
        dfdisks = pd.DataFrame(disk_usage).T
        dfdisks.sort_values('percent_used', inplace=True)
        return dfdisks

    def list_streams(self, keyword='', user='master'):
        """
        '''
        List and summarize Kafka streams and their consumer groups from the Kafka cluster.
        
        Parameters:
            keyword (str): Optional keyword to filter the stream names. Defaults to an empty string.
            user (str): User name to filter the stream names. Defaults to 'master'.
        
        Returns:
            tuple: A tuple containing two dictionaries:
                - streams (dict): Metadata about Kafka topics (streams), keyed by stream path. Each entry includes:
                    - path (str): Stream path derived from the topic name.
                    - topic (str): Kafka topic name.
                    - num_partitions (int): Number of partitions in the topic.
                    - partitions (dict): Information per partition, including earliest and latest offsets and message counts.
                    - replication_factor (int): Minimum replication factor across partitions.
                    - total_messages (int): Total number of messages across all partitions.
                    - consumer_groups (dict, optional): Consumer group information consuming from this stream.
                - consumer_groups (dict): Information about consumer groups in the Kafka cluster, keyed by group ID. Each entry includes:
                    - group_id (str): Consumer group identifier.
                    - state (str): Current state of the consumer group.
                    - coordinator (str): Host and port of the group's coordinator.
                    - members
        """
        from confluent_kafka.admin import AdminClient, NewTopic,OffsetSpec
        from confluent_kafka import Consumer, KafkaError, TopicPartition, Producer
        from confluent_kafka import KafkaException
        
        bootstrap_servers = os.environ['KAFKA_BOOTSTRAP_SERVERS']
        admin = AdminClient({'bootstrap.servers': bootstrap_servers})
        topics = admin.list_topics().topics

                
        streams = {}
        for topic in topics:
            if topic.startswith('__'):
                continue
            stream = {}
            stream['path'] = topic.replace('-', '/')
            stream['topic'] = topic
            # get number of partitions    
            stream['partitions'] = {}
            stream['num_partitions'] = len(topics[topic].partitions)    
            for pid in list(topics[topic].partitions.keys()):
                stream['partitions'][pid] = {}        
            stream['replication_factor'] = min(
                len(p.replicas) for p in topics[topic].partitions.values()
            )        
            
            
            partition_ids = list(stream['partitions'].keys())
            # Create a dictionary of TopicPartition objects for earliest and latest offsets
            topic_partitions_earliest = {TopicPartition(topic, pid): OffsetSpec.earliest() for pid in partition_ids}
            topic_partitions_latest = {TopicPartition(topic, pid): OffsetSpec.latest() for pid in partition_ids}
            
            # Get earliest offsets
            earliest_future = admin.list_offsets(topic_partitions_earliest)    
            for tp in topic_partitions_earliest.keys():
                part = stream['partitions'][tp.partition]
                try:
                    result = earliest_future[tp].result()            
                    part['earliest_offset'] = result.offset if result.offset is not None else 0            
                except KafkaException as e:
                    print(f"Error getting earliest offset for {topic} partition {tp.partition}: {str(e)}")
                    part['earliest_offset'] = 0
            
            # Get latest offsets
            latest_future = admin.list_offsets(topic_partitions_latest)    
            for tp in topic_partitions_latest.keys():
                part = stream['partitions'][tp.partition]
                try:
                    result = latest_future[tp].result()
                    part['latest_offset'] = result.offset if result.offset is not None else 0
                except KafkaException as e:
                    print(f"Error getting latest offset for {topic} partition {tp.partition}: {str(e)}")
                    part['latest_offset'] = 0
            
            # Calculate total messages per partition
            total_messages = 0
            for pid in partition_ids:
                part = stream['partitions'][pid]
                earliest = part.get('earliest_offset', 0)
                latest = part.get('latest_offset', 0)
                messages = max(0, latest - earliest)  # Ensure non-negative count
                total_messages += messages
                part['num_messages'] = messages
            
            stream['total_messages'] = total_messages
            streams[stream['path']] = stream


        # Get future for consumer groups listing

        # Get list of consumer groups
        consumer_groups = {}
        consumer_groups_future = admin.list_consumer_groups()
        consumer_groups_result = consumer_groups_future.result()  # Wait for result

        # Get all group IDs
        group_ids = [group.group_id for group in consumer_groups_result.valid]

        if group_ids:
            # Describe all consumer groups in a single batch
            group_desc_future = admin.describe_consumer_groups(group_ids)
            
            # Iterate through all consumer groups
            for group in consumer_groups_result.valid:        
                # Access the future for the specific group_id from the dictionary
                group_future = group_desc_future[group.group_id]
                group_info = group_future.result()  # Wait for the result of this specific group
                
                # Collect basic information about the consumer group
                group_data = {
                    'group_id': group.group_id,
                    'state': group_info.state.name if hasattr(group_info.state, 'name') else str(group_info.state),
                    'coordinator': f"{group_info.coordinator.host}:{group_info.coordinator.port}" if group_info.coordinator else "N/A",
                    'members': len(group_info.members)
                }
                
                # Add member-specific information
                group_data['members'] = {}
                for i, member in enumerate(group_info.members):
                    m = group_data['members'][member.member_id] = {}
                    m['member_id'] = member.member_id
                    m['host'] = member.host
                    m['client_id'] = member.client_id
                    
                    # Add assignment information if available
                    if hasattr(member, 'assignment') and member.assignment is not None:
                        assignments = member.assignment.topic_partitions if hasattr(member.assignment, 'topic_partitions') else member.assignment
                        try:
                            for topic_partition in assignments:
                                m[topic_partition.topic] = topic_partition.partition
                                path = topic_partition.topic.replace('-', '/')
                                if 'consumer_groups' not in streams[path]:
                                    streams[path]['consumer_groups'] = {}
                                streams[path]['consumer_groups'][group.group_id] = group_data
                        except TypeError:
                            # If assignments is not iterable, skip or handle differently
                            pass
                        
                consumer_groups[group.group_id] = group_data
        
        return streams, consumer_groups
        
    @staticmethod
    def list_memory():
        """
        Scans the shared memory directory specified by the 'DATABASE_FOLDER' environment variable to identify active shared memory segments.
        
        For each CSV file found in the 'shm' subdirectory, attempts to connect to the corresponding shared memory segment by name. If successful, records the segment's size in a DataFrame indexed by the segment name. If the shared memory segment does not exist but the CSV file remains, attempts to remove the stale file.
        
        Returns:
            pd.DataFrame: A DataFrame indexed by shared memory segment names with a single column 'size' indicating the size of each segment in bytes. The DataFrame is sorted by the segment names.
        """
        folder = Path(os.environ['DATABASE_FOLDER'])/'shm'
        shm_names = pd.DataFrame()
        for root, _, filepaths in os.walk(folder):
            for filepath in filepaths:
                if filepath.endswith('.csv'):
                    fpath = os.path.join(root, filepath)
                    shm_name = fpath.removeprefix(str(folder))[1:]
                    shm_name = shm_name.removesuffix('.csv')
                    if os.name == 'posix':
                        shm_name = shm_name.replace('/', '\\')
                    elif os.name == 'nt':
                        shm_name = shm_name.replace('\\', '/')
                    try:
                        shm = shared_memory.SharedMemory(
                            name=shm_name, create=False)
                        shm_names.loc[shm_name, 'size'] = shm.size
                        shm.close()
                    except:
                        try:
                            if fpath.is_file():
                                os.remove(fpath)
                        except:
                            pass
        shm_names = shm_names.sort_index()
        return shm_names
      
    ######### LOAD ############    

    def load_table(self,table,args, user='master'):    
        """
        Load metadata information for a specified table.
        
        Parameters:
            table (object): An object containing table metadata with attributes such as 'name', 'tablename', 'partition', 'database', 'period', and 'source'.
            args (any): Additional arguments (currently unused).
            user (str, optional): Username for accessing the table. Defaults to 'master'.
        
        Returns:
            dict: A dictionary containing metadata about the table including:
                - 'path': The table's name.
                - 'hasindex': Boolean indicating if the table has an index.
                - 'mtime': Last modification time as a pandas Timestamp.
                - 'size': Total size of the table in bytes.
                - 'count': Number of records in the table.
                - 'recordssize': Number of records.
                - 'itemsize': Size of each record item in bytes.
                - 'names': Comma-separated string of field names.
                - 'formats': Comma-separated string of field data types.
        
        Logs an error if loading the table metadata fails.
        """
        result = {}
        result['path'] = table.name        
        try:
            if table['partition']!= '':
                tablename = table['tablename'] + '/' + table['partition']
            else:
                tablename = table['tablename']
                    
            tbl = self.table(table['database'],table['period'],table['source'],tablename, user=user)
            result['hasindex'] = tbl.table.hdr['hasindex']
            result['mtime'] = pd.Timestamp.fromtimestamp(tbl.mtime)
            result['size'] = tbl.recordssize*tbl.dtype.itemsize
            result['count'] = tbl.count
            result['recordssize'] = tbl.recordssize
            result['itemsize'] = tbl.dtype.itemsize
            result['names'] = ','.join([s[0] for s in tbl.dtype.descr])
            result['formats'] = ','.join([s[1] for s in tbl.dtype.descr])
            tbl.free()            
        except Exception as e:
            Logger.log.error(f'Loading {table.name} Error: {e}')                    
        
        return result
    
    def load_tables(self, tables, maxproc=8):
        """
        Loads data for specified tables concurrently and updates the tables DataFrame with the loaded data.
        
        Filters the input DataFrame to include only rows where the 'container' column equals 'table'. Uses a concurrent IO-bound function to load each table's data with a maximum number of parallel processes specified by maxproc. Successfully loaded results are converted into a DataFrame and used to update the original tables DataFrame in place. Logs the progress and any errors encountered during the loading process.
        
        Parameters:
            tables (pd.DataFrame): DataFrame containing table metadata, must include a 'container' column.
            maxproc (int, optional): Maximum number of concurrent processes to use for loading tables. Defaults to 8.
        
        Returns:
            bool: True if tables were loaded successfully, False otherwise.
        """
        try:
            tables = tables[tables['container']=='table']
            Logger.log.info('Loading tables...')
            results = io_bound_unordered(self.load_table,tables,[],maxproc=maxproc)
            Logger.log.info('Tables loaded!')              
            results = [r for r in results if r != -1]
            if len(results)>0:
                df = pd.DataFrame(results).set_index('path')
                tables.loc[df.index,df.columns] = df.values
            return True
        except Exception as e:
            Logger.log.error(f'load_tables error {e}')
        return False

    def load_db(self, database, user='master',maxproc=8):
        """
        Load all tables from a specified database for a given user.
        
        This method retrieves a list of all tables in the specified database and user context,
        filters to include only actual tables (excluding other container types), and then loads
        these tables using a parallel processing approach with a maximum number of processes.
        
        Parameters:
            database (str): The name of the database to load tables from.
            user (str, optional): The user context under which to list and load tables. Defaults to 'master'.
            maxproc (int, optional): The maximum number of parallel processes to use when loading tables. Defaults to 8.
        
        Returns:
            bool: True if tables were loaded successfully, False otherwise.
        
        Logs:
            Info-level log when starting to load tables.
            Error-level log if an exception occurs during the loading process.
        """
        try:
            tables = self.list_all(database, user)
            tables = tables[tables['container']=='table']
            Logger.log.info('Loading tables...')
            self.load_tables(tables, maxproc=maxproc)
            return True
        except Exception as e:
            Logger.log.error(f'load_db error {e}')        
        return False

    ######### DELETE ############
    
    def delete_table(self, database, period, source, tablename, user='master', localonly=False):
        """
        Deletes a specified table from the internal data structure, local filesystem, and remote storage.
        
        Parameters:
            database (str): The name of the database containing the table.
            period (str): The period identifier for the table.
            source (str): The data source of the table.
            tablename (str): The name of the table to delete.
            user (str, optional): The user namespace under which the table exists. Defaults to 'master'.
        
        Returns:
            bool: True if the table was successfully deleted, False otherwise.
        
        The method performs the following steps:
        - Constructs the path to the table based on the provided parameters.
        - Removes the table data from the internal dictionary if it exists.
        - Checks the schema for the table and deletes associated local files if present.
        - Removes the local folder if it becomes empty after file deletion.
        - Calls an external function `S3DeleteTable` to delete the table from remote storage.
        - Logs any errors encountered during the deletion process.
        """
        success = False
        try:
            path = f'{user}/{database}/{period}/{source}/table/{tablename}'
            # raise NotImplementedError(f'Delete {path} not implemented')
            if path in self.data.keys():
                self.data[path].free()
                # del self.data[path]

            if self.schema is None:
                self.init_schema()
            
            delfiles = ['data.bin','bson.bin','dateidx.bin','pkey.bin','symbolidx.bin','portidx.bin']

            buff = np.full((1,),np.nan,dtype=self.schema.dtype)
            buff['symbol'] = path.replace('\\', '/')
            loc = self.schema.get_loc(buff,acquire=False)
            if loc[0] != -1: # table exists
                folder_local = self.schema[loc[0]]['folder_local']
                database_folder = folder_local.decode('utf-8')
                localpath = Path(database_folder) / path
                if localpath.exists():
                    
                    for file in delfiles:
                        delpath = Path(localpath/file)
                        if delpath.exists():
                            os.remove(delpath)
                # if folder is empty remove it
                if localpath.exists():
                    if not any(localpath.iterdir()):
                        shutil.rmtree(localpath)
            else:           
                database_folder = os.environ['DATABASE_FOLDER']     
                # select the first disk with less percent_used
                if len(self.dbfolders) > 1:
                    # scan folders to check if table is already initialized
                    for f in self.dbfolders:
                        localpath = Path(database_folder) / path / 'data.bin'
                        if localpath.is_file():
                            database_folder = f
                            break
                localpath = Path(database_folder) / path
                if localpath.exists():                    
                    for file in delfiles:
                        delpath = Path(localpath/file)
                        if delpath.exists():
                            os.remove(delpath)
                    # if folder is empty remove it
                    if not any(localpath.iterdir()):
                        shutil.rmtree(localpath)
                
            if not localonly:
                S3DeleteTable(path)

            success = True
            
        except Exception as e:
            Logger.log.error(f'Delete {path} Error: {e}')
        finally:
            pass

        return success
        
    def delete_timeseries(self, database, period, source, 
                          tag=None, user='master', localonly=False):
        """
        Deletes a timeseries or a specific tag within a timeseries from the data store.
        
        Parameters:
            database (str): The name of the database.
            period (str): The time period identifier.
            source (str): The source identifier.
            tag (str, optional): The specific tag within the timeseries to delete. If None, deletes the entire timeseries container.
            user (str, optional): The user performing the deletion. Defaults to 'master'.
        
        Returns:
            bool: True if the deletion was successful, False otherwise.
        
        Behavior:
            - If `tag` is None, deletes the entire timeseries container from the in-memory data dictionary, local filesystem, and S3 storage.
            - If `tag` is specified, deletes only the specified tag from the timeseries, removes associated files, and updates the in-memory data.
            - Logs an error and returns False if any exception occurs during the deletion process.
        """
        try:            
            path = f'{user}/{database}/{period}/{source}/timeseries'
            if tag is None:
                # delete timeseries container
                if path in self.data.keys():
                    del self.data[path]                
                localpath = Path(os.environ['DATABASE_FOLDER'])/Path(path)
                if localpath.exists():
                    shutil.rmtree(localpath)
                files_del = ['timeseries_head.bin','timeseries_tail.bin']
                for file in files_del:
                    delpath = Path(localpath.parent/file)
                    if delpath.exists():
                        os.remove(delpath)
                if not localonly:
                    S3DeleteTimeseries(path.replace('/timeseries',''))
                return True
            else:                
                # delete timeseries tag
                ts = self.timeseries(database,period,source,tag,user=user)
                tstag = self.data[path].tags[tag]
                fpath, shm_name = tstag.get_path()
                del self.data[path].tags[tag]
                del ts
                os.remove(fpath)
                return True
            
        except Exception as e:
            Logger.log.error(f'Delete {path}/{tag} Error: {e}')
            return False    
        
    def delete_collection(self, database, period, source, tablename, user='master'):
        """
        Deletes a specified collection from the database and removes its reference from the internal data cache.
        
        Parameters:
            database (str): The name of the database.
            period (str): The period identifier.
            source (str): The source identifier.
            tablename (str): The name of the collection/table to delete.
            user (str, optional): The user context under which the operation is performed. Defaults to 'master'.
        
        Returns:
            bool: True if the collection was successfully deleted, False otherwise.
        
        Notes:
            - The method constructs a path key based on the input parameters to locate and delete the collection.
            - If the collection exists in the internal data cache (`self.data`), it is also removed.
            - Any exceptions during deletion are logged and result in a False return value.
        """
        try:
            path = f'{user}/{database}/{period}/{source}/collection/{tablename}'
            collection = self.collection(database,period,source,tablename,user=user)
            collection._collection.drop()
            if path in self.data.keys():
                del self.data[path]
            del collection
            return True
        except Exception as e:
            Logger.log.error(f'Delete {path} Error: {e}')
            return False

    def delete_stream(self, database, period, source, tablename, user='master'):
        """
        Deletes a data stream specified by database, period, source, and tablename.
        
        Parameters:
            database (str): The name of the database.
            period (str): The time period identifier.
            source (str): The data source name.
            tablename (str): The name of the table/stream to delete.
            user (str, optional): The user context under which to perform the deletion. Defaults to 'master'.
        
        Returns:
            bool: True if the stream was successfully deleted, False otherwise.
        
        This method attempts to retrieve the stream without creating it if it does not exist,
        then deletes it and removes its reference from the internal data dictionary if present.
        Logs any errors encountered during deletion except for FileNotFoundError, which is silently ignored.
        """
        path = f'{user}/{database}/{period}/{source}/stream/{tablename}'
        try:
            stream = self.stream(database,period,source,tablename,user=user,create_if_not_exists=False)
            stream.delete()
            if path in self.data.keys():
                del self.data[path]
            del stream
            return True
        except FileNotFoundError as e:
            pass
        except Exception as e:
            Logger.log.error(f'Delete {path} Error: {e}')
        return False


    ############# MONGODB #############
    # Getter for db
    @property
    def mongodb(self):
        """
        Lazily initializes and returns a MongoDBClient instance.
        
        If the MongoDB client has not been created yet, it initializes a new MongoDBClient
        and stores it in the instance variable `_mongodb`. Subsequent accesses return the
        already initialized client.
        
        Returns:
            MongoDBClient: An instance of the MongoDB client.
        """
        if self._mongodb is None:
            self._mongodb = MongoDBClient()
        return self._mongodb