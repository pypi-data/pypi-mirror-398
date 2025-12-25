# TimeSeriesDisk.py
# This file is part of the SharedData package.
# It manages time series data stored on disk using memory-mapped files for efficient access and modification

# THIRD PARTY LIBS
import os
import pandas as pd
import numpy as np
import time
from numba import jit
from pathlib import Path

from SharedData.Logger import Logger


class TimeSeriesDisk:

    """
    Manages time series data stored on disk using memory-mapped files for efficient access and modification.
    
    This class provides functionality to create, map, and manipulate large time series datasets stored as binary files on disk. It supports initializing from existing data, creating new datasets, and updating values with fast memory mapping techniques. The data is organized by user, database, period, source, and tag, and indexed by timestamps with associated columns representing different symbols or variables.
    
    Key features:
    - Initializes time series data from disk or creates new storage if not present or if overwrite is requested.
    - Uses numpy memmap for memory-efficient file access and pandas DataFrame for convenient data manipulation.
    - Supports fast lookup of symbol and timestamp indices with JIT-compiled helper functions.
    - Handles file path creation and directory management based on environment and input parameters.
    - Provides methods to allocate and map shared memory segments for inter-process data sharing.
    - Ensures data consistency by verifying columns and index alignment when loading existing data.
    - Includes error handling and logging for robust operation.
    
    Parameters:
    - shareddata: Shared memory manager object for allocating and managing shared memory segments.
    - container: Container object providing period duration, start date, and time indexing utilities.
    - database: String identifier for the database name.
    - period: String
    """
    def __init__(self, shareddata, container, database, period, source, tag,
             value=None, columns=None, user='master',overwrite=False):

        """
        '''
        Initialize an instance managing shared memory data storage and retrieval.
        
        Parameters:
            shareddata: Shared data object used for synchronization or shared state.
            container: Container object providing metadata such as periodseconds, startDate, and indexing methods.
            database: Identifier or connection for the database associated with the data.
            period: Time period for the data.
            source: Source identifier for the data.
            tag: String tag identifying the dataset; leading slashes are removed if present.
            value (optional): DataFrame containing initial data values to populate the shared memory.
            columns (optional): Columns to be used for the data; if None and value is provided, columns are inferred from value.
            user (optional): User identifier, default is 'master'.
            overwrite (optional): Boolean flag indicating whether to overwrite existing data; default is False.
        
        Behavior:
        - Sets up internal attributes including period, source, tag, and indexing based on the container.
        - Determines columns and symbol indices from provided columns or value.
        - Attempts to locate existing shared memory file; if found and not overwriting, maps it into memory.
        - Validates that existing data columns and index match expected columns and index; if not, copies and recreates shared memory.
        - If no existing data or overwrite
        """
        self.shareddata = shareddata
        self.container = container
        self.user = user
        self.database = database
        self.period = period
        self.source = source
        self.tag = tag[1:] if tag[0]=="\\" or tag[0]=="/" else tag
        
        # Initialize mutex for multi-process safety
        self.shm_name = f'{self.user}/{self.database}/{self.period}/{self.source}/timeseries/{self.tag}'
        self.relpath = str(self.shm_name)
        if os.name == 'posix':
            self.shm_name = self.shm_name.replace('/', '\\')
        
        self.pid = os.getpid()
        [self.shm_mutex, self.mutex, self.ismalloc] = \
            self.shareddata.mutex(self.shm_name, self.pid)
        
        self.periodseconds = container.periodseconds
        
        # If value DataFrame is provided, use its first date as startDate
        if not value is None and len(value) > 0:
            self.startDate = value.sort_index().index[0]
        else:
            self.startDate = self.container.startDate
        
        self.index = self.container.getTimeIndex(self.startDate)
        self.ctimeidx = self.container.getContinousTimeIndex(self.startDate)
        
        self.columns = None
        if not columns is None:
            self.columns = columns
            self.symbolidx = {}
            for i in range(len(self.columns)):
                self.symbolidx[self.columns.values[i]] = i
        elif not value is None:
            self.columns = value.columns
            self.symbolidx = {}
            for i in range(len(self.columns)):
                self.symbolidx[self.columns.values[i]] = i

        self.path, self.shm_name = self.get_path()
        self.exists = os.path.isfile(self.path)                        
                    
        self.data = None
                        
        self.init_time = time.time()
        try:            
            copy = False
            if (self.exists) & (not overwrite):
                _data = self.malloc_map()
                
                # Handle column mismatch - check if new columns need to be added
                if not self.columns is None:
                    existing_cols = set(_data.columns.tolist())
                    requested_cols = set(self.columns.tolist())
                    
                    # Check if we need to append new columns
                    new_cols = requested_cols - existing_cols
                    if new_cols:
                        Logger.log.info(f'Appending new columns: {new_cols}')
                        self.append_columns(list(new_cols))
                        _data = self.data  # Use the updated data
                    elif not _data.columns.equals(self.columns):
                        copy = True

                if not self.index.equals(_data.index):
                    copy = True

                if not copy:
                    self.data = _data
                    if self.columns is None:
                        self.columns = self.data.columns
                        self.symbolidx = {}
                        for i in range(len(self.columns)):
                            self.symbolidx[self.columns.values[i]] = i
                else:
                    _data = _data.copy(deep=True)                    
                    del self.shf
                    self.columns = _data.columns
                    self.symbolidx = {}
                    for i in range(len(self.columns)):
                        self.symbolidx[self.columns.values[i]] = i
                    self.malloc_create()
                    sidx = np.array([self.get_loc_symbol(s)
                                for s in self.columns])
                    ts = _data.index.values.astype(np.int64)/10**9  # seconds
                    tidx = self.get_loc_timestamp(ts)
                    self.setValuesJit(self.data.values, tidx,
                                        sidx, _data.values)
                    del _data
                                
            elif (not self.exists) | (overwrite):
                # create new empty file
                self.malloc_create()

            if (not value is None):
                # Handle case where value contains columns not in self.columns
                value_cols = set(value.columns.tolist())
                data_cols = set(self.data.columns.tolist())
                missing_cols = value_cols - data_cols
                
                if missing_cols:
                    Logger.log.info(f'Appending missing columns from value: {missing_cols}')
                    self.append_columns(list(missing_cols))
                
                sidx = np.array([self.get_loc_symbol(s)
                                for s in value.columns])
                ts = value.index.values.astype(np.int64)/10**9  # seconds
                tidx = self.get_loc_timestamp(ts)
                
                # Handle multi-dimensional value array
                if len(value.values.shape) == 1:
                    # Single column case
                    self.setValuesSymbolJit(self.data.values, tidx, sidx[0], value.values)
                else:
                    # Multiple columns
                    self.setValuesJit(self.data.values, tidx, sidx, value.values)
                self.shf.flush()
                        
        except Exception as e:            
            errmsg = 'Error initalizing %s!\n%s' % (self.shm_name, str(e))
            Logger.log.error(errmsg)
            # Release mutex before raising exception
            try:
                self.release()
            except:
                pass
            raise Exception(errmsg)
        finally:
            # Always release the mutex after initialization
            # (it was acquired by SharedData.mutex() call)
            try:
                self.release()
            except:
                pass

        self.init_time = time.time() - self.init_time
        
        # Track file metadata for auto-reload detection
        self._last_file_size = None
        self._last_mtime = None
        self._last_column_count = None
        self._update_file_metadata()
    
    def _update_file_metadata(self):
        """Update cached file metadata for change detection"""
        try:
            if os.path.exists(self.path):
                stat = os.stat(self.path)
                self._last_file_size = stat.st_size
                self._last_mtime = stat.st_mtime
                self._last_column_count = len(self.columns) if self.columns is not None else 0
        except:
            pass

    def get_path(self):
        """
        Constructs and returns the file system path and shared memory name for a timeseries data file.
        
        The method builds a hierarchical path based on the instance attributes: user, database, period, source, and tag.
        It ensures the directory structure exists under the base directory specified by the 'DATABASE_FOLDER' environment variable.
        The returned path points to a binary file named after the tag with a '.bin' extension.
        The shared memory name is a string composed of the same attributes separated by slashes, with path separators adjusted for POSIX systems.
        
        Returns:
            tuple: A tuple containing:
                - path (Path): The full Path object to the binary timeseries file.
                - shm_name (str): The shared memory name string with appropriate path separators.
        """
        shm_name = self.user + '/' + self.database + '/' \
            + self.period + '/' + self.source + '/timeseries/' + self.tag
        if os.name == 'posix':
            shm_name = shm_name.replace('/', '\\')

        path = Path(os.environ['DATABASE_FOLDER'])
        path = path / self.user
        path = path / self.database
        path = path / self.period
        path = path / self.source
        path = path / 'timeseries'
        path = path / (self.tag+'.bin')
        path = Path(str(path).replace('\\', '/'))
        os.makedirs(path.parent, exist_ok=True)
        
        return path, shm_name

    def malloc_create(self):
        """
        Creates memory-mapped files with separate metadata and data files for true zero-copy column appending.
        
        File structure (Version 3 - Separated metadata):
        - Metadata file (.meta): version, rows, columns, index, column names
        - Data file (.bin): Fortran-ordered float64 array only
        
        This design enables true zero-copy column appending: just extend the data file and update metadata.
        
        Returns:
            bool: True if the files were successfully created and initialized.
        
        Raises:
            Exception: If any error occurs during file creation.
        """
        filepath = self.path
        metapath = str(filepath).replace('.bin', '.meta')
                            
        try:
            r = len(self.index)
            c = len(self.columns)
            
            # Version 3 indicates separated metadata format
            version = 3
            
            # === Metadata File ===
            # Header: version, num_rows, num_columns
            header_b = np.array([version, r, c], dtype=np.int64).tobytes()
            
            # Index data
            idx_b = self.index.astype(np.int64).values.tobytes()
            
            # Column names as null-terminated CSV
            colscsv_b = str.encode(','.join(self.columns), encoding='UTF-8', errors='ignore') + b'\x00'
            
            # Write metadata file
            with open(metapath, 'wb') as f:
                f.write(header_b)  # 24 bytes
                f.write(idx_b)     # r * 8 bytes
                f.write(colscsv_b) # variable length
            
            # === Data File ===
            # Pure Fortran-ordered data (no header)
            nb_data = int(r * c * 8)
            
            if not Path(filepath).is_file():
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'wb') as f:
                    f.seek(nb_data - 1)
                    f.write(b'\x00')
                    if os.name == 'posix':
                        os.posix_fallocate(f.fileno(), 0, nb_data)
            elif Path(filepath).stat().st_size < nb_data:
                with open(filepath, 'ab') as f:
                    f.seek(nb_data - 1)
                    f.write(b'\x00')
                    if os.name == 'posix':
                        os.posix_fallocate(f.fileno(), 0, nb_data)
            
            # Memory-map the data file (offset=0 since no header in data file)
            self.shf = np.memmap(filepath, dtype='<f8', mode='r+', 
                                offset=0, shape=(r, c), order='F')
            self.shf[:] = np.nan
            self.shf.flush()
            
            # Create DataFrame with zero-copy view
            self.data = pd.DataFrame(self.shf, 
                                     index=self.index,
                                     columns=self.columns,
                                     copy=False)
            self.data.index.name = 'date'
            
            return True
        except Exception as e:
            Logger.log.error('Failed to malloc_create\n%s' % str(e))
            raise Exception('Failed to malloc_create\n%s' % str(e))            

    def malloc_map(self):        
        """
        Maps an existing memory-mapped timeseries file with backward compatibility.
        
        Supports two file format versions:
        - Version 1 (Legacy): Single file, C-ordered, 40-byte header - auto-migrates to V3
        - Version 3 (Current): Separate .meta and .bin files for zero-copy column appending
        
        Auto-migrates V1 to V3 on first load.
        
        Returns:
            pd.DataFrame: DataFrame containing the memory-mapped data.
        """
        filepath = self.path
        metapath = str(filepath).replace('.bin', '.meta')
        
        if not Path(filepath).is_file():
            return None
        
        # Check if we have V3 format (separate metadata file)
        if Path(metapath).is_file():
            _data = self._map_version3(filepath, metapath)
        else:
            # V1: Migrate to V3
            Logger.log.info(f"Migrating V1 timeseries to V3: {filepath}")
            _data = self._migrate_v1_to_v3(filepath, metapath)
        
        # Update startDate, index, and ctimeidx to match the loaded data
        if len(self.index) > 0:
            self.startDate = self.index[0]
            self.ctimeidx = self.container.getContinousTimeIndex(self.startDate)
            
        return _data
    
    def _map_version3(self, filepath, metapath):
        """Map Version 3 format (separate metadata and data files)."""
        with open(metapath, 'rb') as f:
            # Read header
            header_b = f.read(24)
            version, r, c = np.frombuffer(header_b, dtype=np.int64)
            
            # Read index
            idx_b = f.read(r * 8)
            _index = pd.to_datetime(np.frombuffer(idx_b, dtype=np.int64))
            
            # Read column names
            cols_bytes = bytearray()
            while True:
                byte = f.read(1)
                if byte == b'\x00' or not byte:
                    break
                cols_bytes.extend(byte)
            
            _columns = cols_bytes.decode('UTF-8', errors='ignore').split(',')
            _columns = pd.Index(_columns)
        
        # Update internal state
        self.index = _index
        self.columns = _columns
        self.symbolidx = {}
        for i in range(len(self.columns)):
            self.symbolidx[self.columns.values[i]] = i
        
        # Map data file (no header - pure data)
        self.shf = np.memmap(filepath, dtype='<f8', mode='r+',
                            offset=0, shape=(r, c), order='F')
        
        # Create zero-copy DataFrame
        _data = pd.DataFrame(self.shf,
                            index=self.index,
                            columns=self.columns,
                            copy=False)
        _data.index.name = 'date'
        
        return _data
    
    def _migrate_v1_to_v3(self, filepath, metapath):
        """Migrate Version 1 (C-ordered) to Version 3 (Fortran, separate files)."""
        with open(filepath, 'rb') as f:
            # Read V1 header (40 bytes)
            nb_header = 40
            header = np.frombuffer(f.read(nb_header), dtype=np.int64)
            r = header[0]
            c = header[1]
            nb_cols = header[2]
            nb_idx = header[3]
            nb_data = header[4]
            
            cols_b = f.read(nb_cols)
            _columns = cols_b.decode('UTF-8', errors='ignore').split(',')
            
            idx_b = f.read(nb_idx)
            
            nb_offset = nb_header + nb_cols + nb_idx
            
            # Read C-ordered data (exact size from header)
            f.seek(nb_offset)
            data_c = np.frombuffer(f.read(nb_data), dtype='<f8').reshape((r, c), order='C')
        
        # Write V3 metadata file
        header_v3 = np.array([3, r, c], dtype=np.int64).tobytes()
        colscsv_v3 = cols_b + b'\x00'
        
        with open(metapath, 'wb') as f:
            f.write(header_v3)
            f.write(idx_b)
            f.write(colscsv_v3)
        
        # Write V3 data file
        # Key: We need to physically rearrange the data from row-major to column-major
        # Create Fortran array and write column by column
        temp_filepath = str(filepath) + '.tmp'
        data_f = np.asfortranarray(data_c)
        
        # Create memmap and copy data - this ensures proper Fortran layout on disk
        temp_memmap = np.memmap(temp_filepath, dtype='<f8', mode='w+',
                                shape=(r, c), order='F')
        temp_memmap[:] = data_c  # Copy values (numpy handles the reordering)
        temp_memmap.flush()
        del temp_memmap
        
        # Replace old file with new
        os.replace(temp_filepath, filepath)
        
        # Now map the V3 files
        return self._map_version3(filepath, metapath)

    # get / set
    def get_loc_symbol(self, symbol):
        """
        Retrieve the location index associated with the given symbol.
        
        Parameters:
            symbol (hashable): The symbol to look up in the symbol index.
        
        Returns:
            int or float: The location index corresponding to the symbol if found;
                          otherwise, returns numpy.nan.
        """
        if symbol in self.symbolidx.keys():
            return self.symbolidx[symbol]
        else:
            return np.nan

    def get_loc_timestamp(self, ts):
        """
        Convert a timestamp or array of timestamps to location indices relative to the object's start date and period.
        
        Parameters:
            ts (scalar or array-like): Timestamp(s) in seconds to be converted.
        
        Returns:
            int, numpy.ndarray, or float: Location index or array of indices corresponding to the input timestamp(s). Returns np.nan if the timestamp is out of range.
        """
        istartdate = self.startDate.timestamp()  # seconds
        if not np.isscalar(ts):
            tidx = self.get_loc_timestamp_Jit(ts, istartdate,
                                              self.periodseconds, self.ctimeidx)
            return tidx
        else:
            tids = np.int64(ts)  # seconds
            tids = np.int64(tids - istartdate)
            tids = np.int64(tids/self.periodseconds)
            if tids < self.ctimeidx.shape[0]:
                tidx = self.ctimeidx[tids]
                return tidx
            else:
                return np.nan

    @staticmethod
    @jit(nopython=True, nogil=True, cache=True)
    def get_loc_timestamp_Jit(ts, istartdate, periodseconds, ctimeidx):
        """
        Convert an array of timestamps into localized timestamps based on a start date and period, using a precomputed index array.
        
        Parameters:
            ts (np.ndarray): Array of timestamps to be converted.
            istartdate (int): The start date timestamp used as a reference point.
            periodseconds (int): The length of each period in seconds.
            ctimeidx (np.ndarray): Array of precomputed localized timestamps indexed by period.
        
        Returns:
            np.ndarray: Array of localized timestamps corresponding to input timestamps. If a timestamp falls outside the range of ctimeidx, the result is NaN.
        
        Notes:
            This function is optimized with Numba JIT compilation for performance, running without Python's GIL and caching the compiled function.
        """
        tidx = np.empty(ts.shape, dtype=np.float64)
        len_ctimeidx = len(ctimeidx)
        for i in range(len(tidx)):
            tid = np.int64(ts[i])
            tid = np.int64(tid-istartdate)
            tid = np.int64(tid/periodseconds)
            if tid < len_ctimeidx:
                tidx[i] = ctimeidx[tid]
            else:
                tidx[i] = np.nan
        return tidx

    @staticmethod
    @jit(nopython=True, nogil=True, cache=True)
    def setValuesSymbolJit(values, tidx, sidx, arr):
        """
        Set values in a 2D numpy array at specified indices with JIT compilation for enhanced performance.
        
        Parameters:
            values (np.ndarray): A 2D numpy array to be updated.
            tidx (array-like): Iterable of indices for the first dimension of `values`.
            sidx (float or int): Index for the second dimension of `values`. If NaN, no updates are performed.
            arr (array-like): Values to assign at the specified indices.
        
        Notes:
            - Updates occur only where elements in `tidx` are not NaN.
            - Indices are converted to int64 before assignment.
            - Decorated with Numba's JIT to optimize execution by eliminating Python overhead and releasing the GIL.
        """
        if not np.isnan(sidx):
            s = np.int64(sidx)
            i = 0
            for t in tidx:
                if not np.isnan(t):
                    values[np.int64(t), s] = arr[i]
                i = i+1

    @staticmethod
    @jit(nopython=True, nogil=True, cache=True)
    def setValuesJit(values, tidx, sidx, arr):
        """
        Set values in a 2D array at specified indices using JIT compilation for performance.
        
        Parameters:
        values : numpy.ndarray
            The 2D array in which values will be set.
        tidx : array-like
            Array of row indices where values should be assigned. NaN entries are ignored.
        sidx : array-like
            Array of column indices where values should be assigned. NaN entries are ignored.
        arr : numpy.ndarray
            2D array of values to assign to `values` at positions defined by `tidx` and `sidx`.
        
        Notes:
        - Indices in `tidx` and `sidx` are converted to int64 before assignment.
        - Entries in `tidx` or `sidx` that are NaN are skipped.
        - This function is optimized with Numba's JIT for speed and releases the GIL.
        """
        i = 0
        for t in tidx:
            if not np.isnan(t):
                j = 0
                for s in sidx:
                    if not np.isnan(s):
                        values[np.int64(t), np.int64(s)] = arr[i, j]
                    j = j+1
            i = i+1

    def delete_columns(self, columns_to_delete):
        """
        Delete specified columns from the Fortran-ordered timeseries file.
        
        This method handles column deletion by:
        1. Acquires mutex lock for exclusive access
        2. Creates a new data file with only the remaining columns
        3. Copies data column-by-column (efficient in Fortran order)
        4. Updates the metadata file (.meta) with new column names and count
        5. Replaces old files with new ones
        6. Remaps the updated data file
        7. Releases mutex lock
        
        Unlike append_columns, deletion requires data reorganization since we must
        remove columns from the middle of the Fortran-ordered array.
        
        Parameters:
            columns_to_delete (list or pd.Index): Names of columns to delete
        
        Returns:
            pd.DataFrame: Updated DataFrame without deleted columns
        
        Raises:
            Exception: If columns don't exist or file operations fail
            
        Note:
            Requires Version 3 file format (separate .meta and .bin files).
        """
        filepath = self.path
        metapath = str(filepath).replace('.bin', '.meta')
        
        # Convert to list if needed
        if isinstance(columns_to_delete, pd.Index):
            columns_to_delete = columns_to_delete.tolist()
        elif not isinstance(columns_to_delete, list):
            columns_to_delete = [columns_to_delete]
        
        # OPTIMIZATION: Use set for O(1) lookups instead of O(n)
        columns_to_delete_set = set(columns_to_delete)
        
        # Check that columns exist
        existing_cols = set(self.columns.tolist())
        missing = [col for col in columns_to_delete if col not in existing_cols]
        if missing:
            raise ValueError(f"Columns do not exist: {missing}")
        
        # Don't allow deleting all columns
        if len(columns_to_delete) >= len(self.columns):
            raise ValueError("Cannot delete all columns")
        
        try:
            # Acquire mutex lock for file structure modification
            self.acquire()
            
            # Flush current data
            if hasattr(self, 'shf'):
                self.shf.flush()
                del self.shf
            if hasattr(self, 'data'):
                del self.data
            
            # Read current metadata (OPTIMIZED: single read + seek instead of byte-by-byte)
            with open(metapath, 'rb') as f:
                # Read header
                header = np.frombuffer(f.read(24), dtype=np.int64)
                version = header[0]
                r = header[1]
                c_old = header[2]
                
                if version != 3:
                    raise ValueError("delete_columns requires version 3 format (separate .meta/.bin files)")
                
                # Read index
                idx_b = f.read(r * 8)
                
                # OPTIMIZATION: Read remaining file content in one shot instead of byte-by-byte
                remaining_bytes = f.read()
                # Find null terminator
                null_pos = remaining_bytes.find(b'\x00')
                if null_pos != -1:
                    cols_bytes = remaining_bytes[:null_pos]
                else:
                    cols_bytes = remaining_bytes
                
                old_cols_str = cols_bytes.decode('UTF-8', errors='ignore')
            
            # OPTIMIZATION: Calculate new columns using set lookup (O(1) instead of O(n))
            old_cols_list = old_cols_str.split(',')
            new_cols_list = [col for col in old_cols_list if col not in columns_to_delete_set]
            c_new = len(new_cols_list)
            
            # OPTIMIZATION: Pre-calculate column indices to copy for potential batch operations
            cols_to_copy = []
            for i, col in enumerate(old_cols_list):
                if col not in columns_to_delete_set:
                    cols_to_copy.append(i)
            
            # Map old data file (read-only for better OS caching)
            old_shf = np.memmap(filepath, dtype='<f8', mode='r',
                               offset=0, shape=(r, c_old), order='F')
            
            # Create temporary new data file
            temp_filepath = str(filepath) + '.tmp'
            nb_new_data = r * c_new * 8
            
            with open(temp_filepath, 'wb') as f:
                f.seek(nb_new_data - 1)
                f.write(b'\x00')
                if os.name == 'posix':
                    os.posix_fallocate(f.fileno(), 0, nb_new_data)
            
            # Map new data file
            new_shf = np.memmap(temp_filepath, dtype='<f8', mode='r+',
                               offset=0, shape=(r, c_new), order='F')
            
            # OPTIMIZATION: Copy columns using vectorized indexing (much faster for large datasets)
            # Direct array assignment is more efficient than loop
            new_shf[:, :] = old_shf[:, cols_to_copy]
            
            new_shf.flush()
            del new_shf
            del old_shf
            
            # Prepare new metadata
            new_cols_str = ','.join(new_cols_list)
            new_cols_b = str.encode(new_cols_str, encoding='UTF-8', errors='ignore') + b'\x00'
            new_header_b = np.array([3, r, c_new], dtype=np.int64).tobytes()
            
            # Write new metadata file
            temp_metapath = metapath + '.tmp'
            with open(temp_metapath, 'wb') as f:
                f.write(new_header_b)
                f.write(idx_b)
                f.write(new_cols_b)
            
            # Replace old files with new ones (atomic operation)
            os.replace(temp_filepath, filepath)
            os.replace(temp_metapath, metapath)
            
            # Update instance attributes
            self.columns = pd.Index(new_cols_list)
            self.symbolidx = {col: i for i, col in enumerate(self.columns)}
            
            # Remap the data file with new structure
            self.shf = np.memmap(filepath, dtype='<f8', mode='r+',
                                offset=0, shape=(r, c_new), order='F')
            
            self.data = pd.DataFrame(self.shf,
                                    index=self.index,
                                    columns=self.columns,
                                    copy=False)
            self.data.index.name = 'date'
            
            Logger.log.info(f'Deleted {len(columns_to_delete)} columns from {filepath}')
            
            return self.data
            
        except Exception as e:
            Logger.log.error(f'Failed to delete columns: {str(e)}')
            raise Exception(f'Failed to delete columns: {str(e)}')
        finally:
            # Always release mutex lock
            self.release()

    def append_columns(self, new_columns):
        """
        Efficiently append new columns to the Fortran-ordered timeseries file with TRUE zero-copy semantics.
        
        This method leverages the separated metadata/data file architecture (Version 3):
        1. Acquires mutex lock for exclusive access
        2. Extends the data file (.bin) with new column data (NaN-filled)
        3. Updates the metadata file (.meta) with new column names and count
        4. Remaps the expanded data file - NO DATA COPYING!
        5. Releases mutex lock
        
        The key insight: In Fortran (column-major) order, columns are stored contiguously,
        so adding a column = appending to the end of the file. No need to rewrite existing data!
        
        Parameters:
            new_columns (list or pd.Index): Names of columns to append
        
        Returns:
            pd.DataFrame: Updated DataFrame with new columns
        
        Raises:
            Exception: If columns already exist or file operations fail
            
        Note:
            Requires Version 3 file format (separate .meta and .bin files).
            This is a true zero-copy operation - existing data is never read or rewritten!
        """
        filepath = self.path
        metapath = str(filepath).replace('.bin', '.meta')
        
        # Convert to list if needed
        if isinstance(new_columns, pd.Index):
            new_columns = new_columns.tolist()
        elif not isinstance(new_columns, list):
            new_columns = [new_columns]
        
        # Check for duplicate columns
        existing_cols = set(self.columns.tolist())
        duplicates = [col for col in new_columns if col in existing_cols]
        if duplicates:
            raise ValueError(f"Columns already exist: {duplicates}")
        
        try:
            # Acquire mutex lock for file structure modification
            self.acquire()
            
            # Flush current data
            if hasattr(self, 'shf'):
                self.shf.flush()
                del self.shf
            if hasattr(self, 'data'):
                del self.data
            
            # Read current metadata
            with open(metapath, 'rb') as f:
                # Read header
                header = np.frombuffer(f.read(24), dtype=np.int64)
                version = header[0]
                r = header[1]
                c_old = header[2]
                
                if version != 3:
                    raise ValueError("Zero-copy append_columns requires version 3 format (separate .meta/.bin files)")
                
                # Read index
                idx_b = f.read(r * 8)
                
                # Read old column names
                cols_bytes = bytearray()
                while True:
                    byte = f.read(1)
                    if byte == b'\x00' or not byte:
                        break
                    cols_bytes.extend(byte)
                
                old_cols_str = cols_bytes.decode('UTF-8', errors='ignore')
            
            # Prepare new metadata
            c_new = c_old + len(new_columns)
            new_cols_list = old_cols_str.split(',') + new_columns
            new_cols_str = ','.join(new_cols_list)
            new_cols_b = str.encode(new_cols_str, encoding='UTF-8', errors='ignore') + b'\x00'
            
            # === ZERO-COPY MAGIC: Just extend the data file! ===
            # In Fortran order, each column is stored contiguously, so we just append new columns
            nb_new_column_data = r * len(new_columns) * 8  # bytes for new columns
            current_size = os.path.getsize(filepath)
            new_size = current_size + nb_new_column_data
            
            # Extend data file with NaN-filled new columns
            with open(filepath, 'ab') as f:
                # Seek to new end
                f.seek(new_size - 1)
                f.write(b'\x00')
                if os.name == 'posix':
                    f.flush()
                    os.posix_fallocate(f.fileno(), current_size, nb_new_column_data)
            
            # Map new columns and fill with NaN
            new_col_shf = np.memmap(filepath, dtype='<f8', mode='r+',
                                    offset=current_size, shape=(r, len(new_columns)), order='F')
            new_col_shf[:] = np.nan
            new_col_shf.flush()
            del new_col_shf
            
            # Update metadata file with new header and column names
            new_header_b = np.array([3, r, c_new], dtype=np.int64).tobytes()
            
            with open(metapath, 'wb') as f:
                f.write(new_header_b)
                f.write(idx_b)
                f.write(new_cols_b)
            
            # Update instance attributes
            self.columns = pd.Index(new_cols_list)
            self.symbolidx = {col: i for i, col in enumerate(self.columns)}
            
            # Remap the ENTIRE data file (now with more columns)
            self.shf = np.memmap(filepath, dtype='<f8', mode='r+',
                                offset=0, shape=(r, c_new), order='F')
            
            self.data = pd.DataFrame(self.shf,
                                    index=self.index,
                                    columns=self.columns,
                                    copy=False)
            self.data.index.name = 'date'
            
            Logger.log.info(f'Zero-copy appended {len(new_columns)} columns to {filepath} (no data copied!)')
            
            return self.data
            
        except Exception as e:
            Logger.log.error(f'Failed to append columns: {str(e)}')
            raise Exception(f'Failed to append columns: {str(e)}')
        finally:
            # Always release mutex lock
            self.release()

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

    def free(self):
        """
        Releases resources associated with the object by flushing and deleting the memory-mapped file and its related DataFrame if they exist. Also removes the corresponding tag from the shared data dictionary based on the constructed path.
        
        This method ensures that all changes are saved to disk and that memory is freed by deleting references to large data structures.
        """
        if hasattr(self, 'shf'):
            self.shf.flush()  # Ensure all changes are written back to the file
            del self.shf  # Delete the memmap object
            if hasattr(self, 'data'):
                del self.data  # Ensure DataFrame is also deleted if it exists
            
        path = f'{self.user}/{self.database}/{self.period}/{self.source}/timeseries'
        if path in self.shareddata.data.keys():
            del self.shareddata.data[path].tags[self.tag]
    
    def check_for_new_columns(self):
        """
        Check if new columns have been added by another process and reload if detected.
        
        This method reads the metadata file header to check if the column count has changed.
        If changes are detected, it waits for any in-progress modifications to complete,
        then remaps the file with the updated structure.
        
        This is useful for multi-process scenarios where one process might add columns
        while others are reading the data.
        
        Example usage:
            ts = shdata.timeseries('MarketData', 'D1', 'TEST', 'PRICES')
            # ... some time passes, another process adds columns ...
            if ts.check_for_new_columns():
                print("New columns detected and loaded")
            df = ts.data  # Now access the data with new columns
        
        Returns:
            bool: True if new columns were detected and reload occurred, False otherwise
            
        Note:
            This method does NOT acquire a lock itself (read-only operation on header), but it
            will wait if another process holds the lock during file structure modification.
        """
        filepath = self.path
        metapath = str(filepath).replace('.bin', '.meta')
        
        # Check if files exist
        if not os.path.exists(filepath):
            Logger.log.debug(f'File does not exist: {filepath}')
            return False
        
        # Only check if we already have data loaded
        if not hasattr(self, 'data') or self.data is None:
            return False
        
        try:
            # For V3 format, read metadata file
            if os.path.exists(metapath):
                with open(metapath, 'rb') as f:
                    header = np.frombuffer(f.read(24), dtype=np.int64)
                    file_col_count = header[2]
            else:
                # V1 format (single file) - read old header
                with open(filepath, 'rb') as f:
                    header = np.frombuffer(f.read(40), dtype=np.int64)
                    file_col_count = header[1]
            
            current_col_count = len(self.columns)
            
            if file_col_count != current_col_count:
                Logger.log.info(f'Detected column count change for {self.tag}: {current_col_count} -> {file_col_count}')
                
                # Wait for any in-progress file modifications by briefly acquiring and releasing lock
                # This ensures we don't read a partially-modified file
                self.acquire()
                self.release()
                
                # Flush any pending changes
                if hasattr(self, 'shf'):
                    self.shf.flush()
                
                # Clean up current mapping
                if hasattr(self, 'shf'):
                    del self.shf
                if hasattr(self, 'data'):
                    del self.data
                
                # Remap with new structure
                _data = self.malloc_map()
                self.data = _data
                self.columns = self.data.columns
                self.symbolidx = {col: i for i, col in enumerate(self.columns)}
                
                Logger.log.info(f'Successfully reloaded {self.tag} with {file_col_count} columns')
                return True
                
        except Exception as e:
            Logger.log.error(f'Failed to check for new columns: {e}', exc_info=True)
            return False
        
        return False
    
    