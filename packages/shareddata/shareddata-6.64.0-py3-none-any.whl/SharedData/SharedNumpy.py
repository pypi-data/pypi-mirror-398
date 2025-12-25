import pandas as pd
import numpy as np
import time
from datetime import datetime
import os
import bson

from SharedData.Logger import Logger
from SharedData.TableIndexJitFunctions import *
from SharedData.TableIndexJitLoc import *
from SharedData.Utils import mmaparray2df
from SharedData.Database import STRING_FIELDS
       
class SharedNumpy(np.ndarray):

    """
    A subclass of numpy.ndarray designed to represent and manage shared data tables with support for both in-memory and disk-backed storage.
    
    This class integrates tightly with a backing 'table' object that manages metadata, indexing, and persistence. It provides methods for inserting, extending, and upserting records, as well as querying by primary key, date, symbol, portfolio, and tags. It supports synchronization features such as subscribing and publishing data streams.
    
    Key features:
    - Supports two types of storage: 'MEMORY' (in-memory ndarray) and 'DISK' (memory-mapped file).
    - Automatic handling of record metadata such as modification time.
    - Index management and fast lookup operations on primary keys and other indexed fields.
    - Conversion utilities between numpy structured arrays and pandas DataFrames.
    - Methods to manage memory mapping and file resizing for disk-backed tables.
    - Stream reading and synchronization capabilities for real-time data updates.
    - Properties to access and modify table metadata like count, record size, modification time, and indexes.
    
    Intended for use in high-performance data applications requiring efficient storage, indexing, and querying of large structured datasets.
    """
    def __new__(cls, type, *args, **kwargs):
        """
        Create a new instance of the class based on the specified type.
        
        Parameters:
            cls (type): The class to instantiate.
            type (str): The type of instance to create. Must be either 'MEMORY' or 'DISK'.
            *args: Additional positional arguments passed to the underlying ndarray or memmap.
            **kwargs: Additional keyword arguments passed to the underlying ndarray.
        
        Returns:
            instance: A new instance of the class, either a standard ndarray subclass ('MEMORY') or a memmap-backed subclass ('DISK').
        
        Raises:
            Exception: If the provided type is not 'MEMORY' or 'DISK'.
        """
        if type == 'MEMORY':
            obj = np.ndarray.__new__(cls, *args, **kwargs)
            obj.table = None
            return obj
        elif type == 'DISK':
            memmap = args[0]
            obj = memmap.view(cls)
            obj.memmap = memmap
            obj.table = None
            obj._df = None
            return obj
        else:
            raise Exception('Unknown type %s!' % (type))

    ################################ TABLE MUTEX ########################################
    def acquire(self):
        """
        Acquires a lock on the table to ensure thread-safe operations.
        """
        self.table.acquire()
    
    def release(self):
        """
        Releases the lock on the table after thread-safe operations are complete.
        """
        self.table.release()

    ################################ RESOURCE MANAGEMENT ########################################

    def free(self):
        """
        Releases the resources held by the table by invoking its `free` method.
        """
        self.table.free()
        # Close BSON mmap and file handle if open
        if hasattr(self.table, 'bson_mmap') and self.table.bson_mmap is not None:
            self.table.bson_mmap.flush()  # Ensure all writes are committed
            self.table.bson_mmap.close()
            self.table.bson_mmap = None
        
        if hasattr(self.table, 'bson_file_handle') and self.table.bson_file_handle is not None:
            self.table.bson_file_handle.close()
            self.table.bson_file_handle = None

    def cleanup_local_files(self):
        """
        Clean up local BSON and table files before accessing remote versions.
        """
        # Clean up BSON file
        if hasattr(self.table, 'bsonpath') and self.table.bsonpath.exists():
            self.table.bsonpath.unlink()

        # Clean up table files
        if self.table.filepath.exists():
            self.table.filepath.unlink()
        if self.table.headpath.exists():
            self.table.headpath.unlink()
        if self.table.tailpath.exists():
            self.table.tailpath.unlink()

        # Clean up index files
        if hasattr(self.table.index, 'pkeypath') and os.path.exists(self.table.index.pkeypath):
            os.unlink(self.table.index.pkeypath)
        if hasattr(self.table.index, 'dateidxpath') and os.path.exists(self.table.index.dateidxpath):
            os.unlink(self.table.index.dateidxpath)
        if hasattr(self.table.index, 'symbolidxpath') and os.path.exists(self.table.index.symbolidxpath):
            os.unlink(self.table.index.symbolidxpath)
        if hasattr(self.table.index, 'portidxpath') and os.path.exists(self.table.index.portidxpath):
            os.unlink(self.table.index.portidxpath)

    def trim(self):
        """
        Optimize the internal table by trimming unused elements or reducing its storage size.
        
        This method delegates the trimming operation to the internal `table` attribute's `trim` method, which is responsible for optimizing the underlying data structure.
        """
        self.table.trim()

    def write(self,force_write=False):
        """
        Writes the table data to storage, optionally forcing the write operation.
        
        If the table has an index (`hasindex` is 1) and the index is not sorted (`isidxsorted` is 0),
        the index is sorted before writing. The write operation is then performed on the table,
        with the option to force the write regardless of internal conditions.
        
        Parameters:
            force_write (bool): If True, forces the write operation even if not necessary. Defaults to False.
        """
        if self.table.hdr['hasindex']==1 and self.table.hdr['isidxsorted']==0:
            self.sort_index()
        self.table.write(force_write)
        
    def rememmap(self):
        """
        Create and return a memory-mapped view of the table's records.
        
        This method creates a numpy memmap object for the table's data file with the appropriate dtype and shape,
        then creates a new instance of the current class viewing this memmap. It sets the table and memmap attributes
        on the new instance, updates the table's records reference to this new instance, and returns it.
        
        Returns:
            An instance of the current class that provides a memory-mapped view of the table's records.
        """
        memmap = np.memmap(self.table.filepath, self.table.recdtype, 'r+', self.table.hdr.dtype.itemsize, (self.recordssize,))
        new_instance = memmap.view(self.__class__)
        new_instance.table = self.table
        new_instance.memmap = memmap
        self.table.records = new_instance
        self.table.size = self.recordssize
        return new_instance
    
    def reload(self):
        """
        Reloads the data in the table by calling the table's reload method.

        Returns:
            The result of the table's reload operation.
        """
        return self.table.reload()

    def reload_remote(self):
        """
        Forces a reload from remote S3 storage by cleaning up local files and downloading fresh versions.

        This method:
        1. Cleans up all local table and BSON files
        2. Downloads the latest data from S3
        3. Reinitializes the table structure

        Returns:
            self: The reloaded SharedNumpy instance

        Raises:
            Exception: If remote data cannot be downloaded or table cannot be reloaded
        """
        # Clean up local files first
        self.cleanup_local_files()

        # Force re-download from S3 by resetting modification times in header
        if hasattr(self.table, 'hdr'):
            # Reset modification times to force download
            self.table.hdr['mtimehead'] = 0
            self.table.hdr['mtimetail'] = 0

        # Re-download and reload
        self.table.download()

        # Force remapping of files
        if self.table.type == 1:  # DISK type
            self.rememmap()

        return self

    def auto_grow(self, min_add_rows):
        """
        Auto-grow the underlying disk-backed table by at least `min_add_rows`.
        Follows the exact same logic as Table.__init__ when size is increased.
        
        Grows by at least 100MB (page-aligned) or min_add_rows, whichever is larger,
        to avoid multiple resizes.
        
        Returns the updated SharedNumpy records object after resizing.
        No-op for in-memory tables (returns self unchanged).
        
        Parameters:
            min_add_rows (int): Minimum number of rows to add to the table.
            
        Returns:
            SharedNumpy: The updated records object with the new memory map.
        """
        try:
            Logger.log.debug('Auto-growing table %s by at least %d rows' % (getattr(self.table, 'relpath', '?'), min_add_rows))
            # Calculate growth size (same as extend method)
            rec = self.table.records
            page_size = 4096
            extend_size = int(np.round(100 * 1024 * 1024 / page_size) * page_size)
            new_rows = int(np.floor(extend_size / rec.dtype.itemsize))
            new_rows = max(new_rows, int(min_add_rows))
            
            new_size = self.recordssize + new_rows            
            self.table.size = new_size
            self.recordssize = new_size
            self.table.malloc()  # extend file only
                                    
            # Return the updated records object
            return self.table.records
            
        except Exception as e:
            errmsg = 'Error during auto-grow for %s: %s' % (getattr(self.table, 'relpath', '?'), str(e))
            Logger.log.error(errmsg)
            raise Exception(errmsg)    
    
    ################################# SYNC TABLE ########################################
    def subscribe(self, host, port=None, lookbacklines=1000, lookbackdate=None, method='websocket', snapshot=False, bandwidth=1e6, protocol='http'):
        """
        Subscribe to a data source with specified connection parameters.
        
        Parameters:
            host (str): The hostname or IP address of the data source.
            port (int, optional): The port number to connect to. Defaults to None.
            lookbacklines (int, optional): Number of lines to look back from the data source. Defaults to 1000.
            lookbackdate (str or datetime, optional): Specific date to look back to. Defaults to None.
            method (str, optional): Connection method to use (e.g., 'websocket'). Defaults to 'websocket'.
            snapshot (bool, optional): Whether to take a snapshot of the data upon subscription. Defaults to False.
            bandwidth (float, optional): Bandwidth limit in bits per second. Defaults to 1e6.
            protocol (str, optional): Protocol to use for the connection (e.g., 'http'). Defaults to 'http'.
        
        This method delegates the subscription request to the underlying table object's subscribe method.
        """
        self.table.subscribe(host, port, lookbacklines,
                             lookbackdate, method, snapshot, bandwidth,protocol)
        
    def publish(self, host, port=None, lookbacklines=1000, lookbackdate=None, method='websocket', snapshot=False, bandwidth=1e6, protocol='http'):
        """
        Publish the table data to a specified host and port using the given parameters.
        
        Parameters:
            host (str): The hostname or IP address to publish to.
            port (int, optional): The port number to use for publishing. Defaults to None.
            lookbacklines (int, optional): Number of lines to look back for data. Defaults to 1000.
            lookbackdate (str or datetime, optional): Date to look back from for data. Defaults to None.
            method (str, optional): The method of publishing, e.g., 'websocket'. Defaults to 'websocket'.
            snapshot (bool, optional): Whether to publish a snapshot of the data. Defaults to False.
            bandwidth (float, optional): Bandwidth limit in bits per second. Defaults to 1e6.
            protocol (str, optional): Protocol to use for publishing, e.g., 'http'. Defaults to 'http'.
        
        Returns:
            None
        """
        self.table.publish(host, port, lookbacklines,
                             lookbackdate, method, snapshot, bandwidth,protocol)
    
    def read_stream(self, buffer):
        
        """
        Reads and processes complete records from the given byte buffer.
        
        This method checks if the buffer contains enough bytes to form at least one complete record
        based on the predefined item size. It extracts all complete records from the buffer, converts
        them into a NumPy array of the specified data type, and then either upserts or extends these
        records into the associated table depending on whether the table has an index. The processed
        bytes are removed from the buffer.
        
        Parameters:
            buffer (bytearray): The byte buffer containing raw data to be read and processed.
        
        Returns:
            bytearray: The remaining buffer after extracting and processing complete records.
        """
        if len(buffer) >= self.itemsize:
            # Determine how many complete records are in the buffer
            num_records = len(buffer) // self.itemsize
            # Take the first num_records worth of bytes
            record_data = buffer[:num_records * self.itemsize]
            # And remove them from the buffer
            del buffer[:num_records * self.itemsize]
            # Convert the bytes to a NumPy array of records
            rec = np.frombuffer(
                record_data, dtype=self.dtype)
            
            if self.table.hasindex:
                # Upsert all records at once
                self.upsert(rec)
            else:
                # Extend all records at once
                self.extend(rec)

        return buffer

    ############################## KEYLESS OPERATIONS ########################################

    def insert(self, new_records, acquire=True):
        """
        Insert new records into the table, optionally acquiring a lock during the operation.
        
        Parameters:
            new_records (numpy.ndarray): Array of new records to be inserted.
            acquire (bool, optional): Whether to acquire the table lock before insertion. Defaults to True.
        
        Raises:
            Exception: If the table's maximum size is exceeded or if any error occurs during insertion.
        
        Behavior:
            - Acquires the table lock if `acquire` is True.
            - Checks if there is enough space to insert the new records.
            - Converts `new_records` to the table's dtype if necessary.
            - Updates any 'mtime' fields with NaT values to the current time in nanoseconds.
            - Inserts the new records into the table's underlying array.
            - Updates the record count and modification time.
            - Releases the table lock if it was acquired.
            - Logs errors and raises exceptions on failure.
        """
        errmsg = ''
        try:
            if acquire:
                self.table.acquire()

            nrec = new_records.size
            _count = self.count
            if (_count + nrec <= self.size):
                # convert new_records
                if (self.dtype != new_records.dtype):
                    new_records = self.convert(new_records)
                # fill mtime
                nidx = np.isnat(new_records['mtime'])
                if nidx.any():
                    new_records['mtime'][nidx] = time.time_ns()

                arr = super().__getitem__(slice(0, self.size))
                arr[_count:_count+nrec] = new_records
                self.count = _count + nrec
                self.mtime = datetime.now().timestamp()
            else:
                errmsg = 'Table max size reached!'
                Logger.log.error(errmsg)
        except Exception as e:
            errmsg = 'Error inserting %s!\n%s' % (self.table.relpath, str(e))
            Logger.log.error(errmsg)
        finally:
            if acquire:
                self.table.release()
            if errmsg:
                raise Exception(errmsg)

    def extend(self, new_records, acquire=True):
        """
        '''
        Extend the underlying table by appending new records.
        
        This method attempts to add `new_records` to the table's data storage, handling file resizing and memory mapping as needed. It performs several checks and operations:
        
        - Raises an exception if the table is in-memory or has an index, as extending is not supported in these cases.
        - Optionally acquires a lock on the table before modification.
        - If the current allocated record size is insufficient, extends the file size by approximately 100MB (aligned to page size) to accommodate new records.
        - Uses memory mapping to remap the extended file region.
        - Converts `new_records` to the appropriate dtype if necessary.
        - Fills missing modification times ('mtime') in `new_records` with the current time in nanoseconds.
        - Inserts the `new_records` into the table without acquiring the lock again.
        - Releases the lock if it was acquired.
        - Logs and raises exceptions encountered during the process.
        
        Parameters:
            new_records (numpy.ndarray): Array of new records to append to the table.
            acquire (bool, optional): Whether to acquire the table lock during the operation. Defaults to True.
        
        Returns:
            SharedNumpy: The updated records object of the table after extension.
        
        Raises:
            Exception: If the
        """
        errmsg = ''

        if self.table.hdr['hasindex'] == 1:
            raise Exception(
                'Table %s has index, extend not supported!' % (self.table.relpath))
        
        # At this point, new_records should have a size attribute
        if len(new_records) <= 0:
            return

        new_records, dict_list = self.any2records(new_records)

        try:
            if acquire:
                self.table.acquire()
            
            if self.table.size < self.recordssize:
                self = self.rememmap()

            nrec = new_records.size
            _count = self.count.copy()
            
            if (_count + nrec > self.recordssize):
                # extend table by 10MB
                rec = self.table.records
                page_size = 4096
                extend_size = int(np.round(100 * 1024 * 1024 / page_size) * page_size)
                new_rows = int(np.floor(extend_size/rec.dtype.itemsize))
                new_rows = max(new_rows, nrec)

                new_recordssize = rec.size + new_rows
                hdr_bytes = self.table.hdr.dtype.itemsize
                rec_bytes = rec.dtype.itemsize * rec.size                
                totalbytes = hdr_bytes + rec_bytes + rec.dtype.itemsize*new_rows
                
                with open(self.table.filepath, 'ab+') as f:
                    # Seek to the end of the file
                    f.seek(totalbytes-1)
                    # Write a single null byte to the end of the file
                    f.write(b'\x00')
                    if os.name == 'posix':
                        os.posix_fallocate(f.fileno(), 0, totalbytes)
                    elif os.name == 'nt':
                        pass  # TODO: implement preallocation for windows in pyd

                # remap extended file
                if self.table.shf_data is not None:
                    self.table.shf_data.flush()
                self.table.shf_data = np.memmap(
                    self.table.filepath,rec.dtype,'r+',
                    hdr_bytes,(new_recordssize,) )
                self.table.records = SharedNumpy('DISK', self.table.shf_data)
                self.table.records.table = self.table                
                self.recordssize = new_recordssize
            
            # fill mtime
            nidx = np.isnat(new_records['mtime'])
            if nidx.any():
                new_records['mtime'][nidx] = time.time_ns()
            # insert data
            self.table.records.insert(new_records, acquire=False)

            if self.table.is_schemaless and dict_list:
                self.store_dictionaries_batch(self.table.records, range(_count, _count + nrec), dict_list)
            
            return self.table.records
        

        except Exception as e:
            errmsg = 'Error extending %s!\n%s' % (self.table.relpath, str(e))
            Logger.log.error(errmsg)
        finally:
            if acquire:
                self.table.release()
            if errmsg:
                raise Exception(errmsg)

    ############################## PRIMARY KEY OPERATIONS ########################################
    @property
    def loc(self):
        """
        Provides a location-based indexer for selecting data by label.
        
        Returns:
            _LocIndexer: An instance of the _LocIndexer class initialized with the current object,
            enabling label-based indexing and slicing operations.
        """
        return _LocIndexer(self)

    def upsert(self, new_records, acquire=True):        
        """
        Upserts new records into the table, updating existing entries or inserting new ones as needed.
        
        This method performs an upsert operation (update if exists, insert if not) on the table data.
        It automatically handles table growth when near capacity, maintains indexes, and supports
        schemaless tables with BSON data storage.
        
        Key behaviors:
        - Validates and converts input records to the appropriate dtype
        - Removes records with invalid primary keys or out-of-range dates
        - Auto-grows the table when approaching 99% capacity to prevent overflow
        - Preserves existing BSON data for schemaless table updates
        - Updates modification times and maintains index integrity
        - Handles concurrency through optional table locking
        - CRITICAL: Refreshes index array references after auto-grow to prevent stale memory references
        
        Parameters:
            new_records (np.ndarray, pd.DataFrame, dict, or list): The records to be upserted.
                - np.ndarray: A numpy structured array matching the table's dtype
                - pd.DataFrame: A pandas DataFrame with columns matching table schema
                - dict: A single record dictionary (converted to structured array internally)
                - list: A list of dictionaries (converted to structured array internally)
            acquire (bool, optional): Whether to acquire a lock on the table during the operation. 
                Defaults to True. Set to False only when called from methods that already hold the lock.
        
        Returns:
            SharedNumpy: The updated records object of the table after upsert. This may be a new
            object if the table was auto-grown during the operation.
        
        Raises:
            Exception: If the table has no index, if the table becomes full after upsert, 
                or if any error occurs during the upsert process.
        
        Notes:
            - Requires the table to have an index (hasindex=1)
            - For schemaless tables, BSON data is stored separately and referenced via bson_ptr/bson_size fields
            - Auto-growth allocates additional space (minimum 100MB) to avoid frequent resizing
            - Index sorting is deferred until write time for performance
            - Thread-safe when acquire=True (default)
            - After auto-grow and index initialization, all index array references are refreshed to point
              to the new memory-mapped locations, preventing duplicate key issues
        """
        if self.table.hdr['hasindex'] == 0:
            raise Exception('Table %s has no index!' % (self.table.relpath))
                
        # At this point, new_records should have a size attribute
        if len(new_records) <= 0:
            return self.table.records
            
        new_records, dict_list = self.any2records(new_records)

        new_records, dict_list = self.remove_invalid_records(new_records, dict_list)
        
        if new_records.size <= 0:
            return self.table.records
        
        # single record to array
        if new_records.shape == ():
            new_records = np.array([new_records])

        success = False
        try:
            if acquire:
                self.table.acquire()

            # Remap if table size changed externally
            if self.table.size < self.recordssize:
                self = self.rememmap()
                # Also remap index files to match new table size                
                self.table.index.rememmap()
            
            # Ensure index exists and is valid
            if self.table.hdr['isidxcreated'] == 0:
                self.index.create_index(self, self.pkey)

            # Auto-grow if we're near capacity (99% threshold)
            # This ensures we have space for potential new inserts during upsert
            nrec = new_records.size
            threshold = int(np.floor(self.recordssize * 0.99))
            
            if (self.count + nrec) >= threshold:
                # Calculate needed rows: at least nrec, or the difference to reach threshold
                needed = max(nrec, (self.count + nrec) - self.recordssize + 1)
                
                # Auto-grow returns updated records object with new memory map
                updated_records = self.auto_grow(needed)
                self.table.records = updated_records
                self = updated_records

                # Reinitialize index - creates NEW memory-mapped index arrays
                # After this call, all previous index array references become stale
                if self.table.hdr['hasindex'] == 1:
                    self.table.hdr['isidxcreated'] = 0
                    self.table.hdr['isidxsorted'] = 0
                    self.table.index.initialize()
                
                # Get FULL array (not just up to count) from updated records
                # Use ndarray.__getitem__ to bypass custom slicing
                arr = np.ndarray.__getitem__(updated_records, slice(0, updated_records.size))
            else:
                # No auto-grow needed, get full array from current records
                arr = super().__getitem__(slice(0, self.size))

            # Preserve existing BSON pointers/sizes for schemaless updates
            if self.table.is_schemaless:
                loc = self.get_loc(new_records, acquire=False)
                vidx = loc != -1
                if vidx.any():
                    new_records['bson_ptr'][vidx] = self['bson_ptr'][loc[vidx]]
                    new_records['bson_size'][vidx] = self['bson_size'][loc[vidx]]
                
                if not vidx.all():
                    # New records being inserted - initialize bson fields
                    new_records['bson_ptr'][~vidx] = -1
                    new_records['bson_size'][~vidx] = 0

            # Mark index as dirty before upsert
            minchgid = self.count
            self.table.hdr['isidxcreated'] = 0

            # CRITICAL: Get fresh references to ALL index arrays
            # This is essential after initialize() creates new memory-mapped files
            # Without this, JIT functions receive stale pointers causing duplicate keys
            # 
            # Why this is needed:
            # 1. Properties like self.pkey return self.table.index.pkey (a cached reference)
            # 2. When initialize() runs, it creates NEW mmap arrays at NEW memory locations
            # 3. Old cached references point to OLD (deallocated or remapped) memory
            # 4. JIT functions searching stale index don't find existing records
            # 5. Result: Duplicates inserted instead of updates
            #
            # Solution: Explicitly fetch fresh references after any potential initialize()
            index = self.table.index
            pkey = index.pkey
            datelastidx = index.datelastidx 
            dateprevidx = index.dateprevidx 
            portlastidx = index.portlastidx 
            portprevidx = index.portprevidx 
            symbollastidx = index.symbollastidx 
            symbolprevidx = index.symbolprevidx 

            # Call JIT upsert function with fresh index array references
            self.count, minchgid, isidxsorted, upsertpos = self.index.upsert_func(
                arr, self.count, new_records, pkey,
                datelastidx, dateprevidx,
                self.table.mindate, self.table.periodns,
                portlastidx, portprevidx,
                symbollastidx, symbolprevidx)
            
            # Update index status
            self.table.hdr['isidxsorted'] = 1 if isidxsorted else 0
            self.table.hdr['isidxcreated'] = 1

            # For schemaless tables, store BSON data
            if self.table.is_schemaless and dict_list:
                self.store_dictionaries_batch(arr, upsertpos, dict_list)

            # Update metadata
            minchgid = int(minchgid)
            self.minchgid = minchgid
            self.mtime = datetime.now().timestamp()
            
            success = True

        except Exception as e:
            Logger.log.error('Error upserting %s!\n%s' % (self.table.relpath, str(e)))
            raise
        finally:
            if acquire:
                self.table.release()
            
            # Check for table full condition
            if self.count >= self.size:
                Logger.log.critical('Table %s is full!' % self.table.relpath)
            
            if not success:
                raise Exception('Error upserting %s!' % self.table.relpath)
        
        return self.table.records

    def sort_index(self, start=0):
        """
        Sorts the index of the object starting from the specified position.
        
        Parameters:
            start (int): The position from which to start sorting the index. Defaults to 0.
        
        Note:
            This method calls the `sort_index` method of the `index` attribute, passing the current object and the start position.
        """
        self.index.sort_index(self, start)

    def get_loc(self, keys, acquire=True):
        """
        Retrieve the location(s) of the specified key(s) within the indexed table.
        
        This method attempts to find the integer positions of one or multiple keys in the table's index.
        If the index is not yet created, it will be generated automatically. Optionally, the table lock
        can be acquired and released during the operation to ensure thread safety.
        
        Parameters:
            keys (array-like): The key or collection of keys to locate in the table index.
            acquire (bool, optional): Whether to acquire and release the table lock during the operation.
                                      Defaults to True.
        
        Returns:
            numpy.ndarray: An array of integer indices corresponding to the locations of the provided keys.
        
        Raises:
            Exception: If the table lacks an index, if an error occurs during location retrieval,
                       or if the index is not properly created and cannot be generated.
        """
        success = False
        if self.table.hdr['hasindex'] != 1:
            raise Exception(f'Table {self.table.relpath} does not have index!')
        
        try:
            if acquire:
                self.table.acquire()

            # check if index is created & valid
            if self.table.hdr['isidxcreated'] == 0:
                self.index.create_index(self, self.pkey)

            # Get fresh reference to pkey after potential create_index() call
            # create_index() may reinitialize index arrays at new memory locations
            pkey = self.table.index.pkey
            
            loc = self.index.get_loc_func(
                self[:], pkey, keys).astype(np.int64)
            success = True
        except Exception as e:
            Logger.log.error('Error getting loc for %s!\n%s' %
                             (self.table.relpath, str(e)))
            loc = np.array([])
        finally:
            if acquire:
                self.table.release()
            if not success:
                raise Exception('Error getting loc for %s!' %
                                (self.table.relpath))
        return loc

    def get_date_loc(self, date, maxids=0, acquire=True):
        """
        Retrieve the location indices corresponding to a specified date within the table's index.
        
        Parameters:
            date (pd.Timestamp or np.datetime64): The date for which to find location indices.
            maxids (int, optional): Maximum number of indices to return. Defaults to 0, meaning no limit.
        
        Returns:
            np.ndarray: An array of location indices matching the given date. Returns an empty array if the date is out of the table's date range.
        
        Raises:
            Exception: If the table does not have an index, if the index is not created and cannot be created, or if an error occurs during retrieval.
        """
        success = False
        if self.table.hdr['hasindex'] != 1:
            raise Exception(f'Table {self.table.relpath} does not have index!')
        try:
            if acquire:
                self.table.acquire()

            # check if index is created & valid
            if self.table.hdr['isidxcreated'] == 0:
                self.index.create_index(self, self.pkey)
            
            if isinstance(date, pd.Timestamp):
                date = np.datetime64(date,'ns')

            # Get fresh references to index arrays after potential create_index() call
            index = self.table.index
            datelastidx = index.datelastidx
            dateprevidx = index.dateprevidx            
            mindate = self.table.mindate
            periodns = self.table.periodns
            if (date < mindate) | (date >= self.table.maxdate):
                loc = np.array([])                
            else:                            
                loc = get_date_loc_jit(date, datelastidx, dateprevidx, mindate, periodns, maxids)
            
            success = True
        except Exception as e:
            Logger.log.error('Error getting date_loc for %s!\n%s' %
                             (self.table.relpath, str(e)))
        finally:
            if acquire:
                self.table.release()
            if not success:
                raise Exception('Error getting date_loc for %s!' %
                                (self.table.relpath))
        return loc

    # get date loc greater than or equal to startdate
    def get_date_loc_gte(self, startdate, maxids=0):
        """
        Retrieve the indices of records with dates greater than or equal to a specified start date.
        
        This method returns a NumPy array of record indexes where the date is greater than or equal to `startdate`.
        It utilizes a Just-In-Time (JIT) compiled function for fast execution. The table must have an index
        available, otherwise an exception is raised.
        
        Parameters:
            startdate (pd.Timestamp or np.datetime64): The start date to compare against.
            maxids (int, optional): Maximum number of record indexes to return. Defaults to 0 (no limit).
        
        Returns:
            np.ndarray: Array of record indexes with dates >= `startdate`.
        
        Raises:
            Exception: If the table does not have an index.
        """
        if self.table.hdr['hasindex'] != 1:
            raise Exception(f'Table {self.table.relpath} does not have index!')
        if isinstance(startdate, pd.Timestamp):
            startdate = np.datetime64(startdate, 'ns')

        datelastidx = self.table.index.datelastidx
        dateprevidx = self.table.index.dateprevidx
        mindate = self.table.mindate
        periodns = self.table.periodns

        return get_date_loc_gte_jit(startdate, datelastidx, dateprevidx, mindate, periodns, maxids)
    
    # get date loc less than or equal to enddate
    def get_date_loc_lte(self, enddate, maxids=0):
        """
        Retrieve the indices of records with dates less than or equal to a specified end date.
        
        This method returns a NumPy array of record indexes where the record dates are less than or equal to the given `enddate`. It uses a Just-In-Time (JIT) compiled function for fast execution. The method requires the underlying table to have an index; otherwise, it raises an exception.
        
        Parameters:
            enddate (pd.Timestamp or np.datetime64): The end date to compare against record dates.
            maxids (int, optional): Maximum number of record indexes to return. Defaults to 0 (no limit).
        
        Returns:
            np.ndarray: Array of record indexes with dates <= `enddate`.
        
        Raises:
            Exception: If the table does not have an index.
        """
        if self.table.hdr['hasindex'] != 1:
            raise Exception(f'Table {self.table.relpath} does not have index!')
        if isinstance(enddate, pd.Timestamp):
            enddate = np.datetime64(enddate, 'ns')

        datelastidx = self.table.index.datelastidx
        dateprevidx = self.table.index.dateprevidx
        mindate = self.table.mindate
        periodns = self.table.periodns

        return get_date_loc_lte_jit(enddate, datelastidx, dateprevidx, mindate, periodns, maxids)

    def store_dictionaries_batch(self, records, upsertpos, dict_list):
        """High-performance batched BSON storage with in-place updates when possible.

        Strategy per record to minimize file growth:
        - Empty dict -> clear ptr/size (no space freed)
        - Fits in current position (new_size <= old_size) -> in-place overwrite
        - Doesn't fit (new_size > old_size) -> allocate new space at end (old space becomes unused)
                
        Write-only operations for maximum performance. Exceptions abort the batch.
        """
        if not dict_list:
            return

        table = self.table        
        
        # Initialize mmap if needed
        need_remap = (self.next_bson_ptr < self.prev_bson_ptr)\
                  or (self.table.curr_bson_size < self.next_bson_ptr)
        if need_remap:
            self.table.init_bson_mmap()
        self.prev_bson_ptr = self.next_bson_ptr

        # Fast path: all new inserts (common in extend)
        all_new = True
        for pos in upsertpos:
            if records[pos]['bson_size'] != 0:
                all_new = False
                break
        
        if all_new:
            encoded = []
            total = 0
            for d in dict_list:
                if not d:
                    encoded.append((b'', 0))
                    continue
                bts = bson.encode(d)                
                sz = len(bts)
                encoded.append((bts, sz))
                total += sz
            
            if total > 0:
                base = table.allocate_bson_space(total)
                cur = 0
                for (bts, sz), pos in zip(encoded, upsertpos):
                    if sz > 0:                        
                        table.bson_mmap[base + cur:base + cur + sz] = bts                        
                        records[pos]['bson_ptr'] = base + cur
                        records[pos]['bson_size'] = sz
                        cur += sz
                    else:
                        records[pos]['bson_ptr'] = 0
                        records[pos]['bson_size'] = 0
            else:
                for pos in upsertpos:
                    records[pos]['bson_ptr'] = 0
                    records[pos]['bson_size'] = 0
            return

        # General path: separate updates that fit in place from those that need new allocation
        inplace_updates = []
        new_alloc_positions = []
        encoded_for_new = []
        clear_positions = []

        for pos, d in zip(upsertpos, dict_list):
            old_size = int(records[pos]['bson_size'])
            old_ptr = int(records[pos]['bson_ptr'])

            if not d:
                # Clear the record (old space becomes unused)
                clear_positions.append(pos)
                continue

            bts = bson.encode(d)
            new_size = len(bts)

            # Check if we can reuse the existing position
            # CRITICAL: Only reuse if old_ptr is valid (>= 0) AND new size fits
            if old_size > 0 and old_ptr >= 0 and new_size <= old_size:
                # Fits in current position: in-place overwrite
                inplace_updates.append((old_ptr, bts, pos, new_size, old_size))
            else:
                # Doesn't fit or no existing allocation: allocate new space
                # (old space becomes unused - will be reclaimed by defragment)
                new_alloc_positions.append(pos)
                encoded_for_new.append(bts)

        # In-place overwrites (mmap) - zero out unused bytes for cleanliness
        for ptr, bts, pos, new_size, old_size in inplace_updates:
            table.bson_mmap[ptr:ptr + new_size] = bts
            
            # Zero out any remaining bytes from the old allocation
            if new_size < old_size:
                table.bson_mmap[ptr + new_size:ptr + old_size] = b'\x00' * (old_size - new_size)
            
            records[pos]['bson_size'] = new_size
            # Keep the same ptr

        # New allocations (batched, mmap)
        if encoded_for_new:
            sizes = [len(b) for b in encoded_for_new]
            total = sum(sizes)
            if total > 0:
                base = table.allocate_bson_space(total)
                cur = 0
                for bts, pos, sz in zip(encoded_for_new, new_alloc_positions, sizes):                    
                    table.bson_mmap[base + cur:base + cur + sz] = bts                    
                    records[pos]['bson_ptr'] = base + cur
                    records[pos]['bson_size'] = sz
                    cur += sz

        # Clear empty positions
        for pos in clear_positions:
            records[pos]['bson_ptr'] = -1
            records[pos]['bson_size'] = 0

    def get_dict_list(self, loc, acquire=True):
        """
        Decode BSON data from schemaless records into DataFrame format with primary keys as index.

        For schemaless tables, returns all fixed schema columns plus a 'dictionary' column containing BSON data.

        Parameters:
            records (np.ndarray): Records with bson_ptr/bson_size fields.

        Returns:
            list: List of dictionaries containing schema columns + BSON data.
        """
        if not self.table.is_schemaless:
            raise Exception('Table %s is not schemaless or has no records!' % (self.table.relpath))
        
        if loc is None:
            return []

        if isinstance(loc, slice):
            loc_arr = np.arange(self.count, dtype=np.int64)[loc]
        elif isinstance(loc, pd.Index):
            loc_arr = loc.to_numpy(dtype=np.int64, copy=False)
        else:
            loc_arr = np.array(loc, copy=False)

        is_structured = hasattr(loc_arr.dtype, 'names') and loc_arr.dtype.names == self.dtype.names
        if not is_structured:
            if loc_arr.dtype == bool:
                loc_arr = np.flatnonzero(loc_arr)
            loc_arr = np.atleast_1d(loc_arr)
            if loc_arr.size == 0:
                return []
            loc_arr = loc_arr.astype(np.int64, copy=False)
        else:
            loc_arr = np.atleast_1d(loc_arr)
            if loc_arr.size == 0:
                return []
        
        try:
            success = True
            if acquire:
                self.table.acquire()
        
            # check if the file has been modified externally
            need_remap = (self.next_bson_ptr < self.prev_bson_ptr)\
                  or (self.table.curr_bson_size < self.next_bson_ptr)
            if need_remap:
                self.table.init_bson_mmap()
            self.prev_bson_ptr = self.next_bson_ptr

            # Optimization 1: Efficient conversion of structured array to list of dicts
            records = loc_arr if is_structured else self[loc_arr]

            # Get column names and identify datetime and string columns once
            column_names = records.dtype.names
            datetime_cols = [name for name in column_names 
                            if np.issubdtype(records.dtype.fields[name][0], np.datetime64)]
            # string_cols = [name for name in column_names 
            #               if name in STRING_FIELDS]
            string_cols = [name for name in column_names 
                          if np.issubdtype(records.dtype.fields[name][0], np.bytes_)]
            
            # Fast bulk conversion using tolist() then fix datetime and string columns
            records_as_tuples = records.tolist()
            dict_list = [dict(zip(column_names, record_tuple)) for record_tuple in records_as_tuples]
            
            # Efficiently fix datetime columns only where needed
            if datetime_cols:
                for i, record_dict in enumerate(dict_list):
                    for col in datetime_cols:
                        value = record_dict[col]
                        if isinstance(value, (int, np.integer)):
                            record_dict[col] = pd.Timestamp(value, 'ns')
            
            # Decode string fields from bytes to str
            if string_cols:
                for record_dict in dict_list:
                    for col in string_cols:
                        value = record_dict.get(col)
                        if isinstance(value, bytes):
                            record_dict[col] = value.decode('utf-8').rstrip('\x00')
            
            # Optimization 2: Batch BSON loading for records with BSON data
            bson_indices = []
            bson_ptrs = []
            bson_sizes = []
            
            # Collect all BSON records that need loading
            for i, rec in enumerate(records):
                if (rec['bson_size'] > 0) and (rec['bson_ptr'] >= 0):
                    bson_indices.append(i)
                    bson_ptrs.append(rec['bson_ptr'])
                    bson_sizes.append(rec['bson_size'])
            
            # Batch load BSON data if any exists
            if bson_indices:
                bson_data_list = self._batch_load_bson(bson_ptrs, bson_sizes)
                
                # Update dictionaries with BSON data
                for idx, bson_data in zip(bson_indices, bson_data_list):
                    if bson_data:
                        dict_list[idx].update(bson_data)

            success = True
        except Exception as e:
            errmsg = 'Error decoding BSON for %s!\n%s' % (self.table.relpath, str(e))
            Logger.log.error(errmsg)
            success = False
        finally:
            if acquire:
                self.table.release()
            if not success:
                raise Exception('Error decoding BSON for %s!' % (self.table.relpath))
        
        return dict_list
    
    def _batch_load_bson(self, bson_ptrs, bson_sizes):
        """
        Efficiently batch load multiple BSON entries using memory-mapped I/O.
        
        Parameters:
            bson_ptrs (list): List of BSON file pointers
            bson_sizes (list): List of BSON data sizes
            
        Returns:
            list: List of decoded BSON dictionaries
        """
        if not bson_ptrs:
            return []
        
        # Initialize mmap if needed
        if self.table.bson_mmap is None:
            self.table.init_bson_mmap()
            
        # Sort by file position for sequential reads (better cache locality)
        sorted_indices = sorted(range(len(bson_ptrs)), key=lambda i: bson_ptrs[i])
        
        bson_data_list = [None] * len(bson_ptrs)
        
        # Sequential read using mmap (zero-copy)
        for idx in sorted_indices:
            ptr = bson_ptrs[idx]
            size = bson_sizes[idx]
            if size > 0 and ptr >= 0:
                bson_data_list[idx] = self.table.load_dictionary(ptr, size)
            else:
                bson_data_list[idx] = {}
        
        return bson_data_list
    
    # get date loc greater than or equal to startdate
    def get_date_loc_gte_lte(self, startdate, enddate, maxids=0):
        """
        Retrieve the indices of records within the specified date range [startdate, enddate].
        
        This method returns a NumPy array of record indexes where the record dates satisfy the condition:
        startdate <= date <= enddate. It uses a Just-In-Time (JIT) compiled function for fast execution.
        
        Parameters:
            startdate (pd.Timestamp or np.datetime64): The start date of the range (inclusive).
            enddate (pd.Timestamp or np.datetime64): The end date of the range (inclusive).
            maxids (int, optional): Maximum number of record indexes to return. Defaults to 0 (no limit).
        
        Returns:
            np.ndarray: Array of record indexes matching the date range criteria.
        
        Raises:
            Exception: If the underlying table does not have an index.
        """
        if self.table.hdr['hasindex'] != 1:
            raise Exception(f'Table {self.table.relpath} does not have index!')
        if isinstance(startdate, pd.Timestamp):
            startdate = np.datetime64(startdate, 'ns')
        if isinstance(enddate, pd.Timestamp):
            enddate = np.datetime64(enddate, 'ns')

        datelastidx = self.table.index.datelastidx
        dateprevidx = self.table.index.dateprevidx
        mindate = self.table.mindate
        periodns = self.table.periodns

        return get_date_loc_gte_lte_jit(startdate, enddate, datelastidx, dateprevidx, mindate, periodns, maxids)

    def get_symbol_loc(self, symbol, maxids=0):
        """
        Retrieve the location index of a given symbol within the table's indexed data.
        
        This method ensures that the table has an index, creates the index if it is not already created,
        and then searches for the symbol's location using a JIT-compiled helper function. The symbol can be
        provided as a string or bytes; if a string is given, it is encoded to UTF-8 bytes before searching.
        
        Parameters:
            symbol (str or bytes): The symbol to locate in the table.
            maxids (int, optional): A parameter to limit the search range or number of IDs considered. Defaults to 0.
        
        Returns:
            int: The location index of the symbol within the table.
        
        Raises:
            Exception: If the table does not have an index or if there is an error during the symbol location retrieval.
        """
        if self.table.hdr['hasindex'] != 1:
            raise Exception(f'Table {self.table.relpath} does not have index!')
        success = False
        try:
            self.table.acquire()
            # check if index is created & valid
            if self.table.hdr['isidxcreated'] == 0:
                self.index.create_index(self, self.pkey)

            if not isinstance(symbol, bytes):
                symbol = symbol.encode('utf-8')
            
            # Get fresh references to index arrays after potential create_index() call
            index = self.table.index
            symbollastidx = index.symbollastidx
            symbolprevidx = index.symbolprevidx
            
            _rec = np.full((1,),np.nan,dtype=self.dtype)
            _rec['symbol'] = symbol
            loc = get_symbol_loc_jit(self[:], symbollastidx,
                                 symbolprevidx, _rec, maxids)
            success = True
        except Exception as e:
            Logger.log.error('Error getting symbol_loc for %s!\n%s' %
                             (self.table.relpath, str(e)))
        finally:
            self.table.release()
            if not success:
                raise Exception('Error getting symbol_loc for %s!' %
                                (self.table.relpath))
        return loc

    def get_portfolio_loc(self, portfolio, maxids=0):
        """
        Retrieve the location(s) of a specified portfolio within the table using the index.
        
        Parameters:
            portfolio (str or bytes): The portfolio identifier to locate. If a string is provided, it will be encoded to bytes.
            maxids (int, optional): The maximum number of IDs to retrieve. Defaults to 0, which may indicate no limit.
        
        Returns:
            loc: The location(s) of the portfolio in the table as determined by the index.
        
        Raises:
            Exception: If the table does not have an index or if there is an error during the retrieval process.
        
        Notes:
            - Ensures the index is created and valid before performing the search.
            - Locks the table during the operation to prevent concurrent modifications.
            - Uses a JIT-compiled function for efficient location retrieval.
        """
        if self.table.hdr['hasindex'] != 1:
            raise Exception(f'Table {self.table.relpath} does not have index!')
        success = False
        try:
            self.table.acquire()
            # check if index is created & valid
            if self.table.hdr['isidxcreated'] == 0:
                self.index.create_index(self, self.pkey)

            if not isinstance(portfolio, bytes):
                portfolio = portfolio.encode('utf-8')
            
            # Get fresh references to index arrays after potential create_index() call
            index = self.table.index
            portlastidx = index.portlastidx
            portprevidx = index.portprevidx
            
            _rec = np.full((1,),np.nan,dtype=self.dtype)
            _rec['portfolio'] = portfolio
            loc = get_portfolio_loc_jit(
                self[:], portlastidx, portprevidx, _rec, maxids)
            success = True
        except Exception as e:
            Logger.log.error('Error getting portfolio_loc for %s!\n%s' %
                             (self.table.relpath, str(e)))
        finally:
            self.table.release()
            if not success:
                raise Exception('Error getting portfolio_loc for %s!' %
                                (self.table.relpath))
        return loc

    def get_tag_loc(self, tag, maxids=0):
        """
        Retrieve the location index of a specified tag within the table's indexed data.
        
        This method ensures the table has an index, creating one if it does not exist.
        It encodes the tag to bytes if necessary, constructs a record with the tag,
        and uses a JIT-compiled function to find the tag's location in the index.
        
        Parameters:
            tag (str or bytes): The tag to locate in the table index.
            maxids (int, optional): Maximum number of IDs to consider. Defaults to 0.
        
        Returns:
            int: The location index of the tag in the table.
        
        Raises:
            Exception: If the table does not have an index or if an error occurs during the lookup process.
        """
        if self.table.hdr['hasindex'] != 1:
            raise Exception(f'Table {self.table.relpath} does not have index!')
        success = False
        try:
            self.table.acquire()
            # check if index is created & valid
            if self.table.hdr['isidxcreated'] == 0:
                self.index.create_index(self, self.pkey)

            if not isinstance(tag, bytes):
                tag = tag.encode('utf-8')

            # Get fresh references to index arrays after potential create_index() call
            index = self.table.index
            portlastidx = index.portlastidx
            portprevidx = index.portprevidx

            _rec = np.full((1,),np.nan,dtype=self.dtype)
            _rec['tag'] = tag

            loc = get_tag_loc_jit(
                self[:], portlastidx, portprevidx, _rec, maxids)
            success = True
        except Exception as e:
            Logger.log.error('Error getting tag_loc for %s!\n%s' %
                             (self.table.relpath, str(e)))
        finally:
            self.table.release()
            if not success:
                raise Exception('Error getting tag_loc for %s!' %
                                (self.table.relpath))
        return loc

    ############################## CONVERSION ##############################
    @property
    def df(self):
        """
        Lazily loads and returns the DataFrame representation of the data.
        
        If the internal DataFrame (`self._df`) is not initialized or contains fewer rows than expected (`self.count`),
        this property reloads the DataFrame from the underlying data source using memory mapping for improved performance.
        The DataFrame is indexed according to the table's primary key columns.
        
        Returns:
            pandas.DataFrame: The DataFrame containing the complete data.
        """
        mmap_df = False
        if self._df is not None:
            if self._df.shape[0] < self.count:
                mmap_df = True
        else:
            mmap_df = True
            
        if mmap_df:
            indexcols = len(self.table.index.pkeycolumns)
            self._df = mmaparray2df(self[:], indexcols)            

        return self._df
                    
    def records2df(self, records):
        """
        Convert a list of records into a pandas DataFrame using the associated table's conversion method.
        
        Parameters:
            records (list): A list of records to be converted into a DataFrame.
        
        Returns:
            pandas.DataFrame: A DataFrame constructed from the provided records.
        """
        return self.table.records2df(records)

    def df2records(self, df, extra_data=None):
        """
        Convert a pandas DataFrame into a list of records using the table's df2records method.
        
        Parameters:
            df (pandas.DataFrame): The DataFrame to convert.
        
        Returns:
            list: A list of records obtained from the DataFrame.
        """
        return self.table.df2records(df, extra_data)

    def convert(self, new_records, extra_data=None):
        return self.table.convert(new_records, extra_data)

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
        return self.table.tags2df(dt, seltags, datetags)

    def any2records(self, new_records):
        """
        Convert various data formats into a list of records compatible with the table's schema.
        
        This method accepts input data in multiple formats, including pandas DataFrames, dictionaries,
        lists of dictionaries, NumPy structured arrays, and single dictionaries. It processes the input
        accordingly and converts it into a list of records that match the table's schema.
        
        Parameters:
            any_data (pd.DataFrame, dict, list of dicts, np.ndarray): The input data to convert.
            extra_data (list, optional): If provided, columns not in `self.dtype` will be added to this list
                                         as dictionaries (one per row).
        """
        return self.table.any2records(new_records)

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
        return self.table.remove_invalid_records(new_records, dict_list)

    ############################## GETTERS / SETTERS ##############################    

    def __getitem__(self, key):
        """
        Retrieve item(s) from the object using the given key.
        
        If the object has a 'table' attribute and its size is less than 'recordssize',
        it remaps itself by calling 'rememmap()'. Then, it obtains a sliced array of
        elements up to 'count' using the superclass's __getitem__ method. If 'count'
        is greater than zero, it returns the item(s) at the specified key from this
        sliced array; otherwise, it returns the entire sliced array.
        
        If the object does not have a 'table' attribute, it directly returns the item(s)
        from the superclass's __getitem__ method using the provided key.
        
        Parameters:
            key (int, slice, or other): The index or slice to retrieve from the object.
        
        Returns:
            The item(s) corresponding to the key from the internal data structure.
        """
        if hasattr(self, 'table'):
            if self.table.size < self.recordssize:
                self = self.rememmap()

            arr = super().__getitem__(slice(0, self.count))  # slice arr
            if self.count > 0:
                return arr.__getitem__(key)
            else:
                return arr
        else:
            return super().__getitem__(key)
    
    def get_exists_remote(self):
        """
        Proxy method to check the existence of a remote resource.
        
        Delegates the call to the `get_exists_remote` method of the `table` attribute.
        
        Returns:
            The result of `self.table.get_exists_remote()`, indicating whether the remote resource exists.
        """
        return self.table.get_exists_remote()

    @property
    def records(self):
        """
        Return a slice of the underlying data from the beginning up to the current size.
        
        This property accesses the superclass's __getitem__ method with a slice from index 0 to self.size,
        effectively retrieving the first `size` elements of the data.
        
        Returns:
            A sequence containing elements from index 0 up to (but not including) self.size.
        """
        return super().__getitem__(slice(0, self.size))

    @property
    def count(self):
        return self.table.hdr['count']

    @count.setter
    def count(self, value):
        """
        Setter for the 'count' property. Updates the 'count' key in the 'hdr' dictionary of the 'table' attribute with the given value.
        """
        self.table.hdr['count'] = value

    @property
    def recordssize(self):
        return self.table.hdr['recordssize']

    @recordssize.setter
    def recordssize(self, value):
        """
        Set the 'recordssize' field in the table header to the specified value.
        
        Parameters:
            value (int): The new size to assign to the 'recordssize' field in the header.
        """
        self.table.hdr['recordssize'] = value

    @property
    def mtime(self):
        return self.table.hdr['mtime']

    @mtime.setter
    def mtime(self, value):
        """
        Set the modification time in the table header.
        
        Parameters:
            value (int or float): The new modification time to be set.
        """
        self.table.hdr['mtime'] = value

    @property
    def minchgid(self):
        return self.table.hdr['minchgid']

    @minchgid.setter
    def minchgid(self, value):
        """
        Set the 'minchgid' header to the smaller of the current 'minchgid' value and the provided value.
        
        Parameters:
            value (int): The new candidate minimum change ID.
        
        This setter prevents the 'minchgid' header from increasing by always choosing the minimum between the existing header value and the new value.
        """
        value = min(value, self.table.hdr['minchgid'])
        self.table.hdr['minchgid'] = value

    @property
    def index(self):
        return self.table.index

    @index.setter
    def index(self, value):
        """
        Set the index of the internal table to the specified value.
        
        Parameters:
            value: The new index to be assigned to the table.
        """
        self.table.index = value

    @property
    def pkey(self):
        return self.table.index.pkey

    @pkey.setter
    def pkey(self, value):
        """
        Set the primary key of the table's index.
        
        Parameters:
            value: The new primary key to be assigned to the table's index.
        """
        self.table.index.pkey = value

    @property
    def is_schemaless(self):
        return self.table.is_schemaless
    
    @is_schemaless.setter
    def is_schemaless(self, value):
        """
        Set the 'is_schemaless' attribute of the table.
        
        Parameters:
            value (bool): The new value to assign to the 'is_schemaless' attribute.
        """
        self.table.is_schemaless = value
    
    @property
    def hasindex(self):
        return self.table.hasindex
    
    @hasindex.setter
    def hasindex(self, value):
        """
        Set the 'hasindex' attribute of the table.
        
        Parameters:
            value (bool): The new value to assign to the 'hasindex' attribute.
        """
        self.table.hasindex = value

    @property
    def next_bson_ptr(self):
        return self.table.hdr['next_bson_ptr']

    @next_bson_ptr.setter
    def next_bson_ptr(self, value):
        self.table.hdr['next_bson_ptr'] = value
    
    @property
    def prev_bson_ptr(self):
        return self.table.prev_bson_ptr

    @prev_bson_ptr.setter
    def prev_bson_ptr(self, value):
        self.table.prev_bson_ptr = value

