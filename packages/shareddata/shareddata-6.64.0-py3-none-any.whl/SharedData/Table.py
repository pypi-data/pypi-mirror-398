import os
import threading
import time
import pandas as pd
import numpy as np
from pathlib import Path
from multiprocessing import shared_memory
import gzip
import io
import hashlib
from datetime import datetime
from tqdm import tqdm
import threading
import psutil
import traceback
import asyncio
import importlib
import bson
import mmap

from SharedData.Logger import Logger
from SharedData.IO.AWSS3 import S3Upload, S3Download, S3ListFolder, S3GetMtime, S3DeleteFile, UpdateModTime
from SharedData.TableIndex import TableIndex
from SharedData.SharedNumpy import SharedNumpy
from SharedData.IO.ClientSocket import ClientSocket
from SharedData.IO.ClientWebSocket import ClientWebSocket
from SharedData.IO.ClientAPI import ClientAPI
from SharedData.Database import *

class Table:

    
    """
    Represents a data table with support for disk or memory storage, partitioning, indexing, and remote synchronization.
    
    This class manages table metadata, schema initialization, record storage, and concurrency control. It supports creating, loading, and updating tables with optional partitioning by year, month, or day. The table data can be synchronized with remote storage (e.g., S3) including downloading and uploading compressed headers and tails.
    
    Key features include:
    - Initialization with schema and shared data management.
    - Support for different storage types (disk or memory).
    - Automatic handling of table partitioning and date ranges.
    - Creation and maintenance of table headers and indexes.
    - Efficient reading and writing of table data with concurrency locks.
    - Conversion between pandas DataFrames and internal record arrays.
    - Subscription and publishing capabilities over socket, websocket, or API methods.
    - Threaded upload and download operations with progress reporting.
    
    Parameters:
        shareddata: SharedData
            Shared data manager providing schema, mutex, and disk folder information.
        database: str
            Name of the database the table belongs to.
        period: str
            Data period identifier (e.g., 'M15', 'M1').
        source: str
            Data source identifier.
        tablename: str
            Name of
    """
    def __init__(self, shareddata, database, period, source, tablename,
                 records=None, names=None, formats=None, size=None, hasindex=True,
                 overwrite=False, user='master', tabletype=1, partitioning=None, is_schemaless=False):
        # tabletype 1: DISK, 2: MEMORY
        """
        '''
        Initialize a table object with specified parameters, setting up schema, records, indexing, and partitioning.
        
        Parameters:
            shareddata: Shared data resource used by the table.
            database (str): Name of the database.
            period (str): Time period identifier (e.g., 'M15', 'M1', 'RT').
            source (str): Data source identifier.
            tablename (str): Name of the table, possibly including partition info.
            records (optional): Initial records to populate the table.
            names (list, optional): List of field names for the table schema.
            formats (list, optional): List of data formats corresponding to field names.
            size (int, optional): Size of the table; if zero, disables indexing.
            hasindex (bool, optional): Whether the table has an index (default True).
            overwrite (bool, optional): Whether to overwrite existing table data (default False).
            user (str, optional): User identifier for table ownership (default 'master').
            tabletype (int, optional): Table storage type; 1 for DISK, 2 for MEMORY (default 1).
            partitioning (str, optional): Partitioning scheme ('yearly', 'monthly', 'daily').
        """
        self.type = tabletype

        self.shareddata = shareddata
        self.user = user
        self.database = database
        self.period = period
        self.source = source
        self.tablename = tablename
        self.subscription_thread = None
        self.publish_thread = None

        try:
            self.version = importlib.metadata.version("shareddata")
        except:
            self.version = 'unknown'

        self.names = names
        self.formats = formats
        self.size = size
        if not size is None:
            size = int(size)
            if size == 0:
                self.hasindex = False
        self.hasindex = hasindex
        self.is_schemaless = is_schemaless
        self.prev_bson_ptr = 0
        self.curr_bson_size = 0
                
        self.overwrite = overwrite
        self.partitioning = partitioning
        self.mindate = np.datetime64('1970-01-01', 'ns')
        self.maxdate = np.datetime64('2100-01-01', 'ns')
        if self.partitioning is not None:
            if self.partitioning == 'yearly':
                self.mindate = np.datetime64(pd.to_datetime(self.tablename.split('/')[1],format='%Y'), 'ns')
                self.maxdate = np.datetime64(self.mindate + pd.DateOffset(years=1), 'ns')
            elif self.partitioning == 'monthly':
                self.mindate = np.datetime64(pd.to_datetime(self.tablename.split('/')[1],format='%Y%m'), 'ns')
                self.maxdate = np.datetime64(self.mindate + pd.DateOffset(months=1), 'ns')
            elif self.partitioning == 'daily':
                self.mindate = np.datetime64(pd.to_datetime(self.tablename.split('/')[1],format='%Y%m%d'), 'ns')
                self.maxdate = np.datetime64(self.mindate + pd.DateOffset(days=1), 'ns')
        
        self.periodns = np.int64(24*60*60*1000*1000*1000)
        if self.period == 'M15': 
            self.periodns = np.int64(15*60*1000*1000*1000)
        elif self.period == 'M1':
            self.periodns = np.int64(1*60*1000*1000*1000)
        elif self.period == 'RT':
            self.periodns = np.int64(1*1000*1000*1000)
            self.hasindex = False

        # header
        self.hdr = None
        # creation time
        self.ctime = None
        # records
        self.recnames = []
        self.recformats = []
        self.recdtype = None
        self.records = np.ndarray([])        
        # index
        self.index = TableIndex(self)
        
        errmsg = ''
        try:            
            
            self.init_schema()
            
            if (not self.exists) | (self.overwrite):
                
                if not records is None:
                    self.parse_records(records)

                self.create_table()

            elif self.exists:

                self.load_table()
                
            # set the modify time of the file
            self.hdr['isloaded'] = 1
            self.mutex['isloaded'] = 1

            if not records is None:
                if self.hasindex:
                    self.records = self.records.upsert(records, acquire=False)
                else:
                    self.records = self.records.extend(records, acquire=False)                
                

            mtime = max(self.hdr['mtime'],self.hdr['mtimehead'], self.hdr['mtimetail'])
            self.hdr['mtime'] = mtime
            os.utime(self.filepath, (mtime, mtime))
            
        except Exception as e:
            tb = traceback.format_exc()
            errmsg = '%s error initializing\n %s\n%s!' % (
                self.relpath, str(tb), str(e))
            # errmsg = '%s error initalizing \n%s!' % (self.relpath,str(e))
            Logger.log.error(errmsg)
        finally:
            self.release()
            if errmsg != '':
                self.free()
                raise Exception(errmsg)
    
    def init_schema(self):
        """
        Initialize the schema and related attributes for the table instance.
        
        This method sets up header and tail header formats and names, initializes mutexes for shared memory access,
        determines the storage path based on user, database, period, source, and tablename, and manages schema information
        from shared data. It handles synchronization and consistency checks for the table's loading type, updates or inserts
        the table schema if necessary, and selects an appropriate database folder based on availability and usage.
        
        It also ensures the necessary directories exist, sets file paths for data, header, and tail files, and checks for
        the existence of the table data locally or remotely.
        
        Raises:
            Exception: If there are inconsistencies in the mutex type or errors in updating or retrieving the schema or database folder.
        """
        self.header_changed = False
        # head header
        self._hdrnames = ['headersize', 'headerdescr', 'version', 'md5hashhead', 'md5hashtail',
                          'ctime', 'mtime', 'mtimehead', 'mtimetail',
                          'itemsize', 'recordssize', 'count',
                          'headsize', 'tailsize', 'minchgid',
                          'hastail', 'isloaded', 'hasindex', 'isidxcreated', 'isidxsorted',
                          'next_bson_ptr',
                          'descr']
        self._hdrformats = ['<i8', '|S320', '|S8', '|S16', '|S16',
                            '<f8', '<f8', '<f8', '<f8',
                            '<i8', '<i8', '<i8',
                            '<i8', '<i8', '<i8',
                            '<u1', '<u1', '<u1', '<u1', '<u1',
                            '<u8',
                            '|SXXX']
        # tail header
        self._tailhdrnames = ['headersize', 'headerdescr',
                              'md5hash', 'mtime', 'tailsize']
        self._tailhdrformats = ['<i8', '|S80', '|S16', '<f8', '<i8']
    
        self.exists_remote = False
        self.exists_local = False
        
        # path        
        self.shm_name = f'{self.user}/{self.database}/{self.period}/{self.source}/table/{self.tablename}'
        self.relpath = str(self.shm_name)
        if os.name == 'posix':
            self.shm_name = self.shm_name.replace('/', '\\')

        # mutex
        self.pid = os.getpid()
        [self.shm_mutex, self.mutex, self.ismalloc] = \
            self.shareddata.mutex(self.shm_name, self.pid)
        if (self.mutex['type']==0): # type not initialized
            self.mutex['type'] = self.type

        elif self.mutex['type'] != self.type:
            if self.mutex['type'] == 1:
                errmsg = f'Table {self.relpath} is loaded as DISK!'
                Logger.log.error(errmsg)
                raise Exception(errmsg)            
            else:
                errmsg = f'Table {self.relpath} is loaded with unknown type!'
                Logger.log.error(errmsg)
                raise Exception(errmsg)
        
        # schema
        self.database_folder = self.shareddata.dbfolders[0]
        self.schema = None
        
        if not self.shareddata.schema is None:
            errmsg=''
            try:            
                self.shareddata.schema.table.acquire()
                buff = np.full((1,),np.nan,dtype=self.shareddata.schema.dtype)
                buff['symbol'] = self.shm_name.replace('\\', '/')
                loc = self.shareddata.schema.get_loc(buff,acquire=False)
                if loc[0] != -1: # table exists
                    self.schema = self.shareddata.schema[loc[0]]
                    folder_local = self.schema['folder_local']
                    self.database_folder = folder_local.decode('utf-8')
                else: # table does not exist
                    self.shareddata.schema.upsert(buff,acquire=False)
                    loc = self.shareddata.schema.get_loc(buff,acquire=False)
                    if loc[0] == -1: # check if table was added
                        errmsg = '%s error updating schema' % self.relpath
                        Logger.log.error(errmsg)
                        raise Exception(errmsg)
                    
                    self.schema = self.shareddata.schema[loc[0]]
                    self.database_folder = ''
                
                if (self.database_folder == '') | (self.database_folder == 'nan'):
                    # select the first disk with less percent_used
                    if len(self.shareddata.dbfolders) > 1:
                        # scan folders to check if table is already initialized
                        for f in self.shareddata.dbfolders:
                            tmppath = Path(f) / self.shm_name
                            tmppath = Path(str(tmppath).replace('\\', '/'))
                            tmppath = tmppath / 'data.bin'
                            if tmppath.is_file():
                                self.database_folder = f
                                break
                        
                        # if table not initialized get the disk with less percent_used
                        if (self.database_folder == '') | (self.database_folder == 'nan'):
                            dfdisks = self.shareddata.list_disks()
                            self.database_folder = dfdisks.index[0]
                    else:                    
                        self.database_folder = self.shareddata.dbfolders[0]

                if (self.database_folder == '') | (self.database_folder == 'nan'):
                    errmsg = '%s error getting database folder' % self.relpath
                    raise Exception(errmsg)
                else:
                    self.schema['folder_local'] = self.database_folder.encode('utf-8')
                    
            except Exception as e:
                errmsg = '%s error getting database folder\n%s!' % (self.relpath,str(e))
                Logger.log.error(errmsg)
            finally:
                self.shareddata.schema.table.release()
                if errmsg != '':
                    raise Exception(errmsg)
                            
        self.path = Path(self.database_folder)
        self.path = self.path / self.shm_name
        self.path = Path(str(self.path).replace('\\', '/'))
        os.makedirs(self.path, exist_ok=True)
        self.filepath = self.path / 'data.bin'
        self.headpath = self.path / 'head.bin'
        self.tailpath = self.path / 'tail.bin'
        self.bsonpath = self.path / 'bson.bin'      
        self.bson_file_handle = None
        self.bson_mmap = None

        # Check if schemaless (has bson_size and bson_ptr in schema)
        if not self.is_schemaless:
            if (not self.names is None) & (not self.formats is None):
                self.is_schemaless = 'bson_size' in self.names and 'bson_ptr' in self.names        
                
        self.exists_local = self.filepath.is_file()
        if self.exists_local:            
            self.exists = True
        else:
            self.exists = self.get_exists_remote()

        # For schemaless tables, initialize default schema
        if self.is_schemaless and (self.names is None or self.formats is None):
            default_names = DATABASE_PKEYS[self.database] + ['mtime', 'bson_size', 'bson_ptr']
            default_formats = []
            for name in default_names:
                if name == 'date':
                    default_formats.append('<M8[ns]')
                elif name in STRING_FIELDS:
                    default_formats.append('|S32')
                elif name in ['bson_size', 'bson_ptr']:
                    default_formats.append('<i8')
                elif name in ['mtime']:
                    default_formats.append('<M8[ns]')
                else:
                    raise Exception(f'Cannot determine format for field {name} in schemaless table {self.relpath}!')
            
            self.names = default_names
            self.formats = default_formats
                
    def get_exists_remote(self):
        """
        Checks if a remote shared memory resource exists at a specified search path.
        
        The method constructs a search path by normalizing the shared memory name and removing the user component.
        It then queries the remote shared data for any tables at that path associated with the user.
        Returns True if any remote tables are found, otherwise False.
        
        Returns:
            bool: True if remote shared memory data exists at the search path, False otherwise.
        """
        searchpath = self.shm_name.replace('\\', '/').replace(self.user,'').lstrip('/')
        dftables = self.shareddata.list_remote(searchpath, user=self.user)
        if dftables.empty:
            return False
        return self.shm_name.replace('\\', '/') in dftables.index

    def parse_records(self, records):
        """
        Parses input records to extract metadata and convert DataFrame to structured array if necessary.
        
        For schemaless tables, automatically generates default schema from database primary keys if not provided.
        This allows schemaless tables to be created without explicitly specifying names and formats.
        
        If `records` is a pandas DataFrame, it is converted to a structured array using the `df2records` method. 
        The method then extracts field names and data formats from the array interface descriptor and assigns them 
        to `self.names` and `self.formats`. If `self.size` is not set, it is initialized to the number of records.
        
        Parameters:
            records (pandas.DataFrame, list of dicts, numpy.ndarray, or None): Input data to parse.
        
        Returns:
            tuple: (numpy.ndarray, list) - The processed records and list of extra dictionaries for schemaless tables.
        """        
        
        # Set up recdtype if names/formats are available
        if self.names is not None and self.formats is not None:
            self.recnames = self.names
            self.rectypes = self.formats
            self.recdtype = np.dtype(
                {'names': self.recnames, 'formats': self.rectypes})
        
        # Convert input records to numpy structured array
        records, dict_list = self.any2records(records)
        
        # Extract names and formats from records if not already set
        if records.size > 0:
            descr = records.__array_interface__['descr']
            if self.names is None:
                self.names = [item[0] for item in descr]
                self.formats = [item[1] for item in descr]
        
        # Set size if not specified
        if self.size is None:
            self.size = int(records.size) if records.size > 0 else 0
        
        return records, dict_list

    ############### CREATE ###############    
    def create_table(self):
        # create new table or overwrite existing table
        """
        Create a new table or overwrite an existing one with the provided records.

        This method performs the following steps:
        - If the table schema attributes (`names`, `formats`, and `size`) are defined, it creates the table header, file, and allocates memory.
        - If the table does not exist or overwrite is requested but schema attributes are missing, it raises an exception.
        - For schemaless tables during overwrite, deletes existing BSON file to ensure clean state.
        - Inserts the given records into the table if any are provided.
        - If the table has an index, it initializes the index and verifies its coherence. If the index is not coherent, it attempts to reinitialize it and raises an exception if coherence cannot be established.

        Parameters:
            records (optional): The records to insert into the table after creation.

        Raises:
            Exception: If the table does not exist and cannot be created, or if the index cannot be properly created.
        """
        if (not self.names is None) \
            & (not self.formats is None)\
                & (not self.size is None):
            self.create_header()            
            self.malloc(create=True)

        elif (not self.exists) | (self.overwrite):
            raise Exception('%s not found create first!' % (self.relpath))
                    
        if self.hasindex:
            self.index.initialize()
            
        # Initialize BSON mmap for schemaless tables
        if self.is_schemaless:
            self.init_bson_mmap()

    def create_header(self):

        """
        Create and validate the header and record array dtype for the dataset.
        
        This method performs the following steps:
        - Validates that the initial columns in `self.names` match the primary key columns defined in `self.index.pkeycolumns`.
        - Ensures that the 'date' field, if present, has the correct dtype '<M8[ns]'.
        - Checks that string fields defined in `STRING_FIELDS` have string dtype '|S' if `self.hasindex` is True.
        - Inserts a 'mtime' field with dtype '<M8[ns]' if not present, or validates its dtype if present.
        - Confirms that `self.names` and `self.formats` have the same length.
        - Constructs the numpy dtype for the record array (`self.recdtype`) based on `self.names` and `self.formats`.
        - Builds the header dtype (`self.hdrdtype`) and initializes a header record array (`self.hdr`) with metadata including version, timestamps, sizes, and flags.
        - Sets flags related to indexing and loading status.
        
        Raises:
            Exception: If primary key columns do not match, or if any dtype validations fail, or if `names` and `formats` lengths differ.
        """
        check_pkey = True
        npkeys = len(self.index.pkeycolumns)
        if len(self.names) >= npkeys:
            for k in range(npkeys):
                check_pkey = (check_pkey) & (
                    self.names[k] == self.index.pkeycolumns[k])
        else:
            check_pkey = False
        if not check_pkey:
            raise Exception('First columns must be %s!' %
                            (self.index.pkeycolumns))
        else:
            if 'date' in self.names:
                if self.formats[self.names.index('date')] != '<M8[ns]':
                    raise Exception('date must be <M8[ns]!')
            
            if self.hasindex:
                for field in STRING_FIELDS:
                    if field in self.names:
                        fielddtype = self.formats[self.names.index(field)]
                        if not '|S' in fielddtype:
                            raise Exception('symbol must be a string |S!')

            if not 'mtime' in self.names:
                self.names.insert(npkeys, 'mtime')
                self.formats.insert(npkeys, '<M8[ns]')
            elif self.formats[self.names.index('mtime')] != '<M8[ns]':
                raise Exception('mtime must be <M8[ns]!')
            
            if self.is_schemaless:
                if not 'bson_size' in self.names:
                    self.names.append('bson_size')
                    self.formats.append('<i8')
                if not 'bson_ptr' in self.names:
                    self.names.append('bson_ptr')
                    self.formats.append('<i8')
            
            if len(self.names) != len(self.formats):
                raise Exception('names and formats must have same length!')
            
            # malloc recarray
            self.recnames = self.names
            self.rectypes = self.formats
            self.recdtype = np.dtype(
                {'names': self.recnames, 'formats': self.rectypes})
            descr_str = ','.join(self.recnames)+';'+','.join(self.rectypes)
            descr_str_b = str.encode(
                descr_str, encoding='UTF-8', errors='ignore')
            len_descr = len(descr_str_b)

            # build header
            self.hdrnames = self._hdrnames
            hdrformats = self._hdrformats.copy()
            hdrformats[-1] = hdrformats[-1].replace('XXX', str(len_descr))
            self.hdrformats = hdrformats
            hdrnames = ','.join(self.hdrnames)
            hdrdtypes = ','.join(self.hdrformats)
            hdrdescr_str = hdrnames+';'+hdrdtypes
            hdrdescr_str_b = str.encode(
                hdrdescr_str, encoding='UTF-8', errors='ignore')

            self.hdrdtype = np.dtype(
                {'names': self.hdrnames, 'formats': self.hdrformats})
            self.hdr = np.recarray(shape=(1,), dtype=self.hdrdtype)[0]
            self.hdr['headersize'] = 320
            self.hdr['headerdescr'] = b'\x00' * len(self.hdr['headerdescr'])
            self.hdr['headerdescr'] = hdrdescr_str_b
            self.hdr['version'] = self.version
            self.hdr['ctime'] = datetime.now().timestamp()
            self.ctime = self.hdr['ctime']
            self.hdr['mtime'] = datetime.now().timestamp()
            self.hdr['mtimehead'] = self.hdr['mtime']
            self.hdr['mtimetail'] = self.hdr['mtime']
            self.hdr['count'] = 0
            self.hdr['minchgid'] = self.hdr['count']
            self.hdr['itemsize'] = int(self.recdtype.itemsize)
            self.hdr['recordssize'] = int(self.size)
            self.hdr['headsize'] = 0
            self.hdr['descr'] = descr_str_b
            self.hdr['isloaded'] = 0
            if self.hasindex:
                self.hdr['hasindex'] = 1
            else:
                self.hdr['hasindex'] = 0
            self.hdr['isloaded'] = 0
            self.hdr['isidxcreated'] = 0
            self.hdr['isidxsorted'] = 1
            
            # Initialize next_bson_ptr for schemaless tables
            if self.is_schemaless:
                self.hdr['next_bson_ptr'] = 0
            else:
                self.hdr['next_bson_ptr'] = 0  # Set to 0 for consistency
            
    def create_file(self):
        """
        Create or extend a file at the specified filepath to a predetermined size.
        
        The target file size is calculated as the sum of the header dtype item size and the product of the record dtype item size and the number of records (self.size). If the file does not exist, it creates any necessary directories, creates the file, and preallocates space by seeking to the last byte and writing a null byte. On POSIX systems, it uses os.posix_fallocate for efficient disk space allocation. If the file exists but is smaller than the target size, it extends the file similarly. Preallocation for Windows systems is not yet implemented.
        """
        totalbytes = int(self.hdrdtype.itemsize
                         + self.recdtype.itemsize*self.size)
        if not Path(self.filepath).is_file():
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, 'wb') as f:
                # Seek to the end of the file
                f.seek(totalbytes-1)
                # Write a single null byte to the end of the file
                f.write(b'\x00')
                if os.name == 'posix':
                    os.posix_fallocate(f.fileno(), 0, totalbytes)
                elif os.name == 'nt':
                    pass  # TODO: implement preallocation for windows in pyd
        elif (Path(self.filepath).stat().st_size < totalbytes):
            with open(self.filepath, 'ab') as f:
                # Seek to the end of the file
                f.seek(totalbytes-1)
                # Write a single null byte to the end of the file
                f.write(b'\x00')
                if os.name == 'posix':
                    os.posix_fallocate(f.fileno(), 0, totalbytes)
                elif os.name == 'nt':
                    pass  # TODO: implement preallocation for windows in pyd

    def copy_file(self):
        """
        Copies the original file to a temporary file with a new header and preserves the original data.
        If the new file size is larger than the original, the file is extended with null bytes to match the new size.
        Displays a progress bar during the copying process.
        After copying and extending, deletes the original file and renames the temporary file to the original file path.
        """
        if self.size is None:
            self.size = self.hdr['recordssize']
        totalbytes = int(self.hdrdtype.itemsize
                         + self.recdtype.itemsize*self.size)

        orig_size = int(self.orig_hdr.dtype.itemsize
                        + self.orig_hdr['recordssize']*self.orig_hdr['itemsize'])

        self.filepathtmp = str(self.filepath)+'.tmp'
        with open(self.filepath, 'rb') as f:
            with open(self.filepathtmp, 'wb') as ftmp:
                # write new header
                ftmp.seek(0)
                ftmp.write(self.hdr.tobytes())
                # copy data
                f.seek(self.orig_hdr.dtype.itemsize)
                bwritten = self.orig_hdr.dtype.itemsize
                message = 'Copying file :%iMB %s' % (
                    orig_size / (1024*1024), self.relpath)
                buffersize = int(1024**2*250)
                with tqdm(total=orig_size, unit='B', unit_scale=True, desc=message) as pbar:
                    while bwritten < orig_size:
                        nwrite = int(min(buffersize, orig_size-bwritten))
                        ftmp.write(f.read(nwrite))
                        pbar.update(nwrite)
                        bwritten += nwrite
                    # extend file if needed
                    if totalbytes > orig_size:
                        ftmp.write(b'\x00'*(totalbytes-orig_size))
                    ftmp.flush()

        # rename file        
        os.remove(self.filepath)        
        os.rename(self.filepathtmp, self.filepath)

    ############### DOWNLOAD ###############
    def download(self):
        """
        Download and update the object's data from remote gzip-compressed files stored in S3.
        
        This method performs the following steps:
        1. Downloads the 'head' part of the data from a remote S3 path with a '.gzip' extension.
        2. If the remote 'head' file is newer than the local copy, it decompresses and reads the header,
           updating the local modification time and forcing a tail download.
        3. If the header indicates the presence of a 'tail' part, it downloads, decompresses, and reads it,
           updating the tail modification time.
        4. Creates or updates the local file representation.
        5. Reads the decompressed 'head' and 'tail' data into the object, resetting load and index flags.
        
        Dependencies:
        - S3Download: function to download files from S3, returning file-like objects and modification times.
        - gzip: used to decompress the downloaded gzip files.
        - Logger: used for debug logging of download performance.
        
        Updates internal state variables such as self.hdr with modification times and load status.
        """
        head_io = None
        tail_io = None
        mtimetail = None

        tini = time.time()
        remote_path = str(self.headpath)+'.gzip'
        if not self.hdr is None:
            mtimetail = self.hdr['mtimetail']
            [head_io_gzip, head_local_mtime, head_remote_mtime] = \
                S3Download(remote_path, local_mtime=self.hdr['mtimehead']
                        ,database_folder=self.database_folder)            
        else:
            [head_io_gzip, head_local_mtime, head_remote_mtime] = \
                S3Download(remote_path,database_folder=self.database_folder)

        if not head_io_gzip is None:
            # remote file is newer than local
            # unzip head and read
            te = time.time()-tini+0.000001
            datasize = head_io_gzip.getbuffer().nbytes/1000000
            Logger.log.debug('download head %s %.2fMB in %.2fs %.2fMBps ' %
                             (self.relpath, datasize, te, datasize/te))
            head_io_gzip.seek(0)
            head_io = gzip.GzipFile(fileobj=head_io_gzip, mode='rb')
            self.read_header(head_io)
            self.hdr['mtimehead'] = head_remote_mtime # update the head mtime            
            mtimetail = self.hdr['mtimetail'] - 1  # force tail download

        if not self.hdr is None:
            # read tail if needed
            if self.hdr['hastail'] == 1:
                remote_path = str(self.tailpath)+'.gzip'
                [tail_io_gzip, tail_local_mtime, tail_remote_mtime] = \
                    S3Download(remote_path, local_mtime=mtimetail,
                            database_folder=self.database_folder)
                if not tail_io_gzip is None:
                    tail_io_gzip.seek(0)
                    tail_io = gzip.GzipFile(fileobj=tail_io_gzip, mode='rb')
                    self.read_tailheader(tail_io)
                    self.hdr['mtimetail'] = tail_remote_mtime # update the tail mtime

        self.create_file()

        if not head_io is None:
            self.read_head(head_io)
            self.hdr['isloaded'] = 0
            self.hdr['isidxcreated'] = 0

        if not tail_io is None:
            self.read_tail(tail_io)
            self.hdr['isloaded'] = 0
            self.hdr['isidxcreated'] = 0

        # Download BSON file for schemaless tables if available and newer
        if self.is_schemaless:
            bson_gzip_path = str(self.bsonpath) + '.gzip'
            local_bson_mtime = 0.0
            if os.path.exists(self.bsonpath):
                local_bson_mtime = os.path.getmtime(self.bsonpath)
            [bson_io_gzip, local_mtime, remote_bson_mtime] = \
                S3Download(bson_gzip_path, local_mtime=local_bson_mtime,
                          database_folder=self.database_folder)

            if not bson_io_gzip is None:            
                # Remote BSON file is newer (defragmented), unzip and save locally
                bson_io_gzip.seek(0)
                bson_io = gzip.GzipFile(fileobj=bson_io_gzip, mode='rb')
                bson_io.seek(0)
                bson_bytes = bson_io.read()
                
                # Downloaded file is defragmented (compacted)
                # Write it directly without pre-allocation
                with open(self.bsonpath, 'wb') as f:                                                
                    f.write(bson_bytes)
                    f.flush()  
                UpdateModTime(self.bsonpath, remote_bson_mtime)
                
                # Initialize mmap - will handle proper sizing based on actual file size
                # Only preallocate extra space if table has index
                self.init_bson_mmap(from_download=True)

    ############### READ ###############
    def load_table(self):
        # open existing table
        """
        Load data into the table, ensuring the local file is available and up to date.
        
        If a local table file exists, it reads the header from the file. If the table is not loaded or the local file does not exist, it downloads the table data. Memory allocation for the table is then performed.
        
        If the table has an index, it initializes the index and verifies its coherence by checking the location of the first record. If the index is not coherent, it resets and reinitializes the index. If the index still cannot be created correctly, an exception is raised.
        
        Finally, if new records are provided, they are upserted into the table's records.
                
        """
        if self.exists_local:
            with open(self.filepath, 'rb') as io_obj:
                self.read_header(io_obj)

        if ((self.mutex['isloaded']==0) | (not self.exists_local)):
            self.download()

        self.malloc(create=True)

        if self.hasindex:
            self.index.initialize()
            if self.records.count>0:
                # check if index is coherent
                loc = self.records.get_loc(self.records[0:1], acquire=False)
                if loc[0]!=0: 
                    # index is not coherent
                    self.hdr['isidxcreated']=0
                    self.index.initialize()
                    loc = self.records.get_loc(self.records[0:1], acquire=False)
                    if loc[0]!=0:
                        raise Exception('Cannot create index!')

    def read_header(self, io_obj):
        """
        '''
        Reads and processes the header from a binary I/O object, initializing header and record data types and attributes.
        
        Parameters:
            io_obj (io.BufferedIOBase): A binary I/O object positioned at the start of the file.
        
        Raises:
            Exception: If the header description size is zero or if the header is corrupted and cannot be recovered.
        
        Behavior:
        - Seeks to the beginning of the I/O object.
        - Reads the size of the header description and raises an exception if empty.
        - Decodes and parses the header description to extract header field names and formats.
        - Constructs a NumPy dtype for the header and reads the header data into a structured array.
        - Decodes the record description from the header and constructs the record dtype.
        - Attempts to recover corrupted header descriptions using fallback names and formats if available.
        - Validates string fields if an index is present and logs warnings if mismatches occur.
        - Adjusts internal size attributes based on header values.
        - Checks if the header matches expected names; if not, converts and updates the header accordingly.
        - Sets various header flags, timestamps, and version information.
        - If a local copy exists and the I/O object is a buffered reader, closes it and copies the file locally.
        
        Notes:
        - Relies on external variables and
        """
        io_obj.seek(0)
        # load header dtype
        nbhdrdescr = int.from_bytes(io_obj.read(8), byteorder='little')
        if nbhdrdescr == 0:
            raise Exception('Empty header description!')
        hdrdescr_b = io_obj.read(nbhdrdescr)
        hdrdescr = hdrdescr_b.decode(encoding='UTF-8', errors='ignore')
        hdrdescr = hdrdescr.split('\x00', 1)[0]        
        self.hdrnames = hdrdescr.split(';')[0].split(',')
        self.hdrformats = hdrdescr.split(';')[1].split(',')
        self.hdrdtype = np.dtype(
            {'names': self.hdrnames, 'formats': self.hdrformats})
        # read header
        io_obj.seek(0)
        self.hdr = np.ndarray((1,), dtype=self.hdrdtype,
                              buffer=io_obj.read(self.hdrdtype.itemsize))[0]
        self.hdr = self.hdr.copy()
        # load data dtype
        try:
            descr = self.hdr['descr'].decode(encoding='UTF-8')
            self.recnames = descr.split(';')[0].split(',')
            self.recformats = descr.split(';')[1].split(',')
            self.is_schemaless = 'bson_size' in self.recnames and 'bson_ptr' in self.recnames
        except Exception as e:
            errmsg = f'Table header is corrupted!:{self.relpath}\n{str(e)}'
            Logger.log.critical(errmsg)
            if not self.names is None:
                Logger.log.warning(f'Trying to recover:{self.relpath}')
                self.recnames = self.names
                self.recformats = self.formats
                self.is_schemaless = 'bson_size' in self.recnames and 'bson_ptr' in self.recnames
                descr_str = ','.join(self.recnames)+';'+','.join(self.recformats)
                descr_str_b = str.encode(
                    descr_str, encoding='UTF-8', errors='ignore')
                len_descr = len(descr_str_b)
                if len_descr == len(self.hdr['descr']):
                    self.hdr['descr'] = descr_str_b
                    with open(self.filepath, 'r+b') as f:
                        f.seek(0)  # Move to start of file
                        f.write(self.hdr.tobytes())  # Write header bytes
                        f.flush()  # Ensure write is committed
                        os.fsync(f.fileno())  # Force disk write
                else:
                    errmsg = f'Cannot recover header!:{self.relpath}\n{str(e)}'
                    raise Exception(errmsg)                
            else:
                raise Exception(errmsg)
            
        if 'hasindex' in self.hdrnames:
            if self.hdr['hasindex']==1:
                for field in STRING_FIELDS:
                    if field in self.recnames:
                        fielddtype = self.recformats[self.recnames.index(field)]
                        # check if field is a string
                        if not (('S' in fielddtype) or ('|S' in fielddtype)):
                            warnmsg = f'{field} is not a string in {self.relpath}!'
                            Logger.log.warning(warnmsg)
                            self.hdr['hasindex']=0

        self.recdtype = np.dtype(
            {'names': self.recnames, 'formats': self.recformats})

        if self.hdr['count'] > self.hdr['recordssize']:
            self.hdr['recordssize'] = self.hdr['count']

        if self.size is None:
            self.size = self.hdr['recordssize']
        elif self.size < self.hdr['recordssize']:
            self.size = self.hdr['recordssize']                

        if self.hdrnames == self._hdrnames:            
            self.hasindex = self.hdr['hasindex']==1
            self.orig_hdr = self.hdr
        else:
            # convert header
            self.header_changed = True
            self.orig_hdr = self.hdr.copy()

            self.hdrnames = self._hdrnames
            len_descr = len(self.hdr['descr'])
            hdrformats = self._hdrformats.copy()
            hdrformats[-1] = hdrformats[-1].replace('XXX', str(len_descr))
            self.hdrformats = hdrformats
            hdrnames = ','.join(self.hdrnames)
            hdrdtypes = ','.join(self.hdrformats)
            hdrdescr_str = hdrnames+';'+hdrdtypes
            hdrdescr_str_b = str.encode(
                hdrdescr_str, encoding='UTF-8', errors='ignore')
            self.hdrdtype = np.dtype(
                {'names': self.hdrnames, 'formats': self.hdrformats})
            self.hdr = np.ndarray((1,), dtype=self.hdrdtype)[0]
            for name in self.orig_hdr.dtype.names:
                if name in self.hdr.dtype.names:
                    self.hdr[name] = self.orig_hdr[name]
            self.hdr['headerdescr'] = b'\x00' * len(self.hdr['headerdescr'])
            self.hdr['headerdescr'] = hdrdescr_str_b            
            if not 'mtimehead' in self.orig_hdr.dtype.names:
                self.hdr['mtimehead'] = self.hdr['mtime']
            if not 'mtimetail' in self.orig_hdr.dtype.names:
                self.hdr['mtimetail'] = self.hdr['mtime']            
            
            if 'hasindex' in self.orig_hdr.dtype.names:
                self.hasindex = self.orig_hdr['hasindex']==1
                self.hdr['hasindex'] = self.orig_hdr['hasindex']
            else:                
                if self.hasindex:
                    self.hdr['hasindex'] = 1
                else:
                    self.hdr['hasindex'] = 0

            self.hdr['isloaded'] = 0
            self.hdr['isidxcreated'] = 0
            self.hdr['headersize'] = 320
            self.hdr['isidxsorted'] = 0
            self.hdr['ctime'] = datetime.now().timestamp()
            self.ctime = self.hdr['ctime']
            self.hdr['version'] = self.version

            if self.exists_local:
                if isinstance(io_obj, io.BufferedReader):                    
                    io_obj.close()
                self.copy_file()

    def read_tailheader(self, tail_io):
        """
        Reads and parses the tail header from a binary stream.
        
        This method reads the size of the tail header description and then reads and decodes the description itself from the given binary IO stream `tail_io`. It extracts the header field names and formats, constructs a NumPy dtype accordingly, and reads the tail header data into a structured NumPy array. The method updates the instance attributes `tailhdrnames`, `tailhdrformats`, `tailhdrdtype`, and `tailhdr` with the parsed information. Additionally, it updates the main header dictionary `self.hdr` with metadata fields extracted from the tail header, including the MD5 hash, modification time, tail size, and the total count (sum of head size and tail size).
        
        Parameters:
            tail_io (io.BytesIO or similar): A binary stream positioned at the start of the tail header data.
        
        Side Effects:
            - Sets `self.tailhdrnames`, `self.tailhdrformats`, `self.tailhdrdtype`, and `self.tailhdr`.
            - Updates `self.hdr` dictionary with keys 'md5hashtail', 'mtimetail', 'tailsize', and 'count'.
        """
        tail_io.seek(0)
        tailnbhdrdescr = int.from_bytes(tail_io.read(8), byteorder='little')
        tailhdrdescr_b = tail_io.read(tailnbhdrdescr)
        tailhdrdescr = tailhdrdescr_b.decode(encoding='UTF-8', errors='ignore')
        tailhdrdescr = tailhdrdescr.replace('\x00', '')
        self.tailhdrnames = tailhdrdescr.split(';')[0].split(',')
        self.tailhdrformats = tailhdrdescr.split(';')[1].split(',')
        self.tailhdrdtype = np.dtype(
            {'names': self.tailhdrnames, 'formats': self.tailhdrformats})

        nbtailhdr = self.tailhdrdtype.itemsize
        tail_io.seek(0)
        tailheader_buf = tail_io.read(nbtailhdr)
        self.tailhdr = np.ndarray((1,),
                                  dtype=self.tailhdrdtype, buffer=tailheader_buf)[0]
        self.tailhdr = self.tailhdr.copy()
        self.tailhdr['headersize'] = tailnbhdrdescr
        # update header
        self.hdr['md5hashtail'] = self.tailhdr['md5hash']
        self.hdr['mtimetail'] = self.tailhdr['mtime']
        self.hdr['tailsize'] = self.tailhdr['tailsize']
        self.hdr['count'] = self.hdr['headsize']+self.tailhdr['tailsize']

    def read_head(self, head_io):
        """
        Reads header and associated head data from a binary IO stream and writes them to the file at self.filepath.
        
        This method:
        - Resets the input stream to the beginning.
        - Writes the header bytes stored in self.hdr to the start of the target file.
        - Skips the original header size in the input stream.
        - Reads the remaining head data in chunks (up to 250 MB) and writes it to the file.
        - Displays a progress bar to indicate the progress of the data writing process.
        
        Parameters:
        head_io (io.IOBase): A binary file-like object containing the header and head data to be read.
        
        Raises:
        Propagates any exceptions related to file I/O operations.
        """
        buffer_size = 250 * 1024 * 1024  # 250 MB buffer size
        head_io.seek(0)
        with open(self.filepath, 'rb+') as f:
            # write header
            f.seek(0)
            f.write(self.hdr.tobytes())
            # seek start of head data
            head_io.seek(self.orig_hdr.dtype.itemsize)
            # read head data
            nb_head = (self.hdr['headsize']*self.hdr['itemsize'])
            message = 'Unzipping:%iMB %s' % (
                nb_head / (1024*1024), self.relpath)
            with tqdm(total=nb_head, unit='B', unit_scale=True, desc=message) as pbar:
                while True:
                    buffer = head_io.read(buffer_size)
                    if not buffer:
                        break
                    f.write(buffer)
                    pbar.update(len(buffer))
            f.flush()

    def read_tail(self, tail_io):
        """
        Writes data from the given tail_io buffer to the tail section of the file associated with this object.
        
        This method:
        1. Resets the tail_io buffer's position to the beginning.
        2. Calculates the offset in the file by adding the header size and the head data size.
        3. Opens the file in read-write binary mode.
        4. Seeks to the calculated offset.
        5. Advances the tail_io buffer position by the size of the tail header.
        6. Writes the remaining data from tail_io into the file.
        7. Flushes the file buffer to ensure data is written to disk.
        
        Parameters:
        tail_io (io.BytesIO or similar): A file-like object containing the tail data to be written.
        
        Raises:
        Any exceptions related to file I/O operations may be propagated.
        """
        tail_io.seek(0)
        nbhdr = self.hdr.dtype.itemsize
        nbhead = self.hdr['headsize']*self.hdr['itemsize']
        with open(self.filepath, 'rb+') as f:
            f.seek(nbhdr+nbhead)
            tail_io.seek(self.tailhdr.dtype.itemsize)
            f.write(tail_io.read())
            f.flush()

    def compare_hash(self, h1, h2):
        """
        Compare two hash strings up to the length of the shorter one.

        Parameters:
            h1 (str): The first hash string.
            h2 (str): The second hash string.

        Returns:
            bool: True if the prefixes of both hashes up to the length of the shorter hash are equal, False otherwise.
        """
        l1 = len(h1)
        l2 = len(h2)
        l = min(l1, l2)
        return h1[:l] == h2[:l]

    ############### BSON MANAGEMENT ###############
    def init_bson_mmap(self, from_download=False):
        """Initialize or reopen memory-mapped BSON file with proper sizing.
        
        Parameters:
            from_download (bool): If True, file was just downloaded (defragmented).
                                 File will NOT be pre-allocated; use actual file size.
        """
        if not self.is_schemaless:
            return
                    
        # Estimate initial size based on table size (500 bytes per record)
        # For tables with size=0 and hasindex=False, use 100MB initial size
        if self.size == 0 and not self.hasindex:
            initial_size = 100 * 1024 * 1024  # 100MB
        else:
            # 500 bytes per record estimate (ensure integer)
            initial_size = int(max(int(self.size) * 500, 100 * 1024 * 1024))

        if not self.bsonpath.exists():
            # Create new file with initial size (only if NOT from download)
            if from_download:
                # Should not happen - download should create the file
                raise Exception(f'BSON file does not exist after download: {self.bsonpath}')                        
            
            with open(self.bsonpath, 'wb') as f:
                f.seek(initial_size - 1)
                f.write(b'\x00')
                f.flush()
                if os.name == 'posix':
                    os.posix_fallocate(f.fileno(), 0, initial_size)
        
        # Open file handle
        if self.bson_file_handle is not None:
            self.bson_file_handle.close()
        self.bson_file_handle = open(self.bsonpath, 'r+b')
        
        # Get current file size
        self.bson_file_handle.seek(0, 2)
        current_size = self.bson_file_handle.tell()
        
        # If from download, DO NOT extend file - use defragmented size as-is
        # The BSON pointers in records already match the compact layout
        if not from_download and current_size == 0:
            # File is empty, extend it first (only for new files)
            self.bson_file_handle.seek(initial_size - 1)
            self.bson_file_handle.write(b'\x00')
            self.bson_file_handle.flush()
            if os.name == 'posix':
                os.posix_fallocate(self.bson_file_handle.fileno(), 0, initial_size)
            current_size = initial_size
        
        # Create mmap
        if current_size > 0:
            self.bson_mmap = mmap.mmap(
                self.bson_file_handle.fileno(),
                current_size,
                access=mmap.ACCESS_WRITE
            )
            self.curr_bson_size = current_size
        else:
            raise Exception(f'BSON file has zero size: {self.bsonpath}')

    def allocate_bson_space(self, size):
        """
        Allocate space in memory-mapped BSON file for multi-process safety.
        
        Uses the 'next_bson_ptr' field in the table header to track the next available position.
        This ensures multiple processes can safely allocate space without conflicts.
        
        The allocation cursor (next_bson_ptr) is atomically updated in the shared header.
        """
        # Initialize mmap if not done
        if self.bson_mmap is None:
            self.init_bson_mmap()
        
        # Initialize next_bson_ptr in header if needed (first allocation)
        if self.hdr['next_bson_ptr'] == 0:
            # Scan existing records to find high-water mark
            cnt = int(self.hdr['count'])
            recs = getattr(self, 'records', None)
            if recs is not None and hasattr(recs, 'dtype') and ('bson_ptr' in recs.dtype.names and 'bson_size' in recs.dtype.names):
                if cnt > 0:
                    view = recs[:cnt]
                    if view.size > 0:
                        valid = (view['bson_size'] > 0) & (view['bson_ptr'] >= 0)
                        if valid.any():
                            endpos = np.max(view['bson_ptr'][valid] + view['bson_size'][valid])
                            self.hdr['next_bson_ptr'] = int(endpos)
        
        current_size = len(self.bson_mmap)
        current_cursor = int(self.hdr['next_bson_ptr'])
        needed_size = current_cursor + size
        
        # Extend mmap if needed (grow by 100MB chunks or size, whichever is larger)
        if needed_size > current_size:
            grow_by = max(100 * 1024 * 1024, size)
            new_size = current_size + grow_by
            
            # Close and reopen with larger size
            self.bson_mmap.close()
            
            # Extend file
            self.bson_file_handle.seek(new_size - 1)
            self.bson_file_handle.write(b'\x00')
            self.bson_file_handle.flush()
            if os.name == 'posix':
                os.posix_fallocate(self.bson_file_handle.fileno(), 0, new_size)
            
            # CRITICAL: Force OS-level flush to disk before updating header
            # This ensures other processes see the extended file size
            os.fsync(self.bson_file_handle.fileno())

            # Recreate mmap
            self.bson_mmap = mmap.mmap(
                self.bson_file_handle.fileno(),
                new_size,
                access=mmap.ACCESS_WRITE
            )
            self.curr_bson_size = new_size
        
        # Allocate space and update cursor atomically
        offset = current_cursor
        self.hdr['next_bson_ptr'] = current_cursor + size
        return offset

    def store_bson(self, data_dict):
        """Store BSON using memory-mapped file (zero-copy write)."""
        bson_bytes = bson.encode(data_dict)
        size = len(bson_bytes)
        offset = self.allocate_bson_space(size)
        
        # Direct mmap write (no system call overhead)
        self.bson_mmap[offset:offset + size] = bson_bytes
        # No flush needed - mmap handles it
        
        return offset, size

    def store_bson_batch(self, dict_list):
        """Ultra-fast batch BSON storage using memory-mapped I/O.
        
        This function packs all BSON documents contiguously into a single allocated
        region to minimize file seek/write syscalls. Supports arbitrary ordering
        and non-sequential destination record positions because the caller maps
        returned offsets explicitly.

        Empty / None dictionaries produce (0,0) keeping input order.
        """
        if not dict_list:
            return []
        
        # Pre-encode all documents
        encoded = []
        total_size = 0
        for d in dict_list:
            if not d:
                encoded.append((b'', 0))
                continue
            bts = bson.encode(d)
            sz = len(bts)
            encoded.append((bts, sz))
            total_size += sz
        
        if total_size == 0:
            return [(0, 0) for _ in dict_list]
        
        # Single allocation for entire batch
        base_offset = self.allocate_bson_space(total_size)
        
        # Zero-copy batch write using memoryview
        offsets = []
        cursor = 0
        for bts, sz in encoded:
            if sz == 0:
                offsets.append((0, 0))
                continue
            
            # Direct mmap write
            self.bson_mmap[base_offset + cursor:base_offset + cursor + sz] = bts
            offsets.append((base_offset + cursor, sz))
            cursor += sz
        
        # Optional: sync to disk (usually not needed immediately)
        # self.bson_mmap.flush()
        
        return offsets

    def load_dictionary(self, offset, size):
        """Load BSON from memory-mapped file (zero-copy read)."""
        if size == 0:
            return {}
        
        # Initialize mmap if not done
        if self.bson_mmap is None:
            self.init_bson_mmap()
        
        # Direct mmap read (no system call)
        data = bytes(self.bson_mmap[offset:offset + size])
        return bson.decode(data)

    def defragment_bson(self, chunk_size=100000, buffer_mb=512, acquire=True):
        """
        Defragments the BSON file IN-PLACE by creating a compacted copy, then copying it back to the original file.
        
        This approach:
        - Creates a temporary defragmented file
        - Copies the compacted data back to the original file
        - Zeros out the remaining space
        - Truncates the file to the new size
        - Updates record pointers
        - No file removal/rename needed - all operations are in-place
        
        Optimized for millions of rows using:
        - Direct mmap-to-buffer copying without intermediate allocations
        - Vectorized NumPy operations for offset calculations
        - Large batch processing to minimize I/O calls
        - Pre-allocated bytearray buffers instead of list operations
        - Preserves table order (no sorting) to maintain record-to-data mapping
        
        Parameters:
            chunk_size (int): Number of records to process per batch (default: 100000)
            buffer_mb (int): Size of read/write buffer in MB (default: 512)
            acquire (bool): Whether to acquire/release lock. Set to False if caller already holds lock (default: True)
        
        Returns:
            dict: Statistics including original size, new size, and space reclaimed in bytes.
        
        Raises:
            Exception: If the table is not schemaless or if defragmentation fails.
        """
        if not self.is_schemaless:
            raise Exception(f'Cannot defragment non-schemaless table {self.relpath}')
        
        if not self.bsonpath.exists():
            Logger.log.warning(f'No BSON file to defragment for {self.relpath}')
            return {'original_size': 0, 'new_size': 0, 'reclaimed': 0}
        
        if acquire:
            self.acquire()
        
        try:
            original_size = self.bsonpath.stat().st_size
            temp_bson_path = Path(str(self.bsonpath) + '.defrag')
            total_records = self.hdr['count']
            if total_records == 1:
                return {'original_size': original_size, 'new_size': original_size, 'reclaimed': 0}
            
            # Pre-allocate arrays for batch processing (vectorized)
            bson_ptrs = self.records['bson_ptr'][:total_records]
            bson_sizes = self.records['bson_size'][:total_records]
            
            # Filter out empty records (vectorized)
            valid_mask = (bson_sizes > 0)
            valid_indices = np.where(valid_mask)[0]
            
            if len(valid_indices) == 0:
                Logger.log.warning(f'No valid BSON data to defragment for {self.relpath}')
                return {'original_size': original_size, 'new_size': 0, 'reclaimed': original_size}
            
            # Initialize mmap if needed
            if self.bson_mmap is None:
                self.init_bson_mmap()
            
            # Get valid pointers and sizes (vectorized slicing)
            valid_ptrs = bson_ptrs[valid_indices]
            valid_sizes = bson_sizes[valid_indices]
            
            # Write in table order (NO SORTING) to preserve record-to-data mapping
            buffer_size = buffer_mb * 1024 * 1024
            message = f'Defragmenting BSON file: {self.relpath}'
            num_chunks = (len(valid_indices) + chunk_size - 1) // chunk_size
            
            # Pre-allocate new offset arrays (vectorized)
            new_offsets = np.zeros(len(valid_indices), dtype=np.int64)
            
            # Step 1: Create defragmented temporary file
            with open(temp_bson_path, 'wb', buffering=buffer_size) as new_file:
                current_offset = 0
                
                with tqdm(total=num_chunks, desc=message, unit='chunk') as pbar:
                    for chunk_start in range(0, len(valid_indices), chunk_size):
                        chunk_end = min(chunk_start + chunk_size, len(valid_indices))
                        
                        # Get chunk metadata (vectorized slicing) - in table order
                        chunk_ptrs = valid_ptrs[chunk_start:chunk_end]
                        chunk_sizes = valid_sizes[chunk_start:chunk_end]
                        
                        # Pre-allocate buffer for this chunk (single allocation)
                        chunk_size_bytes = int(np.sum(chunk_sizes))
                        chunk_buffer = bytearray(chunk_size_bytes)
                        
                        # Read from old positions, write sequentially
                        buffer_offset = 0
                        for ptr, size in zip(chunk_ptrs, chunk_sizes):
                            size = int(size)
                            # Direct mmap slice access (zero-copy read)
                            chunk_buffer[buffer_offset:buffer_offset + size] = self.bson_mmap[ptr:ptr + size]
                            buffer_offset += size
                        
                        # Single write operation for entire chunk
                        new_file.write(chunk_buffer)
                        
                        # Calculate new offsets (vectorized cumsum)
                        chunk_new_offsets = np.empty(len(chunk_sizes), dtype=np.int64)
                        chunk_new_offsets[0] = current_offset
                        if len(chunk_sizes) > 1:
                            chunk_new_offsets[1:] = current_offset + np.cumsum(chunk_sizes[:-1])
                        
                        new_offsets[chunk_start:chunk_end] = chunk_new_offsets
                        current_offset += chunk_size_bytes
                        
                        pbar.update(1)
                
                new_file.flush()
                os.fsync(new_file.fileno())
            
            new_size = temp_bson_path.stat().st_size
            
            # Step 2: Close old mmap/handle to allow in-place modification
            if self.bson_mmap is not None:
                self.bson_mmap.close()
                self.bson_mmap = None
            if self.bson_file_handle is not None:
                self.bson_file_handle.close()
                self.bson_file_handle = None
            
            # Step 3: Copy defragmented data back to original file IN-PLACE
            with open(self.bsonpath, 'r+b') as orig_file:
                with open(temp_bson_path, 'rb') as defrag_file:
                    # Copy defragmented data
                    orig_file.seek(0)
                    bytes_copied = 0
                    copy_buffer_size = 10 * 1024 * 1024  # 10MB chunks
                    
                    while bytes_copied < new_size:
                        chunk = defrag_file.read(copy_buffer_size)
                        if not chunk:
                            break
                        orig_file.write(chunk)
                        bytes_copied += len(chunk)
                    
                    # Zero out remaining space
                    if original_size > new_size:
                        remaining = original_size - new_size
                        zero_chunk_size = 10 * 1024 * 1024  # 10MB zero chunks
                        zeros_written = 0
                        
                        while zeros_written < remaining:
                            chunk_size = min(zero_chunk_size, remaining - zeros_written)
                            orig_file.write(b'\x00' * chunk_size)
                            zeros_written += chunk_size
                    
                    # Truncate file to new size
                    # orig_file.truncate(new_size)
                    orig_file.flush()
                    os.fsync(orig_file.fileno())
            
            # Step 4: Clean up temporary file
            os.remove(temp_bson_path)
            
            # Step 5: Update pointers - no reordering needed since we wrote in table order
            self.records['bson_ptr'][valid_indices] = new_offsets
            # Sizes remain unchanged
            
            # Step 6: Reset allocation cursor to end of compacted data
            self.hdr['next_bson_ptr'] = new_size
            
            # Step 7: Reinitialize BSON mmap with the modified file
            self.init_bson_mmap(from_download=True)
            
            # Mark records as modified to trigger write
            self.hdr['mtime'] = datetime.now().timestamp()
            self.hdr['minchgid'] = 0
            
            stats = {
                'original_size': original_size,
                'new_size': new_size,
                'reclaimed': original_size - new_size
            }
            
            Logger.log.info(
                f'Defragmented {self.relpath} BSON file: '
                f'{original_size/1024/1024:.2f}MB -> {new_size/1024/1024:.2f}MB '
                f'(reclaimed {stats["reclaimed"]/1024/1024:.2f}MB)'
            )
            
            return stats
                
        except Exception as e:
            errmsg = f'Failed to defragment BSON file for {self.relpath}: {str(e)}'
            Logger.log.error(errmsg)
            
            # Clean up temp file if it exists
            if temp_bson_path.exists():
                try:
                    os.remove(temp_bson_path)
                except:
                    pass
            
            raise Exception(errmsg)
        
        finally:
            if acquire:
                self.release()

    ############### WRITE ###############
    def write(self, force_write=False):
        """
        Writes data to a file and uploads it concurrently using separate threads.
        
        This method performs the following steps:
        1. Acquires a lock to ensure thread safety.
        2. Creates or updates the file header if necessary.
        3. Syncs BSON mmap for schemaless tables.
        4. Starts two threads:
           - One to upload the data (possibly to S3) with header information.
           - Another to flush/write the file data locally.
        5. Waits for both threads to complete.
        6. Logs the write operation details including file path, data size, elapsed time, and throughput.
        7. Handles exceptions by logging an error message and re-raising the exception.
        8. Releases the lock regardless of success or failure.
        
        Parameters:
            force_write (bool): If True, forces the header to be written even if not modified.
        
        Raises:
            Exception: If the write or upload operation fails.
        """
        errmsg = ''
        try:
            self.acquire()

            tini = time.time()
            # create header
            mtime = self.hdr['mtime']
            write_head = False            
            write_head = self.fill_header(force_write)

            # Flush BSON mmap if schemaless table
            if self.is_schemaless and self.bson_mmap is not None:
                self.bson_mmap.flush()
                if self.bson_file_handle is not None:
                    os.fsync(self.bson_file_handle.fileno())

            thread_s3 = threading.Thread(
                target=self.upload, args=(write_head, mtime, force_write))
            thread_s3.start()

            thread_flush = threading.Thread(target=self.write_file)
            thread_flush.start()

            # join threads
            thread_s3.join()
            thread_flush.join()

            te = time.time() - tini
            datasize = self.hdr['count'] * self.hdr['itemsize'] / 1000000
            Logger.log.debug('write %s %.2fMB in %.2fs %.2fMBps ' %
                             (self.relpath, datasize, te, datasize / te))
        except Exception as e:
            errmsg = 'Could not write %s\n%s!' % (self.relpath, e)
            Logger.log.error(errmsg)
        finally:
            self.release()
            if errmsg != '':
                raise Exception(errmsg)

    def partition_head_tail(self):
        
        """
        Partition records into head and tail segments based on the presence and value of a 'date' field.
        
        If the 'date' field is absent, the entire dataset is treated as the head with no tail.
        If the 'date' field exists, records are split at the start of the current year:
        - Records before the current year form the head.
        - Records from the current year onward form the tail.
        
        Updates the header dictionary (`self.hdr`) with:
        - 'headsize': number of records in the head segment.
        - 'tailsize': number of records in the tail segment.
        - 'hastail': flag indicating if a tail segment exists (1 if yes, 0 if no).
        - 'minchgid': reset to one more than the total record count.
        - 'mtimehead' and 'mtimetail': modification times for head and tail segments.
        
        Returns:
            write_head (bool): Whether the head segment needs to be written or updated.
            headsize (int): Number of records in the head segment.
            tailsize (int): Number of records in the tail segment.
        """
        if not 'date' in self.records.dtype.names:
            tailsize = 0
            headsize = self.hdr['count']
            self.hdr['hastail'] = 0
        else:
            # partition data by current year
            partdate = pd.Timestamp(datetime(datetime.now().year, 1, 1))      
            if self.hdr['count']>0:  
                idx = self.records['date'] >= partdate
                if np.any(idx):  # there is data for the current year
                    if np.all(idx):  # all data for the current year
                        headsize = self.hdr['count']
                        tailsize = 0
                        self.hdr['hastail'] = 0
                    else:  # some data for the current year
                        partid = np.where(idx)[0][0]
                        headsize = partid
                        tailsize = self.hdr['count'] - partid
                        self.hdr['hastail'] = 1
                else:  # there is not data for the current year
                    tailsize = 0
                    headsize = self.hdr['count']
                    self.hdr['hastail'] = 0
            else:  # there is not data for the current year
                tailsize = 0
                headsize = self.hdr['count']
                self.hdr['hastail'] = 0

        headsize_chg = (headsize != self.hdr['headsize'])
        self.hdr['headsize'] = headsize        
        self.hdr['tailsize'] = tailsize

        head_modified = (self.hdr['minchgid'] <= self.hdr['headsize'])
        self.hdr['minchgid'] = self.hdr['count']+1 # reset the minchgid
        
        write_head = (head_modified) | (headsize_chg) 
        
        self.hdr['mtimetail'] = self.hdr['mtime']
        if write_head:
            self.hdr['mtimehead'] = self.hdr['mtime']

        return write_head, headsize, tailsize

    def fill_header(self, force_write=False):

        """
        Fill and update the header and tail header information, including computing MD5 hashes for data integrity.
        
        This method partitions the data into head and tail sections, initializes the tail header record array,
        and calculates MD5 hashes for the head and tail data sections. It supports incremental hashing with a
        progress bar for large data blocks to avoid memory overload.
        
        Parameters:
            force_write (bool): If True, forces the header to be written and the MD5 hash to be recalculated,
                                regardless of the current state.
        
        Returns:
            bool: A flag indicating whether the head section should be written.
        
        Side Effects:
            - Updates self.tailhdr with tail header metadata including header size, description, modification time,
              tail size, and MD5 hash.
            - Updates self.hdr with MD5 hashes for head and tail sections.
        """
        write_head, headsize, tailsize = self.partition_head_tail()

        nb_header = int(self.hdrdtype.itemsize)
        nb_head = int(self.hdr['headsize']*self.hdr['itemsize'])
        nb_tail = int(tailsize*self.hdr['itemsize'])

        self.tailhdrdtype = np.dtype(
            {'names': self._tailhdrnames, 'formats': self._tailhdrformats})
        self.tailhdr = np.recarray(shape=(1,), dtype=self.tailhdrdtype)[0]
        self.tailhdr['headersize'] = 80
        _headerdescr = ','.join(self._tailhdrnames) + \
            ';'+','.join(self._tailhdrformats)
        _headerdescr_b = str.encode(
            _headerdescr, encoding='UTF-8', errors='ignore')
        self.tailhdr['headerdescr'] = _headerdescr_b
        self.tailhdr['mtime'] = self.hdr['mtime']
        self.tailhdr['tailsize'] = tailsize

        if (write_head) | (force_write):
            self.hdr['md5hashhead'] = 0  # reset the hash value
            nb_records_mb = (nb_header+nb_head)/(1024*1024)
            if nb_records_mb <= 100:
                m = hashlib.md5(self.records[0:self.hdr['headsize']].tobytes())
            else:
                message = 'Creating md5 hash:%iMB %s' % (
                    nb_records_mb, self.relpath)
                block_size = 100 * 1024 * 1024  # or any other block size that you prefer
                chunklines = int(block_size/self.hdr['itemsize'])
                total_lines = self.hdr['headsize']
                read_lines = 0
                nb_total = self.hdr['headsize']*self.hdr['itemsize']
                m = hashlib.md5()
                # Use a with block to manage the progress bar
                with tqdm(total=nb_total, unit='B', unit_scale=True, desc=message) as pbar:
                    # Loop until we have read all the data
                    while read_lines < total_lines:
                        # Read a block of data
                        chunk_size = min(chunklines, total_lines-read_lines)
                        # Update the shared memory buffer with the newly read data
                        m.update(
                            self.records[read_lines:read_lines+chunk_size].tobytes())
                        read_lines += chunk_size  # update the total number of bytes read so far
                        # Update the progress bar
                        pbar.update(chunk_size*self.hdr['itemsize'])
            self.hdr['md5hashhead'] = m.digest()

        if self.hdr['hastail'] == 1:
            self.tailhdr['md5hash'] = 0  # reset the hash value
            self.hdr['md5hashtail'] = 0  # reset the hash value
            nb_records_mb = (nb_tail)/(1024*1024)
            startbyte = nb_header+nb_head
            if nb_records_mb <= 100:
                m = hashlib.md5(
                    self.records[self.hdr['headsize']:self.hdr['count']].tobytes())
            else:
                message = 'Creating md5 hash:%iMB %s' % (
                    nb_records_mb, self.relpath)
                block_size = 100 * 1024 * 1024  # or any other block size that you prefer
                chunklines = int(block_size/self.hdr['itemsize'])
                total_lines = self.tailhdr['tailsize']
                read_lines = 0
                tailstart = self.hdr['headsize']
                nb_total = self.tailhdr['tailsize']*self.hdr['itemsize']
                m = hashlib.md5()
                # Use a with block to manage the progress bar
                with tqdm(total=nb_total, unit='B', unit_scale=True, desc=message) as pbar:
                    # Loop until we have read all the data
                    while read_lines < total_lines:
                        # Read a block of data
                        chunk_size = min(chunklines, total_lines-read_lines)
                        # Update the shared memory buffer with the newly read data
                        m.update(
                            self.records[tailstart+read_lines:tailstart+read_lines+chunk_size].tobytes())
                        read_lines += chunk_size  # update the total number of bytes read so far
                        # Update the progress bar
                        pbar.update(chunk_size*self.hdr['itemsize'])

            self.tailhdr['md5hash'] = m.digest()
            self.hdr['md5hashtail'] = self.tailhdr['md5hash']

        return write_head

    ############### UPLOAD ###############
    def upload(self, write_head, mtime, force_write=False):
        """
        Uploads the head, tail, and BSON files to remote storage based on modification times and flags.
        
        For schemaless tables, defragments the BSON file FIRST to ensure that the uploaded head/tail
        contain the correct updated pointers for the defragmented BSON file.
        """
        # DEFRAGMENT BSON FIRST (before uploading head/tail) for schemaless tables
        # This ensures the pointers in records are updated before we upload them
        if self.is_schemaless and self.bsonpath.exists():
            bson_gzip_path = str(self.bsonpath) + '.gzip'
            remote_bson_mtime = S3GetMtime(bson_gzip_path, self.database_folder)
            remote_bson_is_updated = False
            if remote_bson_mtime is not None:
                remote_bson_is_updated = remote_bson_mtime >= mtime
            
            # Defragment if BSON needs upload (this updates pointers in records)
            if not remote_bson_is_updated or force_write:
                # Pass acquire=False because we're already in write() context with lock held
                stats = self.defragment_bson(acquire=False)
                
                # Mark header as modified to force head/tail upload with new pointers
                write_head = True
                self.hdr['mtimehead'] = mtime
                self.hdr['mtimetail'] = mtime
        
        # Now upload head/tail with UPDATED pointers
        remote_head_mtime = S3GetMtime(str(self.headpath)+'.gzip', self.database_folder)
        remote_head_is_updated = False
        if not remote_head_mtime is None:
            remote_head_is_updated = remote_head_mtime >= self.hdr['mtimehead']

        if (write_head) | (not remote_head_is_updated) | (force_write):
            self.upload_head(mtime)

        if self.hdr['hastail'] == 1:
            remote_tail_mtime = S3GetMtime(str(self.tailpath)+'.gzip', self.database_folder)
            remote_tail_is_updated = False
            if not remote_tail_mtime is None:
                remote_tail_is_updated = remote_tail_mtime >= self.hdr['mtimetail']
            if not remote_tail_is_updated:
                self.upload_tail(mtime)
        else:
            self.delete_tail()

        # Upload the defragmented BSON file (already defragmented above)
        if self.is_schemaless and self.bsonpath.exists():
            bson_gzip_path = str(self.bsonpath) + '.gzip'
            remote_bson_mtime = S3GetMtime(bson_gzip_path, self.database_folder)
            remote_bson_is_updated = False
            if remote_bson_mtime is not None:
                remote_bson_is_updated = remote_bson_mtime >= mtime
            if not remote_bson_is_updated or force_write:
                # Compress and upload the already-defragmented BSON file
                self.upload_bson(mtime)

    def upload_head(self, mtime):
        # zip head        
        """
        Compresses the header data in chunks using gzip and uploads the compressed file to S3.
        
        Parameters:
            mtime (float): The modification time to associate with the uploaded file.
        
        The method performs the following steps:
        - Creates an in-memory bytes buffer.
        - Compresses the header data (`self.hdr` and `self.records`) in chunks of up to 100 MB using gzip with compression level 1.
        - Displays a progress bar indicating the compression progress.
        - Uploads the resulting gzip file to an S3 bucket using the `S3Upload` function, storing it at `self.headpath` with a '.gzip' extension and associating it with the given modification time.
        """
        gzip_io = io.BytesIO()
        with gzip.GzipFile(fileobj=gzip_io, mode='wb', compresslevel=1) as gz:
            gz.write(self.hdr.tobytes())
            headsize_mb = (self.hdr['headsize'] *
                           self.hdr['itemsize']) / (1024*1024)
            blocksize = 1024*1024*100
            chunklines = int(blocksize/self.hdr['itemsize'])
            descr = 'Zipping:%iMB %s' % (headsize_mb, self.relpath)
            with tqdm(total=headsize_mb, unit='B', unit_scale=True, desc=descr) as pbar:
                written = 0
                while written < self.hdr['headsize']:
                    # write in chunks of max 100 MB size
                    chunk_size = min(chunklines, self.hdr['headsize']-written)
                    gz.write(
                        self.records[written:written+chunk_size].tobytes())
                    written += chunk_size
                    pbar.update(chunk_size*self.hdr['itemsize'])
        S3Upload(gzip_io, str(self.headpath)+'.gzip', mtime,
                 database_folder=self.database_folder)

    def upload_tail(self, mtime):
        """
        Compresses the tail header and a subset of records into a gzip archive and uploads it to an S3 bucket.
        
        Parameters:
            mtime (int or float): The modification time to associate with the uploaded file.
        
        This method creates an in-memory gzip file containing the tail header and a slice of the records from the current object.
        The compressed data is then uploaded to an S3 bucket using the S3Upload function. The upload path is constructed by
        appending '.gzip' to the object's tailpath attribute, and the file is stored within the specified database folder.
        """
        gzip_io = io.BytesIO()
        with gzip.GzipFile(fileobj=gzip_io, mode='wb', compresslevel=1) as gz:
            gz.write(self.tailhdr.tobytes())
            gz.write(self.records[self.hdr['headsize']
                     :self.hdr['count']].tobytes())
        S3Upload(gzip_io, str(self.tailpath)+'.gzip', mtime,
                 database_folder=self.database_folder)

    def upload_bson(self, mtime):
        """
        Defragments and compresses the BSON file using gzip, then uploads it to S3.
        
        This method defragments the BSON file to remove free space, compresses it with gzip,
        and uploads it to S3. The defragmentation ensures only actively used BSON data is uploaded.

        Parameters:
            mtime (float): The modification time to associate with the uploaded file.
        """
        if not self.bsonpath.exists():
            return
        
        try:
            
            # Compress the defragmented file
            gzip_io = io.BytesIO()
            with open(self.bsonpath, 'rb') as bson_file:
                with gzip.GzipFile(fileobj=gzip_io, mode='wb', compresslevel=1) as gz:
                    # Read and compress in chunks to handle large files
                    chunk_size = 10 * 1024 * 1024  # 10MB chunks
                    while True:
                        chunk = bson_file.read(chunk_size)
                        if not chunk:
                            break
                        gz.write(chunk)

            # Reset position to beginning before upload
            gzip_io.seek(0)
            S3Upload(gzip_io, str(self.bsonpath)+'.gzip', mtime,
                     database_folder=self.database_folder)
                        
        except Exception as e:
            Logger.log.error(f'Failed to upload BSON file for {self.relpath}: {e}')
            raise

    def delete_tail(self):
        """
        Deletes the compressed tail file from the S3 storage if it exists.
        
        This method constructs the remote file path for the compressed tail file by appending '.gzip' to the object's tailpath attribute.
        It then adjusts the path relative to the database folder, normalizing path separators to forward slashes.
        Finally, it calls the S3DeleteFile function to remove the file from the S3 bucket.
        """
        # delete tail if it exists
        path = str(self.tailpath)+'.gzip'
        if self.database_folder:
            remotefilepath = str(path).replace(
                self.database_folder.rstrip('/'), '')
        else:
            remotefilepath = str(path).replace(
                os.environ['DATABASE_FOLDER'], '')
        remotefilepath = remotefilepath.replace('\\', '/')        
        S3DeleteFile(remotefilepath)        

    ############### CONVERT ###############
    def records2df(self, records):
        """
        Convert a list of records into a pandas DataFrame, decode byte-string columns to UTF-8 strings, and set the DataFrame index.
        
        Parameters:
            records (list or iterable): A collection of records (e.g., list of dictionaries) to be converted into a DataFrame.
        
        Returns:
            pandas.DataFrame: DataFrame constructed from the input records with byte-string columns decoded to UTF-8 strings and indexed by the primary key columns specified in self.index.pkeycolumns.
        """
        df = pd.DataFrame(records, copy=False)
        dtypes = df.dtypes.reset_index()
        dtypes.columns = ['tag', 'dtype']
        # convert object to string
        string_idx = pd.Index(['|S' in str(dt) for dt in dtypes['dtype']])
        string_idx = (string_idx) | pd.Index(dtypes['dtype'] == 'object')
        tags_obj = dtypes['tag'][string_idx].values
        for tag in tags_obj:
            try:
                df[tag] = df[tag].str.decode(encoding='utf-8', errors='ignore')
            except:
                pass
        df = df.set_index(self.index.pkeycolumns)
        return df

    def df2records(self, df, extra_data=None):
        """
        Convert a pandas DataFrame into a NumPy structured array (records) with validation and type handling.
        
        This method verifies that the DataFrame's index matches the expected primary key columns (`self.index.pkeycolumns`).
        If the index does not match, it raises an Exception.
        
        If `self.recdtype` is None:
        - The DataFrame index is reset.
        - Datetime columns with timezones are converted to UTC naive datetimes.
        - Object dtype columns are converted to UTF-8 encoded byte strings.
        - The DataFrame is converted to a contiguous NumPy structured array.
        - If any object dtype remains in the resulting array, an Exception is raised.
        
        If `self.recdtype` is provided:
        - The DataFrame index is reset.
        - Datetime columns with timezones are converted to UTC naive datetimes.
        - A NumPy structured array of the specified dtype is created, filled initially with NaNs.
        - Columns are converted to the specified dtype, with missing integer values filled with zero.
        - Columns not in `self.recdtype` are optionally collected into a list of dictionaries.
        - Errors during conversion are logged but do not halt processing.
        
        Parameters:
            df (pandas.DataFrame): The DataFrame to convert. Must have an index matching `self.index.pkeycolumns`.
            extra_data (list, optional): If provided, columns not in `self.recdtype` will be added to this list
                                            as dictionaries (one per row).
        
        Returns:
            numpy.ndarray: A structured array representing the DataFrame records
        """
        check_pkey = True
        if len(self.index.pkeycolumns) == len(df.index.names):
            for k in range(len(self.index.pkeycolumns)):
                check_pkey = (check_pkey) & (
                    df.index.names[k] == self.index.pkeycolumns[k])
        else:
            check_pkey = False
        if not check_pkey:
            raise Exception('First columns must be %s!' %
                            (self.index.pkeycolumns))
        else:
            if self.recdtype is None:
                df = df.reset_index()
                dtypes = df.dtypes.reset_index()
                dtypes.columns = ['tag', 'dtype']
            
                # Convert datetime columns with timezone to UTC naive datetime
                for col in df.columns:
                    if pd.api.types.is_datetime64_any_dtype(df[col]):
                        if df[col].dt.tz is not None:
                            df[col] = df[col].dt.tz_convert('UTC').dt.tz_localize(None)
                
                # convert object to string
                tags_obj = dtypes['tag'][dtypes['dtype'] == 'object'].values
                for tag in tags_obj:
                    try:
                        df[tag] = df[tag].astype(str)
                        df[tag] = df[tag].str.encode(encoding='utf-8', errors='ignore')
                    except Exception as e:
                        Logger.log.error(f'Table.df2records(): Could not convert {self.relpath} {tag} : {str(e)}!')
                    df[tag] = df[tag].astype('|S')
                    
                rec = np.ascontiguousarray(df.to_records(index=False))
                type_descriptors = [field[1] for field in rec]
                if '|O' in type_descriptors:
                    errmsg = f'Table.df2records(): Could not convert {self.relpath} |0 type to binary'
                    Logger.log.error(errmsg)
                    raise Exception(errmsg)
                        
                return rec
            else:
                df = df.reset_index()
                # Convert datetime columns with timezone to UTC naive datetime
                for col in df.columns:
                    if pd.api.types.is_datetime64_any_dtype(df[col]):
                        if df[col].dt.tz is not None:
                            df[col] = df[col].dt.tz_convert('UTC').dt.tz_localize(None)
                
                dtypes = self.recdtype
                
                # Handle schemaless columns if requested
                if extra_data is not None:
                    # Find columns not in the schema
                    extra_cols = [col for col in df.columns if col not in dtypes.names]
                    if len(extra_cols) > 0:
                        # VECTORIZED APPROACH: Use pandas built-in to_dict method
                        # Replace NaN with None for cleaner JSON serialization
                        extra_df = df[extra_cols].where(pd.notnull(df[extra_cols]), None)
                        # Convert to list of dictionaries in one operation
                        extra_data.extend(extra_df.to_dict('records'))
                
                rec = np.full((df.shape[0],), fill_value=np.nan, dtype=dtypes)
                for col in dtypes.names:
                    try:
                        if col in df.columns:
                            if pd.api.types.is_integer_dtype(dtypes[col])\
                                or pd.api.types.is_unsigned_integer_dtype(dtypes[col]):
                                df[col] = df[col].fillna(0)
                                
                            rec[col] = df[col].astype(dtypes[col])
                            
                    except Exception as e:
                        Logger.log.error(f'Table.df2records(): Could not convert {self.relpath} {col} : {str(e)}!')
                return rec
            
    def dict2records(self, list_of_dicts, extra_data=None):
        """
        Convert a list of dictionaries into a NumPy structured array (records) with validation and type handling.
        
        This method processes the list of dictionaries using pure NumPy operations, avoiding pandas.
        It verifies that the primary key columns exist in the dictionaries.
        
        If `self.recdtype` is None:
        - Automatically infers column types from the data.
        - String columns are converted to UTF-8 encoded byte strings.
        - The data is converted to a contiguous NumPy structured array.
        - If any object dtype remains in the resulting array, an Exception is raised.
        
        If `self.recdtype` is provided:
        - A NumPy structured array of the specified dtype is created, filled initially with zeros.
        - Columns are converted to the specified dtype, with missing values filled appropriately.
        - Columns not in `self.recdtype` are optionally collected into a list of dictionaries.
        - Errors during conversion are logged but do not halt processing.
        
        Parameters:
            list_of_dicts (list): List of dictionaries to convert. Each dictionary represents one record.
            extra_data (list, optional): If provided, columns not in `self.recdtype` will be added to this list
                                            as dictionaries (one per row).
        
        Returns:
            numpy.ndarray: A structured array representing the dictionary records
        """
        if not list_of_dicts:
            # Return empty array with correct dtype if available
            if self.recdtype is not None:
                return np.array([], dtype=self.recdtype)
            else:
                return np.array([])
        
        num_rows = len(list_of_dicts)
        
        if self.recdtype is None:
            # Auto-infer types from data
            # First pass: collect all unique column names
            all_columns = set()
            for d in list_of_dicts:
                all_columns.update(d.keys())
            
            # Check if primary key columns exist in the data
            missing_pkeys = [col for col in self.index.pkeycolumns if col not in all_columns]
            if missing_pkeys:
                raise Exception('Primary key columns %s must be present in the data!' % missing_pkeys)
            
            # Reorder columns to put primary keys first
            ordered_columns = self.index.pkeycolumns + [col for col in all_columns if col not in self.index.pkeycolumns]
            
            # Second pass: collect column data efficiently
            column_set = set(ordered_columns)
            column_data = {col: [None] * num_rows for col in ordered_columns}
            for i, d in enumerate(list_of_dicts):
                for k, v in d.items():
                    if k in column_set:
                        column_data[k][i] = v
            
            # Infer types and create dtype
            dtype_list = []
            for col in ordered_columns:
                values = column_data[col]
                non_none_values = [v for v in values if v is not None]
                
                if not non_none_values:
                    dtype_list.append((col, 'O'))
                    continue
                
                sample_val = non_none_values[0]
                if isinstance(sample_val, str):
                    max_len = max(len(str(v).encode('utf-8')) for v in non_none_values)
                    dtype_list.append((col, f'S{max_len}'))
                elif isinstance(sample_val, (int, np.integer)):
                    dtype_list.append((col, 'i8'))
                elif isinstance(sample_val, (float, np.floating)):
                    dtype_list.append((col, 'f8'))
                elif isinstance(sample_val, (bool, np.bool_)):
                    dtype_list.append((col, 'bool'))
                elif hasattr(sample_val, 'timestamp'):  # datetime-like
                    dtype_list.append((col, 'M8[ns]'))
                else:
                    dtype_list.append((col, 'O'))
            
            dt = np.dtype(dtype_list)
            rec = np.zeros(num_rows, dtype=dt)
            
            # Fill the array
            for col in ordered_columns:
                values = column_data[col]
                col_dtype = dt[col]
                
                if col_dtype.kind == 'S':  # String type
                    byte_values = []
                    for v in values:
                        if v is None:
                            byte_values.append(b'')
                        else:
                            try:
                                byte_values.append(str(v).encode('utf-8', errors='ignore'))
                            except Exception as e:
                                Logger.log.error(f'Table.dict2records(): Could not convert {self.relpath} {col} value {v}: {str(e)}!')
                                byte_values.append(b'')
                    rec[col] = byte_values
                elif col_dtype.kind == 'M':  # Datetime type
                    dt_values = []
                    for v in values:
                        if v is None:
                            dt_values.append(np.datetime64('NaT'))
                        else:
                            try:
                                if hasattr(v, 'timestamp'):
                                    # Convert to UTC if timezone-aware
                                    if hasattr(v, 'tz') and v.tz is not None:
                                        v = v.tz_convert('UTC').tz_localize(None)
                                    dt_values.append(np.datetime64(v))
                                else:
                                    dt_values.append(np.datetime64(v))
                            except Exception as e:
                                Logger.log.error(f'Table.dict2records(): Could not convert {self.relpath} {col} datetime {v}: {str(e)}!')
                                dt_values.append(np.datetime64('NaT'))
                    rec[col] = dt_values
                else:
                    # Numeric or boolean types
                    if col_dtype.kind in 'iu':  # Integer types
                        fill_val = 0
                    elif col_dtype.kind == 'f':  # Float types
                        fill_val = np.nan
                    elif col_dtype.kind == 'b':  # Boolean
                        fill_val = False
                    else:
                        fill_val = None
                    
                    filled_values = []
                    for v in values:
                        if v is None:
                            filled_values.append(fill_val)
                        else:
                            filled_values.append(v)
                    try:
                        rec[col] = filled_values
                    except Exception as e:
                        Logger.log.error(f'Table.dict2records(): Could not convert {self.relpath} {col}: {str(e)}!')
                        # Fill with default values
                        rec[col] = fill_val
            
            # Check for remaining object types
            if any(dt[name].kind == 'O' for name in dt.names):
                errmsg = f'Table.dict2records(): Could not convert {self.relpath} object types to binary'
                Logger.log.error(errmsg)
                raise Exception(errmsg)
                
            return rec
            
        else:
            # Optimized predefined schema path
            dtypes = self.recdtype
            names = dtypes.names
            n = num_rows
            rec = np.empty(n, dtype=dtypes)

            schema_set = set(names)
            missing_pkeys = set(self.index.pkeycolumns)

            # Column accumulators
            cols = {col: [] for col in names}
            extras = [] if extra_data is not None else None

            for d in list_of_dicts:
                # Track pkeys
                dpkeys = d.keys()
                for pk in tuple(missing_pkeys):
                    if pk in dpkeys:
                        missing_pkeys.discard(pk)

                # Append values for schema fields
                for col in names:
                    cols[col].append(d.get(col))

                if extras is not None:
                    extra = {k: (None if (isinstance(v, float) and np.isnan(v)) else v)
                             for k, v in d.items() if k not in schema_set}
                    extras.append(extra)

            if missing_pkeys:
                raise Exception('Primary key columns %s must be present in the data!' % list(missing_pkeys))

            # Vectorized assignment per dtype kind
            for col in names:
                values = cols[col]
                col_dtype = dtypes[col]
                k = col_dtype.kind
                try:
                    if k in 'iu':  # integers
                        rec[col] = [0 if v is None else v for v in values]
                    elif k == 'f':
                        rec[col] = [np.nan if v is None else v for v in values]
                    elif k == 'b':
                        rec[col] = [False if v is None else v for v in values]
                    elif k == 'S':
                        rec[col] = [b'' if v is None else str(v).encode('utf-8', 'ignore') for v in values]
                    elif k == 'M':
                        out = []
                        ap = out.append
                        for v in values:
                            if v is None:
                                ap(np.datetime64('NaT'))
                            else:
                                try:
                                    if hasattr(v, 'tz') and v.tz is not None:
                                        v = v.tz_convert('UTC').tz_localize(None)
                                    ap(np.datetime64(v))
                                except Exception:
                                    ap(np.datetime64('NaT'))
                        rec[col] = out
                    else:
                        rec[col] = values
                except Exception as e:
                    Logger.log.error(f'Table.dict2records(): Could not convert {self.relpath} {col}: {str(e)}!')
                    if k in 'iu':
                        rec[col] = 0
                    elif k == 'f':
                        rec[col] = np.nan
                    elif k == 'b':
                        rec[col] = False
                    elif k == 'M':
                        rec[col] = np.datetime64('NaT')
                    elif k == 'S':
                        rec[col] = b''

            if extra_data is not None and extras:
                extra_data.extend(extras)
            return rec

    def any2records(self, new_records):
        """
        Convert various data formats into a list of records compatible with the table's schema.
        
        This method accepts input data in multiple formats, including pandas DataFrames, dictionaries,
        lists of dictionaries, NumPy structured arrays, and single dictionaries. It processes the input
        accordingly and converts it into a list of records that match the table's schema.
        
        Parameters:
            any_data (pd.DataFrame, dict, list of dicts, np.ndarray): The input data to convert.
            extra_data (list, optional): If provided, columns not in `self.recdtype` will be added to this list
                                         as dictionaries (one per row).
        """
        # convert to same dtype record
        dict_list = []
        if isinstance(new_records, dict):
            # single record dict to list of dicts
            new_records = [new_records]

        if isinstance(new_records, list):
            new_records = self.dict2records(new_records, dict_list)
            
        elif isinstance(new_records, pd.DataFrame):                
            new_records = self.df2records(new_records, dict_list)
        
        if not self.recdtype is None:
            if (self.recdtype != new_records.dtype):
                new_records = self.convert(new_records, dict_list)

        return new_records, dict_list
    
    def convert(self, new_records, extra_data=None):
        """
        Converts fields of a structured NumPy array `new_records` to match the data types defined in `self.recdtype`.
        
        For each column in `self.recdtype.names` that exists in `new_records.dtype.names`, attempts to:
        - Replace byte-string representations of 'nan' with 0 for integer fields.
        - Replace byte-string 'True' with 1 and 'False' with 0 for integer fields.
        - Cast the column data to the corresponding dtype in `self.recdtype`.
        
        If conversion fails for any column, logs an error message.
        
        Parameters:
            new_records (np.ndarray): Structured NumPy array with new data to convert.
            extra_data (list, optional): If provided, columns not in `self.recdtype` will be added to this list
                                            as dictionaries (one per row).
        
        Returns:
            np.ndarray: Structured array with the same shape as `new_records` and dtype `self.recdtype`,
                        containing the converted data.
        """
        if self.recdtype is None:
            return new_records
        
        rec = np.full((new_records.size,), fill_value=np.nan, dtype=self.recdtype)
        for col in self.recdtype.names:
            if col in new_records.dtype.names:
                try:
                    if np.issubdtype(self.recdtype[col], np.integer):
                        nanidx = new_records[col] == b'nan'
                        new_records[col][nanidx] = 0
                        trueidx = new_records[col] == b'True'
                        new_records[col][trueidx] = 1
                        falseidx = new_records[col] == b'False'
                        new_records[col][falseidx] = 0
                    rec[col] = new_records[col].astype(self.recdtype[col])
                except Exception as e:
                    Logger.log.error(f'SharedNumpy.convert(): Could not convert {col} on {self.relpath}: {str(e)}!')
        
        if extra_data is not None:
            # check for columns present in new_records but not in self.recdtype
            extra_cols = [col for col in new_records.dtype.names if col not in self.recdtype.names]            
            if len(extra_cols) > 0:
                # VECTORIZED APPROACH 1: Using list comprehension with zip
                # This is typically the fastest for structured arrays
                extra_data.extend([
                    dict(zip(extra_cols, row)) 
                    for row in new_records[extra_cols].tolist()
                ])
                
        return rec
    
    def remove_invalid_records(self, new_records, dict_list):
        """
        Remove records with invalid primary key values from the input array.
        
        This method checks each record in the input structured NumPy array `new_records` to ensure that
        all primary key fields (as defined in `self.pkey`) are valid. A primary key field is considered
        invalid if it is NaN for float types or zero/empty for integer and string types. Records with
        any invalid primary key fields are excluded from the returned array.
        
        Parameters:
            new_records (np.ndarray): Structured NumPy array containing the records to validate.

        """
        utcnow = np.datetime64(time.time_ns(), 'ns') # add 1 second tolerance
        # fill mtime
        nidx = np.isnat(new_records['mtime'])
        if nidx.any():
            new_records['mtime'][nidx] = utcnow

        # remove invalid mtime
        invalididx = new_records['mtime'].astype(np.int64) > utcnow.astype(np.int64) + 1000000000
        if invalididx.any():
            new_records[invalididx]['mtime'] = utcnow
            Logger.log.warning('%s: %d records with invalid mtime check your system clock!' \
                                % (self.relpath, invalididx.sum()))
            #remove from dict_list
            if self.is_schemaless and dict_list:
                dict_list = [d for i, d in enumerate(dict_list) if not invalididx[i]]
            
        # check for null date
        if 'date' in DATABASE_PKEYS[self.database]:
            invalididx = np.isnat(new_records['date'])
            invalididx = invalididx | (new_records['date'] < self.mindate)
            invalididx = invalididx | (new_records['date'] >= self.maxdate)
            if invalididx.any():
                new_records = new_records[~invalididx]
                # remove from dict_list
                if not dict_list is None:
                    dict_list = [d for i, d in enumerate(dict_list) if not invalididx[i]]

            # round date to period
            new_records['date'] = (new_records['date'].astype(np.int64) // self.periodns) * self.periodns
        
        return new_records, dict_list
    
    def tags2df(self, dt, seltags, datetags=None):
        """
        Convert selected tags' records at a given datetime into two DataFrames.
        
        Parameters:
            dt (datetime-like): The datetime index to select records from.
            seltags (list of str): List of tags to extract data for.
            datetags (list of str, optional): Subset of tags whose 'value' should be converted from timestamps to pandas Timestamps.
        
        Returns:
            tuple:
                - df (pd.DataFrame): DataFrame indexed by the union of all record indices, containing the 'value' for each selected tag.
                - dfmtime (pd.DataFrame): DataFrame with the same index as df, containing the modification time ('mtime') for each selected tag.
        
        Notes:
            - If a tag is in datetags, its 'value' entries are converted from UNIX timestamps to pandas Timestamps.
            - Errors during data retrieval for any tag are logged but do not interrupt processing.
        """
        idx = pd.Index([])
        df = pd.DataFrame(columns=seltags)
        dfmtime = pd.DataFrame(columns=seltags)
        tag = seltags[0]        
        for tag in seltags:
            try:
                rec = self.loc[dt,tag]
                if len(rec)>0:            
                    values = self.records2df(rec).loc[dt].droplevel(0)
                    idx = idx.union(values.index)
                    df = df.reindex(idx)    
                    if not datetags is None:
                        if tag in datetags:
                            values['value'] = values['value'].apply(lambda x: pd.Timestamp.fromtimestamp(x))
                    df[tag] = values['value']
                    dfmtime[tag] = values['mtime']
            except Exception as e:
                Logger.log.error('Could not get %s %s!' % (tag,e))
        return df, dfmtime

    ############### LOCK ###############
    def acquire(self):
        """
        Acquire a lock on the shared data resource.
        
        This method uses the `acquire` function of the `shareddata` object to obtain a lock,
        ensuring synchronized access to the shared resource identified by the mutex, process ID, and relative path.
        """
        self.shareddata.acquire(self.mutex, self.pid, self.relpath)

    def release(self):
        """
        Releases the lock or resource associated with the current process and path.
        
        This method invokes the `release` method of the `shareddata` object, providing
        the current mutex, process ID (`pid`), and relative path (`relpath`) to ensure
        the proper release of the held resource.
        
        Does not return any value.
        """
        self.shareddata.release(self.mutex, self.pid, self.relpath)

    ############### SUBSCRIBE ###############

    def subscribe(self, host, port, lookbacklines=1000, 
                  lookbackdate=None, method='websocket', snapshot=False, bandwidth=1e6, protocol='http'):
        """
        Starts a subscription thread to receive data from a specified host and port using the given method.
        
        Parameters:
            host (str): The hostname or IP address to connect to.
            port (int): The port number to connect to.
            lookbacklines (int, optional): Number of lines to look back on subscription start. Default is 1000.
            lookbackdate (datetime or None, optional): Specific date to look back to on subscription start. Default is None.
            method (str, optional): Connection method to use; one of 'socket', 'websocket', or 'api'. Default is 'websocket'.
            snapshot (bool, optional): Whether to take a snapshot of the data on subscription start. Default is False.
            bandwidth (float, optional): Bandwidth limit for the subscription in bytes per second. Default is 1e6.
            protocol (str, optional): Protocol to use when method is 'api'. Default is 'http'.
        
        Behavior:
            - If no subscription thread is currently running, starts a new thread based on the specified method.
            - Logs the start of the subscription or any errors encountered.
            - If a subscription is already running, logs an error and does not start a new one.
        """
        if self.subscription_thread is None:
            if method == 'socket':
                self.subscription_thread = threading.Thread(
                    target=ClientSocket.subscribe_table_thread,
                    args=(self, host, port, lookbacklines, lookbackdate, snapshot, bandwidth),
                )
                self.subscription_thread.start()
                Logger.log.info('Socket to %s:%s -> %s started...' % (host,str(port),self.relpath))
            elif method == 'websocket':
                def websocket_thread():
                    asyncio.run(ClientWebSocket.subscribe_table_thread(
                        self, host, port, lookbacklines, lookbackdate, snapshot, bandwidth,  protocol))
                
                self.subscription_thread = threading.Thread(
                    target=websocket_thread,                    
                )
                self.subscription_thread.start()                    
                Logger.log.info('Websocket to %s:%s -> %s started...' % (host,str(port),self.relpath))
            elif method == 'api':
                self.subscription_thread = threading.Thread(
                    target=ClientAPI.subscribe_table_thread,
                    args=(self, host, port, lookbacklines, lookbackdate, snapshot, bandwidth, protocol),
                )
                self.subscription_thread.start()
                Logger.log.info('API to %s:%s -> %s started...' % (host,str(port),self.relpath))
            else:
                Logger.log.error('Invalid method %s to %s:%s -> %s !!!' % (method,host,str(port),self.relpath))
        else:
            Logger.log.error('Subscription to %s:%s -> %s already running!' % (host,str(port),self.relpath))

    def free(self):
        """
        Frees the table's resources including shared memory, indices, file handles, and closes BSON files.

        This method should be called when the table is no longer needed to ensure proper cleanup
        of system resources. It closes memory mappings, file handles, and releases any allocated
        shared memory segments. For schemaless tables, it also closes BSON files.

        Arguments: None
        Returns: None
        """
        try:
            self.release()

            if hasattr(self, 'records') and self.records is not None:
                self.records.free()

            if self.type == 1:  # DISK type
                if hasattr(self, 'shf_data') and self.shf_data is not None:
                    del self.shf_data

            if hasattr(self, 'shm_mutex') and self.shm_mutex is not None:
                if self.ismalloc:
                    if hasattr(self, 'mutex'):
                        self.shareddata.free_mutex(self.shm_mutex, self.mutex, self.pid)
                else:
                    self.shareddata.free_mutex(self.shm_mutex, self.mutex, self.pid)

            # Close BSON file handle if open (for schemaless tables)
            if self.is_schemaless and hasattr(self, 'bson_file') and self.bson_file is not None:
                self.bson_file.close()
                self.bson_file = None

            # Clean up temporary attributes
            for attr in ['shm_mutex', 'mutex', 'records', 'index', 'hdr', 'move_to_memory']:
                if hasattr(self, attr):
                    setattr(self, attr, None)

        except Exception as e:
            Logger.log.error(f'Table.free() {self.relpath}: {e}')

    def publish(self, host, port=None, lookbacklines=1000, 
                  lookbackdate=None, method='websocket', snapshot=False, 
                  bandwidth=1e6, protocol='http',max_requests_per_minute=100):
        """
        '''
        Starts a publishing thread to send data to a specified host and port using the chosen method.
        
        Parameters:
            host (str): The target host address to publish data to.
            port (int, optional): The target port number. Defaults to None.
            lookbacklines (int, optional): Number of lines to look back and publish initially. Defaults to 1000.
            lookbackdate (datetime or None, optional): Specific date/time to look back from. Defaults to None.
            method (str, optional): The publishing method to use. One of 'socket', 'websocket', or 'api'. Defaults to 'websocket'.
            snapshot (bool, optional): Whether to send a snapshot of the data initially. Defaults to False.
            bandwidth (float, optional): Bandwidth limit in bits per second. Defaults to 1e6.
            protocol (str, optional): Protocol to use when method is 'api'. Defaults to 'http'.
            max_requests_per_minute (int, optional): Maximum API requests allowed per minute when method is 'api'. Defaults to 100.
        
        Behavior:
            - If no publishing thread is currently running, starts a new thread based on the specified method.
            - Logs the start of the publishing thread or errors
        """
        if self.publish_thread is None:
            if method == 'socket':
                self.publish_thread = threading.Thread(
                    target=ClientSocket.publish_table_thread,
                    args=(self, host, port, lookbacklines, lookbackdate, snapshot,bandwidth),
                )
                self.publish_thread.start()
                Logger.log.info('Socket to %s:%s -> %s started...' % (host,str(port),self.relpath))

            elif method == 'websocket':
                def websocket_thread():
                    asyncio.run(ClientWebSocket.publish_table_thread(
                        self, host, port, lookbacklines, lookbackdate, snapshot, bandwidth, protocol))
                self.publish_thread = threading.Thread(
                    target=websocket_thread,                    
                )
                self.publish_thread.start()                    
                Logger.log.info('Websocket to %s:%s -> %s started...' % (host,str(port),self.relpath))

            elif method == 'api':
                self.publish_thread = threading.Thread(
                    target=ClientAPI.publish_table_thread,
                    args=(self, host, port, lookbacklines, lookbackdate, snapshot,bandwidth, protocol, max_requests_per_minute),
                )
                self.publish_thread.start()
                Logger.log.info('API to %s:%s -> %s started...' % (host,str(port),self.relpath))
                
            else:
                Logger.log.error('Invalid method %s to %s:%s -> %s !!!' % (method,host,str(port),self.relpath))
        else:
            Logger.log.error('Subscription to %s:%s -> %s already running!' % (host,str(port),self.relpath))
