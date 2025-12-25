import os
import io
import hashlib
import gzip
import shutil
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from pandas.tseries.offsets import BDay
from threading import Thread
from tqdm import tqdm

from SharedData.Logger import Logger
from SharedData.TimeSeriesDisk import TimeSeriesDisk
from SharedData.IO.AWSS3 import S3Upload, S3Download, UpdateModTime


class TimeseriesContainer:

    """
    Container class for managing time series data from various sources and periods, supporting both disk and shared memory storage types.
    
    This class pre-creates complete time indices from the specified startDate through the end of the current year,
    ensuring efficient access to all time periods within this range for data operations.
    
    Attributes:
        shareddata: Shared data manager instance.
        user (str): Username or namespace, default is 'master'.
        database (str): Database name.
        period (str): Time period granularity ('W1', 'D1', 'M15', 'M1').
        source (str): Data source identifier.
        type (str): Storage type, either 'DISK' or 'MEMORY'.
        startDate (pd.Timestamp): Start date for the time index.
        tags (dict): Dictionary mapping tag names to their time series data handlers.
        timeidx (dict): Dictionary of time indices keyed by startDate, each spanning from startDate to end of current year.
        ctimeidx (dict): Dictionary of continuous time indices keyed by startDate, each spanning from startDate to end of current year.
        periodseconds (int): Number of seconds in the specified period.
        default_startDate (pd.Timestamp): Default start date based on period
    """
    def __init__(self, shareddata, database, period, source,
                 user='master',type='DISK', startDate=None):

        """
        '''
        Initialize the data handler with specified parameters and set up time indexing.
        
        Parameters:
            shareddata: Shared data resource or object used across instances.
            database (str): Name or identifier of the database to connect to.
            period (str): Time period for data aggregation ('W1', 'D1', 'M15', 'M1').
            source (str): Data source identifier.
            user (str, optional): Username for database access. Defaults to 'master'.
            type (str, optional): Type of data storage or retrieval method. Defaults to 'DISK'.
            startDate (str or pd.Timestamp, optional): Starting date for data indexing. Defaults to None.
        
        Attributes set:
            tags (dict): Dictionary to store data tags.
            timeidx (dict): Dictionary for time indexing.
            ctimeidx (dict): Dictionary for continuous time indexing.
            periodseconds (int): Number of seconds in the specified period.
            default_startDate (pd.Timestamp): Default start date based on period.
            startDate (pd.Timestamp): Actual start date used for indexing.
            loaded (bool): Flag indicating if data has been loaded.
        
        Raises:
            Exception: If the mutex type conflicts with an already loaded type.
        
        Calls:
            getTimeIndex(startDate
        """
        self.shareddata = shareddata
        self.user = user
        self.database = database
        self.period = period
        self.source = source
        self.type = type

        # Initialize mutex for process safety
        self.shm_name = self.user + '/' + self.database + '/' \
            + self.period + '/' + self.source + '/timeseries'
        if os.name == 'posix':
            self.shm_name = self.shm_name.replace('/', '\\')
        
        self.pid = os.getpid()
        [self.shm_mutex, self.mutex, self.ismalloc] = \
            self.shareddata.mutex(self.shm_name, self.pid)
        
        # Set mutex type - 1 for DISK, 2 for MEMORY
        mutex_type = 1 if self.type == 'DISK' else 2
        if self.mutex['type'] == 0:  # type not initialized
            self.mutex['type'] = mutex_type
        elif self.mutex['type'] != mutex_type:
            if self.mutex['type'] == 1:
                errmsg = f'TimeseriesContainer {self.shm_name} is loaded as DISK!'
                Logger.log.error(errmsg)
                raise Exception(errmsg)
            elif self.mutex['type'] == 2:
                errmsg = f'TimeseriesContainer {self.shm_name} is loaded as MEMORY!'
                Logger.log.error(errmsg)
                raise Exception(errmsg)
            else:
                errmsg = f'TimeseriesContainer {self.shm_name} is loaded with unknown type!'
                Logger.log.error(errmsg)
                raise Exception(errmsg)

        # DATA DICTIONARY
        # tags[tag]
        self.tags = {}

        # TIME INDEX
        self.timeidx = {}
        self.ctimeidx = {}
        if self.period == 'W1':
            self.periodseconds = 7*60*60*24
            self.default_startDate = pd.Timestamp('1995-01-01')
        elif self.period == 'D1':
            self.periodseconds = 60*60*24
            self.default_startDate = pd.Timestamp('1995-01-01')
        elif self.period == 'M15':
            self.periodseconds = 60*15
            self.default_startDate = pd.Timestamp('2010-01-01')
        elif self.period == 'M1':
            self.periodseconds = 60
            self.default_startDate = pd.Timestamp('2010-01-01')

        if startDate is None:
            self.startDate = self.default_startDate
        else:
            self.startDate = pd.Timestamp(startDate)            
        self.getTimeIndex(self.startDate)
        self.getContinousTimeIndex(self.startDate)
        self.loaded = False        

        self.release()

    def getTimeIndex(self, startDate):
        """
        '''
        Generate and cache a pandas Index of business time periods starting from a given date.
        
        This method pre-creates and caches a complete time index from the specified startDate
        through the end of the current year (January 1st of the next year). If the time index
        for the specified startDate does not exist in the cache (self.timeidx), this method
        creates it based on the object's period attribute, which can be 'D1' (daily),
        'M15' (15-minute intervals), or 'M1' (1-minute intervals).
        
        The time index spans the entire period from startDate to the end of the current year,
        ensuring that all possible time points within this range are available for data operations.
        
        For 'M15' and 'M1' periods, the index is filtered to include only times between 7 AM and 10 PM
        on weekdays (Monday to Friday). The method also sets self.periodseconds to the number of seconds
        in each period (86400 for daily, 900 for 15 minutes, and 60 for 1 minute).
        
        Parameters:
            startDate (str or datetime-like): The start date from which to generate the time index.
        
        Returns:
            pd.Index: A pandas Index object containing all time periods from
        """
        if not startDate in self.timeidx.keys():
            lastdate = pd.Timestamp(datetime.now().year+1, 1, 1)

            if self.period == 'D1':
                self.timeidx[startDate] = pd.Index(
                    pd.bdate_range(start=startDate,
                                   end=np.datetime64(lastdate)))
                self.periodseconds = 60*60*24

            elif self.period == 'M15':
                self.timeidx[startDate] = pd.Index(
                    pd.bdate_range(start=startDate,
                                   end=np.datetime64(lastdate), freq='15min'))
                idx = (self.timeidx[startDate].hour > 6)
                idx = (idx) & (self.timeidx[startDate].hour < 22)
                idx = (idx) & (self.timeidx[startDate].day_of_week < 5)
                self.timeidx[startDate] = self.timeidx[startDate][idx]
                self.periodseconds = 60*15

            elif self.period == 'M1':
                self.timeidx[startDate] = pd.Index(
                    pd.bdate_range(start=startDate,
                                   end=np.datetime64(lastdate), freq='1min'))
                idx = (self.timeidx[startDate].hour > 6)
                idx = (idx) & (self.timeidx[startDate].hour < 22)
                idx = (idx) & (self.timeidx[startDate].day_of_week < 5)
                self.timeidx[startDate] = self.timeidx[startDate][idx]
                self.periodseconds = 60

        return self.timeidx[startDate]

    def getContinousTimeIndex(self, startDate):
        """
        Generate and cache a continuous time index array starting from the given startDate.
        
        This method pre-creates a continuous time index that spans from the specified startDate
        through the end of the current year. If the continuous time index for the specified
        startDate does not exist in the cache (self.ctimeidx), this method computes it by:
        - Obtaining the original time index corresponding to startDate (which covers the full year).
        - Calculating the number of periods elapsed since startDate based on the time difference and the defined period length (self.periodseconds).
        - Creating a NumPy array initialized with NaNs, sized to cover all periods from startDate to end of current year.
        - Filling the array at calculated period positions with sequential indices.
        
        The resulting continuous index provides a complete mapping for all time periods within
        the year, enabling efficient data access and alignment operations.
        
        Parameters:
            startDate (Timestamp or compatible datetime-like): The starting date/time from which to generate the continuous time index.
        
        Returns:
            numpy.ndarray: An array representing the continuous time index from startDate to end of current year, with NaNs for missing periods.
        """
        if not startDate in self.ctimeidx.keys():
            _timeidx = self.getTimeIndex(startDate)
            nsec = (_timeidx - startDate).astype(np.int64)
            periods = (nsec/(10**9)/self.periodseconds).astype(np.int64)
            self.ctimeidx[startDate] = np.empty(max(periods)+1)
            self.ctimeidx[startDate][:] = np.nan
            self.ctimeidx[startDate][periods.values] = np.arange(len(periods))
        return self.ctimeidx[startDate]

    def get_path(self):
        """
        Constructs and returns the filesystem path for the timeseries data based on the object's attributes.
        
        The method builds a path using the environment variable 'DATABASE_FOLDER' combined with the user, database, period, source, and 'timeseries' subdirectories.
        
        If the object's type attribute is 'DISK', it ensures that the parent directory of the constructed path exists by creating it if necessary.
        
        Returns:
            tuple: A tuple containing:
                - path (Path): The constructed Path object pointing to the timeseries directory.
                - shm_name (str): The shared memory name string with platform-specific separators.
        """
        path = Path(os.environ['DATABASE_FOLDER'])
        path = path / self.user
        path = path / self.database
        path = path / self.period
        path = path / self.source
        path = path / 'timeseries'
        path = Path(str(path).replace('\\', '/'))
        if (self.type == 'DISK'):
            os.makedirs(path.parent, exist_ok=True)
            
        return path, self.shm_name

    # READ
    def load(self):
        # read if not loaded
        """
        Load data into the object. If the data source type is 'DISK', it reads the data from disk and initializes TimeSeriesDisk objects for each binary file found in the specified path, storing them in the tags dictionary. If the data source type is not 'DISK', it raises a NotImplementedError. Handles exceptions by logging errors and re-raising them after releasing resources.
        """
        errmsg = ''
        try:
            self.acquire()
            
            if self.type == 'DISK':
                self.read()
                
                path, shm_name = self.get_path()
                tagslist = path.rglob('*.bin')
                for tag in tagslist:
                    if tag.is_file():
                        tagname = str(tag).replace(str(path),'').replace('.bin','').replace('\\','/')
                        if (tagname[0] == '/') | (tagname[0] == '\\'):
                            tagname = tagname[1:]
                        if not tagname in self.tags.keys():
                            self.tags[tagname] = TimeSeriesDisk(self.shareddata, self, self.database,
                                                        self.period, self.source, tag=tagname, user=self.user)
            else:
                raise NotImplementedError("Loading from non-DISK sources is not implemented.")
                
        except Exception as e:
            errmsg = f'Could not load timeseries container {self.shm_name}\n{e}!'
            Logger.log.error(errmsg)
        finally:
            self.release()
            if errmsg != '':
                raise Exception(errmsg)

    def read(self):
        """
        Reads and processes time series data segments ('head' and 'tail') from S3 or local storage.
        
        The method attempts to download gzipped binary files for both 'head' and 'tail' segments from S3. If successful, it decompresses these files with a progress bar and writes the decompressed data either to memory or disk depending on the instance's type attribute ('MEMORY' or 'DISK'). If downloading fails or is not required, it falls back to reading the files from local storage if available.
        
        After obtaining the data streams, it processes them using the `read_io` method. For instances of type 'MEMORY', it writes data to shared memory containers and cleans up the placeholder files by truncating them to a single null byte while preserving modification times. For 'DISK' type, it manages placeholder files accordingly.
        
        Finally, the method logs the total amount of data read and the throughput in MB/s.
        
        Returns:
            None
        """
        tini = time.time()
        datasize = 1
        path, shm_name = self.get_path()
        headpath = Path(str(path)+'_head.bin')
        tailpath = Path(str(path)+'_tail.bin')
        head_io = None
        tail_io = None        

        [head_io_gzip, head_local_mtime, head_remote_mtime] = \
            S3Download(str(headpath)+'.gzip', str(headpath), False)
        if not head_io_gzip is None:
            head_io = io.BytesIO()
            total_size = head_io_gzip.seek(0, 2)
            head_io_gzip.seek(0)
            with gzip.GzipFile(fileobj=head_io_gzip, mode='rb') as gz:
                with tqdm(total=total_size, unit='B', unit_scale=True,
                            desc='Unzipping %s' % (shm_name), dynamic_ncols=True) as pbar:
                    chunk_size = int(1024*1024)
                    while True:
                        chunk = gz.read(chunk_size)
                        if not chunk:
                            break
                        head_io.write(chunk)
                        pbar.update(len(chunk))                                    
            with open(headpath, 'wb') as f:
                    f.write(b'\x00')            
            UpdateModTime(headpath, head_remote_mtime)

        [tail_io_gzip, tail_local_mtime, tail_remote_mtime] = \
            S3Download(str(tailpath)+'.gzip', str(tailpath), False)
        if not tail_io_gzip is None:
            tail_io = io.BytesIO()
            tail_io_gzip.seek(0)
            with gzip.GzipFile(fileobj=tail_io_gzip, mode='rb') as gz:
                shutil.copyfileobj(gz, tail_io)
            with open(tailpath, 'wb') as f:
                f.write(b'\x00')
            UpdateModTime(tailpath, tail_remote_mtime)

        
        if (head_io is None):
            # read local
            if os.path.isfile(str(headpath)):
                if (headpath.stat().st_size > 1):
                    head_io = open(str(headpath), 'rb')                

        if (tail_io is None):
            if os.path.isfile(str(tailpath)):
                if (tailpath.stat().st_size > 1):
                    tail_io = open(str(tailpath), 'rb')                

        if not head_io is None:
            datasize += self.read_io(head_io, headpath, shm_name, ishead=True)
            # delete head file if type was memory 
            if (headpath.stat().st_size > 1):
                head_io.close()
                mtime = headpath.stat().st_mtime
                with open(headpath, 'wb') as f:                            
                    f.write(b'\x00')
                os.utime(headpath, (mtime, mtime))


        if not tail_io is None:
            datasize += self.read_io(tail_io, tailpath, shm_name, ishead=False)
            # delete tail file if type was memory 
            if (tailpath.stat().st_size > 1):
                tail_io.close()
                mtime = tailpath.stat().st_mtime
                with open(tailpath, 'wb') as f:                            
                    f.write(b'\x00')
                os.utime(tailpath, (mtime, mtime))

        te = time.time()-tini+0.000001
        datasize = datasize/(1024*1024)
        Logger.log.debug('read %s/%s %.2fMB in %.2fs %.2fMBps ' %
                         (self.source, self.period, datasize, te, datasize/te))

    def read_io(self, io_obj, path, shm_name, ishead=True):
        """
        Reads and verifies timeseries data from a binary I/O object, validates its integrity using an MD5 hash, 
        and loads the data into the object's tags as disk-backed timeseries.
        
        Supports both V1 (legacy) and V3 (new) bundle formats with automatic detection.
        
        V1 Bundle Format (Legacy):
        - For each tag: separator(1), [tag_len, idx_len, cols_len, r, c], tag, index, columns, C-ordered data
        - Terminator: separator(0), MD5 hash
        
        V3 Bundle Format (Current):
        - Version marker (3)
        - For each tag: separator(1), [tag_len, r, c], tag, index, null-terminated columns, F-ordered data
        - Terminator: separator(0), MD5 hash
        
        Parameters:
            io_obj (io.BufferedIOBase): A binary I/O object containing the serialized timeseries data.
            path (str): The file path or identifier associated with the data (not used directly in this method).
            shm_name (str): Name of the shared memory segment used for logging and verification messages.
            ishead (bool, optional): Indicates if the data being read is the initial header load. Defaults to True.
        
        Returns:
            int: The size in bytes of the timeseries data read (excluding the trailing 24 bytes used for hash and metadata).
        
        Raises:
            Exception: If the MD5 hash verification fails, indicating data corruption.
            Exception: If the object's type is not 'DISK', as other types are not implemented.
        """
        datasize = 0
        # read
        io_obj.seek(0)
        io_data = io_obj.read()
        _io_data = io_data[:-16]  # Exclude MD5 hash (16 bytes)
        datasize = len(_io_data)
        datasizemb = datasize/(1024*1024)
        
        # Verify MD5 hash
        if datasizemb > 100:
            message = 'Verifying:%iMB %s' % (datasizemb, shm_name)
            block_size = 100 * 1024 * 1024
            nb_total = datasize
            read_bytes = 0
            _m = hashlib.md5()
            with tqdm(total=nb_total, unit='B', unit_scale=True, desc=message) as pbar:
                while read_bytes < nb_total:
                    chunk_size = min(block_size, nb_total-read_bytes)
                    _m.update(_io_data[read_bytes:read_bytes+chunk_size])
                    read_bytes += chunk_size
                    pbar.update(chunk_size)
            _m = _m.digest()
        else:
            _m = hashlib.md5(_io_data).digest()  # Hash the data without the trailing 16 bytes
        
        m = io_data[-16:]
        if not self.compare_hash(m, _m):
            Logger.log.error('Timeseries file %s corrupted!' % (shm_name))
            raise Exception('Timeseries file %s corrupted!' % (shm_name))
        
        io_obj.seek(0)
        
        # Detect bundle format version
        first_value = np.frombuffer(io_obj.read(8), dtype=np.int64)[0]
        
        if first_value == 3:
            # V3 bundle format
            Logger.log.debug(f'Reading V3 bundle format for {shm_name}')
            self._read_io_v3(io_obj, ishead)
        elif first_value == 1:
            # V1 bundle format (legacy) - first_value is actually the separator
            Logger.log.debug(f'Reading V1 bundle format for {shm_name}, will convert to V3')
            io_obj.seek(0)  # Reset to read from beginning
            self._read_io_v1(io_obj, ishead)
        else:
            raise Exception(f'Unknown bundle format version: {first_value}')
        
        io_obj.close()
        return datasize

    def _read_io_v3(self, io_obj, ishead):
        """
        Read V3 bundle format.
        
        Format:
        - Version marker (3) - already read
        - For each tag:
          - Separator (1)
          - Header: [tag_length, rows, cols]
          - Tag name
          - Index (int64 timestamps)
          - Column names (null-terminated CSV)
          - Data (Fortran-ordered float64)
        - Terminator (0)
        """
        separator = np.frombuffer(io_obj.read(8), dtype=np.int64)[0]
        
        while separator == 1:
            # Read header: tag_length, rows, cols
            header = np.frombuffer(io_obj.read(24), dtype=np.int64)
            nbtag = header[0]
            r = header[1]
            c = header[2]
            
            # Read tag name
            tag_b = io_obj.read(int(nbtag))
            tag = tag_b.decode(encoding='UTF-8', errors='ignore')
            
            # Read index
            idx_b = io_obj.read(int(r * 8))
            idx = pd.to_datetime(np.frombuffer(idx_b, dtype=np.int64))
            
            # Read column names (null-terminated CSV)
            cols_bytes = bytearray()
            while True:
                byte = io_obj.read(1)
                if byte == b'\x00' or not byte:
                    break
                cols_bytes.extend(byte)
            cols_str = cols_bytes.decode('UTF-8', errors='ignore')
            cols = cols_str.split(',')
            
            # Read data (Fortran-ordered)
            total_bytes = int(r * c * 8)
            data_bytes = io_obj.read(total_bytes)
            
            # Reshape as Fortran-ordered to match the way it was written
            data = np.frombuffer(data_bytes, dtype=np.float64).reshape((r, c), order='F')
            
            # Create DataFrame
            df = pd.DataFrame(data, index=idx, columns=cols)
            
            # Store in tags
            if self.type == 'DISK':
                if ishead:
                    self.tags[tag] = TimeSeriesDisk(self.shareddata, self, self.database,
                                                    self.period, self.source, tag=tag, 
                                                    value=df, user=self.user, overwrite=True)
                else:
                    if tag not in self.tags.keys():
                        self.tags[tag] = TimeSeriesDisk(self.shareddata, self, self.database,
                                                        self.period, self.source, tag=tag, 
                                                        value=df, user=self.user, overwrite=True)
                    else:
                        data = self.tags[tag].data
                        iidx = df.index.intersection(data.index)
                        icol = df.columns.intersection(data.columns)
                        data.loc[iidx, icol] = df.loc[iidx, icol].copy()
            else:
                raise Exception(f'Not implemented for {self.type} type')
            
            # Read next separator
            separator = np.frombuffer(io_obj.read(8), dtype=np.int64)[0]

    def _read_io_v1(self, io_obj, ishead):
        """
        Read V1 (legacy) bundle format and convert to V3 local format.
        
        V1 Format:
        - For each tag:
          - Header: [separator(1), tag_len, idx_len, cols_len, rows, cols]
          - Tag name
          - Index (int64 timestamps)
          - Column names (CSV string, NOT null-terminated)
          - Data (C-ordered float64)
        - Terminator: [0]
        """
        separator = np.frombuffer(io_obj.read(8), dtype=np.int64)[0]
        
        while separator == 1:
            # Read V1 header: [tag_len, idx_len, cols_len, r, c]
            header = np.frombuffer(io_obj.read(40), dtype=np.int64)
            nbtag = header[0]
            nbidx = header[1]
            nbcols = header[2]
            r = header[3]
            c = header[4]
            
            # Read tag name
            tag_b = io_obj.read(int(nbtag))
            tag = tag_b.decode(encoding='UTF-8', errors='ignore')
            
            # Read index
            idx_b = io_obj.read(int(nbidx))
            idx = pd.to_datetime(np.frombuffer(idx_b, dtype=np.int64))
            
            # Read column names (NOT null-terminated in V1)
            colscsv_b = io_obj.read(int(nbcols))
            colscsv = colscsv_b.decode(encoding='UTF-8', errors='ignore')
            cols = colscsv.split(',')
            
            # Read data (C-ordered in V1)
            total_bytes = int(r * c * 8)
            data = np.frombuffer(io_obj.read(total_bytes), dtype=np.float64).reshape((r, c), order='C')
            
            # Create DataFrame (C-ordered)
            df = pd.DataFrame(data, index=idx, columns=cols)
            
            # Store in tags - TimeSeriesDisk will convert to V3 F-ordered format
            if self.type == 'DISK':
                if ishead:
                    self.tags[tag] = TimeSeriesDisk(self.shareddata, self, self.database,
                                                    self.period, self.source, tag=tag, 
                                                    value=df, user=self.user, overwrite=True)
                else:
                    if tag not in self.tags.keys():
                        self.tags[tag] = TimeSeriesDisk(self.shareddata, self, self.database,
                                                        self.period, self.source, tag=tag, 
                                                        value=df, user=self.user, overwrite=True)
                    else:
                        data = self.tags[tag].data
                        iidx = df.index.intersection(data.index)
                        icol = df.columns.intersection(data.columns)
                        data.loc[iidx, icol] = df.loc[iidx, icol].copy()
            else:
                raise Exception(f'Not implemented for {self.type} type')
            
            # Read next separator
            separator = np.frombuffer(io_obj.read(8), dtype=np.int64)[0]

    def compare_hash(self,h1,h2):
        """
        Compares two hash strings up to the length of the shorter one.
        
        Parameters:
            h1 (str): The first hash string.
            h2 (str): The second hash string.
        
        Returns:
            bool: True if the prefixes of both hashes up to the length of the shorter hash are equal, False otherwise.
        """
        l1 = len(h1)
        l2 = len(h2)
        l = min(l1,l2)
        return h1[:l]==h2[:l]

    # WRITE
    def flush(self):
        """
        Flushes the buffered data for all tags if the object's type is 'DISK'.
        
        Acquires a lock before iterating over each tag in the `tags` dictionary and
        calls the `flush` method on the `shf` attribute of each tag to ensure all
        buffered data is written out. Releases the lock afterward.
        
        If an exception occurs during flushing, logs an error message and raises an
        exception with the error details.
        """
        errmsg = ''
        try:
            self.acquire()
            for tag in self.tags:
                self.tags[tag].shf.flush()
        except Exception as e:
            errmsg = f'Could not flush timeseries container {self.shm_name}\n{e}!'
            Logger.log.error(errmsg)
        finally:
            self.release()
            if errmsg != '':
                raise Exception(errmsg)

    def write(self, startDate=None):
        """
        Writes data to a file or shared memory segment, optionally starting from a specified date.
        
        Parameters:
            startDate (pd.Timestamp or None): Optional start date to determine the writing range.
                If provided and earlier than the start of the current year, the header is written
                starting from this date; otherwise, writing begins from the start of the current year.
        
        Behavior:
            - Acquires a lock to ensure thread-safe operation.
            - Retrieves the file path and shared memory name.
            - Sets the modification time to the current timestamp.
            - Defines the partition date as January 1st of the current year.
            - Determines the first date to write from, defaulting to '1970-01-01' if no startDate is given.
            - Writes the header if the first date is before the partition date.
            - Writes the tail data.
            - Releases the lock.
            - Flushes the output to ensure all data is written.
            - Logs and raises an exception if any error occurs during writing.
        """
        errmsg = ''
        try:
            self.acquire()
            
            path, shm_name = self.get_path()
            mtime = datetime.now().timestamp()
            partdate = pd.Timestamp(datetime(datetime.now().year, 1, 1))
            firstdate = pd.Timestamp('1970-01-01')
            if not startDate is None:
                firstdate = startDate
            if firstdate < partdate:
                self.write_head(path, partdate, mtime, shm_name)
            self.write_tail(path, partdate, mtime, shm_name)            
            
        except Exception as e:
            errmsg = f'Could not write timeseries container {self.shm_name}\n{e}!'
            Logger.log.error(errmsg)
        finally:
            self.release()
            if errmsg != '':
                raise Exception(errmsg)
            
        self.flush()

    def write_head(self, path, partdate, mtime, shm_name):
        """
        Compresses and uploads a header file associated with a given path and partition date.
        
        This method creates a header IO object for the specified partition date, compresses its contents using gzip,
        and uploads the compressed data asynchronously to S3 in a separate thread. If the instance type is 'DISK',
        it also creates a placeholder header file on the local filesystem and sets its modification time.
        
        Args:
            path (str or Path): The base path for the header file.
            partdate (Any): The partition date used to create the header IO object.
            mtime (float): The modification time to set on the local header file if the instance type is 'DISK'.
            shm_name (str): Shared memory name (not used directly in this method).
        """
        io_obj = self.create_head_io(partdate)

        threads = []    
        io_obj.seek(0)
        gzip_io = io.BytesIO()
        with gzip.GzipFile(fileobj=gzip_io, mode='wb', compresslevel=1) as gz:
            # Copy using 1MB chunks to balance throughput and memory usage
            shutil.copyfileobj(io_obj, gz, length=1024*1024)
        threads = [*threads, Thread(target=S3Upload,
                                    args=(gzip_io, str(path)+'_head.bin.gzip', mtime))]
        
        with open(str(path)+'_head.bin', 'wb') as f:
            f.write(b'\x00')
        os.utime(str(path)+'_head.bin', (mtime, mtime))

        for i in range(len(threads)):
            threads[i].start()

        for i in range(len(threads)):
            threads[i].join()

    def create_head_io(self, partdate):
        """
        Create a binary I/O stream containing serialized data frames for each tag up to a specified date.
        
        Uses V3 bundle format for improved serialization speed and compatibility with local V3 format.
        
        V3 Bundle Format:
        - Bundle version marker (int64 = 3)
        - For each tag:
          - Tag separator (int64 = 1)  
          - Tag name length (int64)
          - Tag name (UTF-8)
          - Rows (int64)
          - Cols (int64)
          - Index data (int64 timestamps)
          - Column names (null-terminated CSV)
          - Data values (Fortran-ordered float64 for faster access)
        - Terminator (int64 = 0)
        - MD5 hash (16 bytes)
        
        Parameters:
            partdate (Timestamp): The cutoff date (exclusive) for selecting data from each tag's DataFrame.
        
        Returns:
            io.BytesIO: A BytesIO object containing the V3 bundle format data.
        """
        io_obj = io.BytesIO()
        
        # Write bundle format version
        bundle_version = np.array([3], dtype=np.int64)
        io_obj.write(bundle_version.tobytes())
        
        for tag in self.tags.keys():            
            dftag = self.tags[tag].data.loc[:partdate-BDay(1)]
            # create binary df
            df = dftag.dropna(how='all', axis=0).copy()
            r, c = df.shape
            
            if r == 0:  # Skip empty dataframes
                continue
            
            # Tag name
            tag_b = str.encode(tag, encoding='UTF-8', errors='ignore')
            nbtag = len(tag_b)
            
            # Index as int64 timestamps
            idx_b = df.index.astype(np.int64).values.tobytes()
            
            # Column names as null-terminated CSV (matching local V3 format)
            colscsv = ','.join(df.columns.values)
            colscsv_b = str.encode(colscsv, encoding='UTF-8', errors='ignore') + b'\x00'
            
            # Write tag separator
            io_obj.write(np.array([1], dtype=np.int64).tobytes())
            
            # Write header: tag_length, rows, cols
            header = np.array([nbtag, r, c], dtype=np.int64)
            io_obj.write(header.tobytes())
            
            # Write tag name
            io_obj.write(tag_b)
            
            # Write index
            io_obj.write(idx_b)
            
            # Write column names
            io_obj.write(colscsv_b)
            
            # Write data as Fortran-ordered (column-major) for consistency with local format
            # This also compresses better for timeseries data
            data_f = np.asfortranarray(df.values.astype(np.float64))
            io_obj.write(data_f.tobytes())

        # Write terminator
        io_obj.write(np.array([0], dtype=np.int64).tobytes())
        
        # Write MD5 hash without copying the buffer
        m = hashlib.md5(io_obj.getbuffer()).digest()
        io_obj.write(m)

        return io_obj

    def write_tail(self, path, partdate, mtime, shm_name):
        """
        Compresses the tail data of a partition, uploads it to S3, and optionally writes a placeholder tail file on disk.
        
        Parameters:
            path (str or Path): The base file path for the tail files.
            partdate (datetime or similar): The partition date used to create the tail IO object.
            mtime (float): The modification time to set on the local tail file.
            shm_name (str): Shared memory name (not used directly in this method).
        
        Behavior:
        - Creates a tail IO object for the given partition date.
        - Compresses the tail data using gzip with compression level 1.
        - Starts a thread to upload the compressed tail data to S3 with a filename suffix '_tail.bin.gzip'.
        - Writes a single null byte to a local tail file and sets its modification time.
        - Waits for all upload threads to complete before returning.
        """
        io_obj = self.create_tail_io(partdate)

        threads = []        
        io_obj.seek(0)
        gzip_io = io.BytesIO()
        with gzip.GzipFile(fileobj=gzip_io, mode='wb', compresslevel=1) as gz:
            shutil.copyfileobj(io_obj, gz, length=1024*1024)
        threads = [*threads, Thread(target=S3Upload,
                                    args=(gzip_io, str(path)+'_tail.bin.gzip', mtime))]
                
        with open(str(path)+'_tail.bin', 'wb') as f:
            f.write(b'\x00')
        os.utime(str(path)+'_tail.bin', (mtime, mtime))

        for i in range(len(threads)):
            threads[i].start()

        for i in range(len(threads)):
            threads[i].join()

    def create_tail_io(self, partdate):
        """
        Create a binary in-memory stream containing serialized data frames from the object's tags starting from a specified date.
        
        Uses V3 bundle format for improved serialization speed and compatibility with local V3 format.
        
        V3 Bundle Format:
        - Bundle version marker (int64 = 3)
        - For each tag:
          - Tag separator (int64 = 1)  
          - Tag name length (int64)
          - Tag name (UTF-8)
          - Rows (int64)
          - Cols (int64)
          - Index data (int64 timestamps)
          - Column names (null-terminated CSV)
          - Data values (Fortran-ordered float64)
        - Terminator (int64 = 0)
        - MD5 hash (16 bytes)
        
        Parameters:
            partdate (Timestamp or compatible): The starting date from which to include data in the serialization.
        
        Returns:
            io.BytesIO: An in-memory binary stream containing the V3 bundle format data and checksum.
        """
        io_obj = io.BytesIO()
        
        # Write bundle format version
        bundle_version = np.array([3], dtype=np.int64)
        io_obj.write(bundle_version.tobytes())
        
        for tag in self.tags.keys():            
            self.tags[tag].shf.flush()
            dftag = self.tags[tag].data.loc[partdate:]
            # create binary df
            df = dftag.dropna(how='all', axis=0)
            r, c = df.shape
            
            if r == 0:  # Skip empty dataframes
                continue
            
            # Tag name
            tag_b = str.encode(tag, encoding='UTF-8', errors='ignore')
            nbtag = len(tag_b)
            
            # Index as int64 timestamps
            idx_b = df.index.astype(np.int64).values.tobytes()
            
            # Column names as null-terminated CSV (matching local V3 format)
            colscsv = ','.join(df.columns.values)
            colscsv_b = str.encode(colscsv, encoding='UTF-8', errors='ignore') + b'\x00'
            
            # Write tag separator
            io_obj.write(np.array([1], dtype=np.int64).tobytes())
            
            # Write header: tag_length, rows, cols
            header = np.array([nbtag, r, c], dtype=np.int64)
            io_obj.write(header.tobytes())
            
            # Write tag name
            io_obj.write(tag_b)
            
            # Write index
            io_obj.write(idx_b)
            
            # Write column names
            io_obj.write(colscsv_b)
            
            # Write data as Fortran-ordered (column-major) for consistency with local format
            data_f = np.asfortranarray(df.values.astype(np.float64))
            io_obj.write(data_f.tobytes())

        # Write terminator
        io_obj.write(np.array([0], dtype=np.int64).tobytes())
        
        # Write MD5 hash without copying the buffer
        m = hashlib.md5(io_obj.getbuffer()).digest()
        io_obj.write(m)
        
        return io_obj

    @staticmethod
    def write_file(io_obj, path, mtime, shm_name):
        """
        Writes the contents of a BytesIO-like object to a specified file path, optionally displaying a progress bar for large files, and sets the file's modification time.
        
        Parameters:
            io_obj (io.BytesIO): An in-memory bytes buffer containing the data to write.
            path (str): The file system path where the data should be written.
            mtime (float): The modification time to set on the written file (as a Unix timestamp).
            shm_name (str): A name used in the progress bar description when writing large files.
        
        Behavior:
            - If the size of the data exceeds 100 MB, writes the file in 100 MB chunks while displaying a tqdm progress bar.
            - Otherwise, writes the entire buffer at once.
            - After writing, flushes the file and updates its modification time to `mtime`.
        """
        with open(path, 'wb') as f:
            nb = len(io_obj.getbuffer())
            size_mb = nb / (1024*1024)
            if size_mb > 100:
                blocksize = 1024*1024*100
                descr = 'Writing:%iMB %s' % (size_mb, shm_name)
                with tqdm(total=nb, unit='B', unit_scale=True, desc=descr) as pbar:
                    written = 0
                    while written < nb:
                        # write in chunks of max 100 MB size
                        chunk_size = min(blocksize, nb-written)
                        f.write(io_obj.getbuffer()[written:written+chunk_size])
                        written += chunk_size
                        pbar.update(chunk_size)
            else:
                f.write(io_obj.getbuffer())
            f.flush()
        os.utime(path, (mtime, mtime))

    ############### LOCK ###############
    def acquire(self):
        """
        Acquire a lock on the shared data resource to ensure synchronized access.
        
        This method uses the specified mutex, process ID, and shared memory name to obtain a lock by delegating
        the operation to the `acquire` method of the `shareddata` object.
        
        Parameters:
            None
        
        Returns:
            None
        """
        self.shareddata.acquire(self.mutex, self.pid, self.shm_name)

    def release(self):
        """
        Releases the lock or resource associated with the current process and shared memory name.
        
        This method calls the `release` function of the `shareddata` object, passing
        the current mutex, process ID (`pid`), and shared memory name (`shm_name`) to
        properly release the held resource.
        
        No return value.
        """
        self.shareddata.release(self.mutex, self.pid, self.shm_name)

    def free(self):
        """
        Releases resources associated with the object's tags and removes its timeseries data from shared storage.
        
        This method:
        1. Calls the `free()` method on each tag object contained in the `tags` dictionary to release their resources.
        2. Constructs a unique path string using the object's `user`, `database`, `period`, and `source` attributes.
        3. Removes the timeseries data corresponding to this path from the `shareddata.data` dictionary if it exists.
        
        This cleanup helps prevent memory leaks and ensures that shared timeseries data is properly discarded when no longer needed.
        """
        _tags = list(self.tags.keys())
        for tag in _tags:
            self.tags[tag].free()
        path = f'{self.user}/{self.database}/{self.period}/{self.source}/timeseries'
        if path in self.shareddata.data.keys():
            del self.shareddata.data[path]
        
    # GETTER AND SETTER
    def __getitem__(self, key):
        """
        Retrieve the data associated with the given tag key.
        
        Parameters:
            key (str): The tag key to look up.
        
        Returns:
            The data corresponding to the specified tag key.
        
        Raises:
            Exception: If the tag key is not found in the tags dictionary, with a message indicating the missing tag and its context (database, period, source).
        """
        try:
            self.acquire()
            if key in self.tags.keys():
                return self.tags[key].data
            else:
                raise Exception('Tag %s not found in %s/%s/%s' %
                        (key, self.database, self.period, self.source))
        finally:
            self.release()
        
    def __setitem__(self, key, value):
        """
        Sets the value of an existing tag identified by `key`.
        
        If the `key` exists in the `tags` dictionary, its value is updated to `value`.
        If the `key` does not exist, raises an Exception indicating the tag was not found,
        including the database, period, and source context in the error message.
        
        Parameters:
            key: The tag key to be updated.
            value: The new value to assign to the tag.
        
        Raises:
            Exception: If the tag `key` is not found in the current tags.
        """
        try:
            self.acquire()
            if key in self.tags.keys():
                self.tags[key] = value
            else:
                raise Exception('Tag %s not found in %s/%s/%s' %
                        (key, self.database, self.period, self.source))
        finally:
            self.release()

    def __del__(self):
        """
        Destructor to safely release the mutex held by the object upon its destruction.
        
        Ensures that if the current process holds the mutex associated with this instance,
        it is properly released to avoid deadlocks or resource contention when the object
        is garbage collected or the program exits. Any exceptions during cleanup are caught
        and ignored to prevent errors during object finalization.
        """
        try:
            # Check if mutex is held by this process and release it
            if hasattr(self, 'mutex') and hasattr(self, 'pid') and hasattr(self, 'shm_name'):
                # Only try to release if this process holds the mutex
                if self.mutex is not None and 'pid' in self.mutex:
                    current_holder = self.mutex.get('pid', 0)
                    if current_holder == self.pid:
                        self.release()
        except Exception:
            # Ignore errors during cleanup - object is being destroyed anyway
            pass