class _LocIndexer:
    """
    .loc indexer for SharedNumpy data structures, enabling advanced row- and column-wise selection.
    
    Supports selection by primary and secondary keys such as 'symbol', 'tag', and 'portfolio', including:
    - Access by string keys to filter rows matching the key.
    - Multi-key tuple indexing with support for date ranges, slices, and lists/arrays of string keys.
    - Column selection via single column names or lists of columns.
    - Handling of MultiIndex row selections.
    - Read-only enforcement on assignment attempts.
    
    This indexer is designed to work with tables that have a multi-level index with primary key columns,
    including special handling when the first primary key is a date.
    
    Raises:
        Exception: If an attempt is made to assign values via .loc (readonly).
    
    Returns:
        Subsets of the underlying data array or numpy arrays depending on the indexing operation.
    """
    def __init__(self, data):
        """
        Initializes the instance with the provided data.
        
        Parameters:
            data: The data to be stored in the instance.
        """
        self.data = data

    def __setitem__(self, key, value):
        """
        Prevent setting an item in the object, enforcing read-only behavior.
        
        This method intercepts attempts to assign a value to an item using subscript notation (e.g., obj[key] = value),
        logs an error message, and raises an Exception to indicate that the object does not support item assignment.
        
        Parameters:
            key: The key or index where the assignment was attempted.
            value: The value that was attempted to be assigned.
        
        Raises:
            Exception: Always raised to signal that the object is read-only and does not allow item assignment.
        """
        errmsg = "Error: loc is readonly!"
        Logger.log.error(errmsg)
        raise Exception(errmsg)

    def __getitem__(self, index):
         # --- Multi-secondary-key support  ---
        """
        '''
        Retrieve data from the dataset using flexible and complex indexing.
        
        Supports indexing by integers, slices, strings, tuples, pandas Timestamps, numpy datetime64, and MultiIndex objects,
        with special handling for multi-secondary keys such as 'symbol', 'tag', and 'portfolio'. Enables advanced filtering
        and selection based on primary key columns, including date ranges and multi-key tuples.
        
        Parameters:
            index (int, slice, str, tuple, pd.Timestamp, np.datetime64, or pd.MultiIndex): The index or key used to select data.
                - int or slice: Select rows by position.
                - str: Select rows by secondary key (e.g., 'symbol', 'tag', 'portfolio').
                - tuple: Combine row and column selectors, supporting multi-key indexing.
                - pd.Timestamp or np.datetime64: Select rows by date.
                - pd.MultiIndex: Advanced multi-level indexing.
        
        Returns:
            numpy.ndarray or structured array subset corresponding to the requested index. Returns an empty array if no matches found.
        
        Raises:
            IndexError: If a requested key is not found in certain indexing scenarios.
        
        Behavior:
            - Optimizes access for tuples containing secondary keys.
            - Maps string keys to appropriate secondary index lookup methods.
            - Applies date filtering when '
        """
        # Capture count at start - this is our safe upper bound for all index operations
        initial_count = self.data.count
        schemaless = self.data.is_schemaless

        pkeycolumns = getattr(self.data.table.index, "pkeycolumns", [])

        # Fast path for index = (row, col) tuple and [:, [sec_key,...]]
        if isinstance(index, tuple):
            row_index, col_index = self._parse_index(index)
            if (
                isinstance(row_index, (type(None), slice))
                and isinstance(col_index, (list, np.ndarray, pd.Index))
                and len(pkeycolumns) >= 2
                and pkeycolumns[1] in {'symbol', 'tag', 'portfolio'}
            ):
                idx_type = pkeycolumns[1]
                get_func = {
                    'symbol': self.data.get_symbol_loc,
                    'tag': self.data.get_tag_loc,
                    'portfolio': self.data.get_portfolio_loc
                }[idx_type]
                locs = np.concatenate([
                    get_func(val) for val in col_index
                ]) if len(col_index) else np.array([], dtype=int)
                locs = np.unique(locs)
                # Filter out indices >= initial_count
                locs = locs[locs < initial_count]
                
                if 'date' in pkeycolumns:
                    # If date is the first primary key, sort by date
                    locs = np.array(locs, dtype=int)
                    locs = locs[np.argsort(self.data[locs]['date'])]
                    if isinstance(row_index, slice):
                        start = row_index.start
                        stop = row_index.stop
                        if start is None:
                            start = self.data.table.mindate
                        if stop is None:
                            stop = self.data.table.maxdate
                        locidx = (self.data[locs]['date'] >= start) & (self.data[locs]['date'] <= stop)
                        locs = locs[locidx]

                if schemaless:
                    return self.data.get_dict_list(locs)
                return self.data[locs] if len(locs) else np.array([], dtype=self.data.dtype)

        # Secondary-key-only (e.g. tbl.loc["AAPL"])
        if isinstance(index, str):
            if pkeycolumns:
                if pkeycolumns == ["symbol"]:
                    buffer = np.full((1,), dtype=self.data.dtype, fill_value=np.nan)
                    buffer['symbol'] = index
                    locs = self.data.get_loc(buffer)
                    # Filter indices - ensure locs is array first
                    if not isinstance(locs, np.ndarray):
                        locs = np.array(locs, dtype=int)
                    locs = locs[locs < initial_count]
                    if locs.size and locs[0] != -1:
                        if schemaless:
                            return self.data.get_dict_list([locs[0]])
                        return self.data[locs[0]]
                    return [] if schemaless else np.array([], dtype=self.data.dtype)
                
                primary_string_keys = [k for k in pkeycolumns if k in STRING_FIELDS]
                if primary_string_keys:
                    key = primary_string_keys[0]
                    method = {
                        'symbol': self.data.get_symbol_loc,
                        'tag': self.data.get_tag_loc,
                        'portfolio': self.data.get_portfolio_loc,
                    }.get(key)
                    if method is not None:
                        key_locs = method(index)
                        key_locs = np.array(key_locs, dtype=int)
                        # Filter indices
                        key_locs = key_locs[key_locs < initial_count]
                        
                        if schemaless:
                            return self.data.get_dict_list(key_locs)

                        if pkeycolumns[0] == "date":
                            # restrict to mindate... for date-ordered                            
                            key_locs = key_locs[np.argsort(self.data[key_locs]['date'])]
                            return self.data[key_locs] if len(key_locs) else np.array([], dtype=self.data.dtype)
                        else:
                            # secondary-only
                            return self.data[key_locs] if len(key_locs) else np.array([], dtype=self.data.dtype)

        # Fully general multi-key/pkey access (including date, symbol, ... multi-columns)
        if (
            isinstance(index, tuple)
            and (1 <= len(index) <= len(pkeycolumns) + 1)
            and any(pkey == "date" for pkey in pkeycolumns)
        ):
            row_keys = index[:len(pkeycolumns)]
            col_selector = index[len(pkeycolumns):]
            col_selector = col_selector[0] if col_selector else None

            # Build a filter list - always use get_date_loc* for date!
            sort_by_date = False
            row_locs_list = []
            for val, pkey in zip(row_keys, pkeycolumns):
                if pkey == "date":
                    # --- Use date indexers for date portions ---
                    if isinstance(val, slice):
                        start = val.start
                        stop = val.stop
                        if not start and not stop:
                            sort_by_date = True
                            continue  # Empty slice, skip
                        else:
                            start = (np.datetime64(pd.Timestamp(start), 'ns') if start is not None 
                                    else self.data.table.mindate)
                            stop = (np.datetime64(pd.Timestamp(stop), 'ns') if stop is not None 
                                    else self.data.table.maxdate)
                            locs = self.data.get_date_loc_gte_lte(start, stop)
                    elif isinstance(val, (pd.Timestamp, np.datetime64, str)):
                        dt = pd.Timestamp(val) if isinstance(val, str) else val
                        dt = np.datetime64(dt, 'ns')
                        locs = self.data.get_date_loc(dt)
                    elif val is None:
                        locs = np.arange(initial_count)
                    else:
                        locs = np.array([], dtype=int)
                    # Filter indices - ensure locs is array first
                    if not isinstance(locs, np.ndarray):
                        locs = np.array(locs, dtype=int)
                    locs = locs[locs < initial_count]
                    row_locs_list.append(locs)
                elif pkey in STRING_FIELDS:
                    # --- Use existing secondary key indexers ---
                    if isinstance(val, (list, tuple, np.ndarray, pd.Index)):
                        arr = np.concatenate([
                            getattr(self.data, f"get_{pkey}_loc")(v) for v in val
                        ]) if len(val) else np.array([], dtype=int)
                        arr = np.unique(arr)
                        # Filter indices
                        arr = arr[arr < initial_count]
                        row_locs_list.append(arr)
                    elif isinstance(val, (str, bytes)):
                        arr = getattr(self.data, f"get_{pkey}_loc")(val)
                        # Filter indices
                        arr = np.array(arr, dtype=int)
                        arr = arr[arr < initial_count]
                        row_locs_list.append(arr)
                    elif val is None:
                        continue
                    else:
                        continue
                else:
                    # For classic non-string non-date fields, fall back to boolean masking (rare)
                    # This can be optimized only if you add an integer-index.
                    # For now, do standard comparison on all records:
                    records = self.data[:initial_count]  # Use initial_count here
                    if val is not None:
                        mask = (records[pkey] == val)
                        arr = np.flatnonzero(mask)
                        row_locs_list.append(arr)
                        
            # Intersect all location arrays, preserving order by the first.
            if row_locs_list:
                result_locs = row_locs_list[0]
                for other in row_locs_list[1:]:
                    result_locs = np.intersect1d(result_locs, other, assume_unique=True)
            else:
                result_locs = np.arange(initial_count)                

            if sort_by_date and len(result_locs) > 0:
                # If we are sorting by date, we need to sort the result_locs by the date column
                result_locs = np.array(result_locs, dtype=int)
                result_locs = result_locs[np.argsort(self.data[result_locs]['date'])]

            if schemaless:
                return self.data.get_dict_list(result_locs)

            selected = self.data[result_locs]            
            # Robust column selection: list/tuple/Index or single column
            if col_selector is not None:
                if isinstance(col_selector, (list, tuple, pd.Index)):
                    return selected[list(col_selector)]
                else:
                    return selected[col_selector]
            else:
                return selected
                

        # MultiIndex rows
        row_index, col_index = self._parse_index(index)
        if isinstance(row_index, pd.MultiIndex):
            return self._multiindex_locs(row_index, col_index, initial_count)

        # Tuple as (slice/Timestamp/int, key)
        if isinstance(row_index, tuple):
            row_part, key_part = row_index
            if isinstance(row_part, slice) and isinstance(key_part, str):
                start, stop, step = self._slice_to_bounds(row_part, initial_count)
                locs = self._secondary_index_locs(row_key=key_part)
                # Filter indices
                locs = locs[locs < initial_count]
                if locs.size:
                    result = locs[(locs >= start) & (locs < stop)]
                    if schemaless:
                        return self.data.get_dict_list(result)
                    return self.data[result]
                else:
                    return [] if schemaless else np.array([], dtype=self.data.dtype)
            elif row_part is None:
                if schemaless:
                    return self.data.get_dict_list(np.arange(initial_count))
                return self.data[:initial_count][..., col_index]
            else:
                raise NotImplementedError("Tuple with this signature in .loc not handled.")

        # Integer row index
        if isinstance(row_index, int):
            if row_index >= initial_count:
                raise IndexError(f"Index {row_index} out of bounds for size {initial_count}")
            if isinstance(col_index, str) and col_index not in self.data.dtype.names:
                locs = self._secondary_index_locs(row_key=col_index)
                # Filter indices
                locs = locs[locs < initial_count]
                if locs.size:
                    idx = row_index % len(locs)
                    if schemaless:
                        return self.data.get_dict_list([locs[idx]])
                    return self.data[locs[idx]]
                else:
                    raise IndexError(f"No entry for key '{col_index}'")
            if schemaless:
                return self.data.get_dict_list([row_index])
            return self.data[row_index][col_index]

        # Timestamp row index (date lookup)
        if isinstance(row_index, pd.Timestamp) or np.issubdtype(type(row_index), np.datetime64):
            row_index = np.datetime64(row_index, 'ns')
            locs = self.data.get_date_loc(row_index)
            if not isinstance(locs, np.ndarray):
                locs = np.array(locs)
            # Filter indices
            locs = locs[locs < initial_count]
            
            if isinstance(col_index, str) and col_index not in self.data.dtype.names:
                key_locs = self._secondary_index_locs(row_key=col_index)
                # Filter indices
                key_locs = key_locs[key_locs < initial_count]
                if key_locs.size and locs.size:
                    result = np.intersect1d(locs, key_locs, assume_unique=True)
                    if schemaless:
                        return self.data.get_dict_list(result)
                    return self.data[result]
                return [] if schemaless else np.array([], dtype=self.data.dtype)
            if isinstance(col_index, pd.Index):
                idxname = self.data.table.index.pkeycolumns[1]
                all_locs = []
                for key in col_index:
                    sec_locs = self._secondary_index_locs(row_key=key)
                    # Filter indices
                    sec_locs = sec_locs[sec_locs < initial_count]
                    all_locs.extend(np.intersect1d(locs, sec_locs, assume_unique=True))
                if schemaless:
                    return self.data.get_dict_list(np.sort(np.unique(all_locs)))
                return self.data[np.sort(np.unique(all_locs))]
            if schemaless:
                return self.data.get_dict_list(locs)
            return self.data[locs][col_index] if locs.size else np.array([], dtype=self.data.dtype)

        # Fallback - apply initial_count bound
        if isinstance(row_index, (int, slice)):
            if isinstance(row_index, int) and row_index >= initial_count:
                raise IndexError(f"Index {row_index} out of bounds for size {initial_count}")
            if schemaless:
                locs = np.arange(initial_count)[row_index] if isinstance(row_index, slice) else [row_index]
                return self.data.get_dict_list(locs)
            return self.data[:initial_count][row_index][col_index]
        
        if schemaless:
            return self.data.get_dict_list(row_index)
        return self.data[row_index][col_index]

    def _parse_index(self, index):
        """
        Parses the given index used in .loc[] calls and returns a tuple of (row_index, col_index).
        
        Supports various index types including tuples, MultiIndex, slices, and strings, and assigns default
        values for missing row or column indices to ensure consistent tuple output.
        
        Parameters:
            index: The index provided in a .loc[] call. It can be a tuple, MultiIndex, slice, string, or other types.
        
        Returns:
            tuple: A tuple (row_index, col_index) where each element is an index, slice, or None, representing
                   the row and column indices respectively.
        """
        if isinstance(index, tuple):
            if len(index) == 2:
                return index
            elif len(index) == 1:
                return index[0], slice(None)
        elif isinstance(index, pd.MultiIndex):
            return index, slice(None)
        elif isinstance(index, slice):
            return index, slice(None)
        elif isinstance(index, str):
            return None, index
        return index, slice(None)

    def _slice_to_bounds(self, s: slice, initial_count: int):
        """
        Convert a slice object with possible timestamp bounds into integer index bounds.
        
        Parameters:
            s (slice): A slice object where start and stop can be integers, None, or pd.Timestamp.
            initial_count (int): The count captured at the start of indexing operation.
        
        Returns:
            tuple: A tuple (start, stop, step) where start and stop are integer indices corresponding
                   to the slice bounds, and step is the slice step (defaulting to 1 if not specified).
        
        Notes:
            - If start or stop is None, they default to 0 and initial_count, respectively.
            - If start or stop is a pd.Timestamp, it is converted to the corresponding integer index
              using the data's date location method.
        """
        def bound(val, fallback):
            """
            Returns a bounded value based on the input `val`. If `val` is `None`, returns the provided `fallback`.
            If `val` is a `pandas.Timestamp`, attempts to locate its position in `self.data` using `get_date_loc` and returns the first matching index if found; otherwise, returns `fallback`.
            For all other types, returns `val` unchanged.
            """
            if val is None:
                return fallback
            if isinstance(val, pd.Timestamp):
                arr = self.data.get_date_loc(np.datetime64(val, 'ns'))
                arr = arr[arr < initial_count]  # Filter here too
                return arr[0] if len(arr) > 0 else fallback
            return val
        start = bound(s.start, 0)
        stop = bound(s.stop, initial_count)
        step = s.step if s.step is not None else 1
        return start, stop, step

    def _secondary_index_locs(self, row_key: str):
        """
        Retrieve the indices corresponding to a secondary key type (symbol, tag, or portfolio) for a given row key.
        
        This method determines the secondary key type based on the table's primary key columns and uses the appropriate
        lookup function to find the indices associated with the provided row key. If the secondary key type is not recognized
        or there are fewer than two primary key columns, it returns an empty integer array.
        
        Parameters:
            row_key (str): The key value to look up in the secondary index.
        
        Returns:
            np.ndarray: An array of integer indices corresponding to the row_key for the secondary key type.
            Returns an empty array if the secondary key type is not supported or not present.
        """
        pkeycolumns = getattr(self.data.table.index, 'pkeycolumns', [])
        if len(pkeycolumns) < 2:
            return np.array([], dtype=int)
        idx_type = pkeycolumns[1]
        get_func = {
            'symbol': self.data.get_symbol_loc,
            'tag': self.data.get_tag_loc,
            'portfolio': self.data.get_portfolio_loc,
        }.get(idx_type)
        if get_func is None:
            return np.array([], dtype=int)
        out = get_func(row_key)
        if not isinstance(out, np.ndarray):
            out = np.array(out, dtype=int)
        return out

    def _multiindex_locs(self, row_index: pd.MultiIndex, col_index, initial_count: int):
        """
        Retrieve data locations for specified MultiIndex rows and column index.
        
        Parameters:
            row_index (pd.MultiIndex): MultiIndex object specifying the rows to locate.
            col_index: Column index or label(s) to select from the located rows.
            initial_count (int): The count captured at the start of indexing operation.
        
        Returns:
            Selected data corresponding to the provided MultiIndex rows and column index.
        
        This method converts the MultiIndex rows into a structured numpy array with appropriate dtypes,
        finds their locations within the underlying data, filters out invalid locations, and returns
        the data at those locations for the specified columns.
        """
        dtype = np.dtype([(x, row_index.get_level_values(x).dtype) for x in row_index.names])
        record_keys = np.array([tuple(x) for x in row_index.values], dtype=dtype)
        record_keys = self.data.convert(record_keys)
        locs = self.data.get_loc(record_keys)
        locs = np.array(locs)
        locs = locs[(locs >= 0) & (locs < initial_count)]  # Filter with initial_count
        if self.data.is_schemaless:
            locs = np.atleast_1d(locs.astype(np.int64, copy=False))
            if locs.size == 0:
                return []
            return self.data.get_dict_list(locs)
        return self.data[locs][col_index]
