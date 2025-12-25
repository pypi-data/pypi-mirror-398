import pandas as pd
import numpy as np
import os
import time
from multiprocessing import shared_memory


import SharedData.TableIndexJitFunctions as TableIndexJitFunctions
from SharedData.TableIndexJitFunctions import *

from SharedData.Logger import Logger
from SharedData.Database import DATABASE_PKEYS

class TableIndex:        

    """
    Manages and maintains various indices for a table to enable efficient data access and manipulation.
    
    This class handles the creation, initialization, memory allocation, updating, sorting, and flushing of indices based on the table's primary key columns. It supports indexing by primary key, date, symbol, portfolio, and tag fields, depending on the table's schema and database type.
    
    Key functionalities include:
    - Initializing index structures and shared memory or memory-mapped files for persistent storage.
    - Creating and updating indices to reflect the current state of the table's records.
    - Sorting records based on primary key columns and updating indices accordingly.
    - Managing memory allocation for different index components (primary key, date, symbol, portfolio).
    - Flushing changes to disk and freeing allocated resources.
    - Dynamically loading JIT-compiled functions for index operations based on the database schema.
    
    Attributes:
        table: The table object for which the index is managed.
        shareddata: Shared memory manager associated with the table.
        initialized: Boolean flag indicating if the index has been successfully initialized.
        pkeycolumns: List of primary key column names for the table's database.
        pkeystr: Concatenated string of primary key columns used to identify index functions.
        pkey: Numpy array holding the
    """
    def __init__(self, table):
        """
        Initialize the indexer with the given table, setting up primary key, date, symbol, and portfolio indices.
        
        Parameters:
            table (Table): The table object containing data and metadata to be indexed.
        
        Attributes initialized:
            table (Table): The input table.
            shareddata: Shared data reference from the table.
            initialized (bool): Flag indicating if the indexer has been initialized.
            pkeycolumns (list): List of primary key column names from the table's database.
            pkeystr (str): Concatenated string of primary key columns separated by underscores.
            pkey (np.ndarray): Numpy array to store primary key hashes.
            periodns: Period namespace or related period information from the table.
            datelastidx (np.ndarray): Numpy array for storing last date indices.
            dateprevidx (np.ndarray): Numpy array for storing previous date indices.
            symbollastidx (np.ndarray): Numpy array for storing last symbol indices.
            symbolprevidx (np.ndarray): Numpy array for storing previous symbol indices.
            portlastidx (np.ndarray): Numpy array for storing last portfolio indices.
            portprevidx (np.ndarray): Numpy array for storing previous portfolio indices.
        """
        self.table = table
        self.shareddata = self.table.shareddata

        self.initialized = False

        # primary key hash table
        self.pkeycolumns = TableIndex.get_pkeycolumns(self.table.database)
        self.pkeystr = '_'.join(self.pkeycolumns)
        self.pkey = np.ndarray([],dtype=np.int64)

        # date index
        self.periodns = self.table.periodns
        self.datelastidx = np.ndarray([],dtype=np.int64)
        self.dateprevidx = np.ndarray([],dtype=np.int64)        

        # symbol index        
        self.symbollastidx = np.ndarray([],dtype=np.int64)
        self.symbolprevidx = np.ndarray([],dtype=np.int64)

        # portfolio index
        self.portlastidx = np.ndarray([],dtype=np.int64)
        self.portprevidx = np.ndarray([],dtype=np.int64)

    def initialize(self):
        """
        Initializes the index for the associated table.
        
        This method performs the following steps:
        - Retrieves necessary functions via `get_functions()`.
        - Allocates required resources using `malloc()`.
        - Checks if the index has already been created; if not, it creates the index and updates the table header accordingly.
        - If the table type is 1, it flushes the shared header and the current state.
        - Marks the table as having an index and sets the `initialized` flag to True.
        
        If any step fails, it logs an error message and raises an exception indicating the failure to initialize the index.
        """
        errmsg = ''
        try:

            self.get_functions()

            self.malloc()

            # check if index was created            
            if self.table.hdr['isidxcreated'] == 0:
                self.create_index()
                self.table.hdr['isidxcreated'] = 1
                if self.table.type==1:
                    self.table.shf_hdr.flush()
                    self.flush()
            
            self.table.hdr['hasindex'] = 1
            self.initialized = True
        except Exception as e:
            errmsg = 'Failed to intialize index for %s!\n%s' % (self.table.relpath, str(e))            
            self.initialized = False
        finally:            
            if not self.initialized:
                Logger.log.error(errmsg)
                raise Exception(errmsg)

    def get_functions(self):
        # primary key & index functions
        """
        Initializes and assigns primary key and index-related functions based on the current primary key string.
        
        This method dynamically constructs function names for creating primary keys, upserting records,
        and retrieving record locations by appending the primary key string to predefined prefixes.
        It then attempts to retrieve these functions from the TableIndexJit class and assigns them to
        instance variables. If any of the required functions are not found, it raises an exception
        indicating the missing function for the associated database.
        
        Raises:
            Exception: If any of the required functions (create_pkey, upsert, get_loc) are not found
                       for the current database.
        """
        self.create_index_func = None
        self.upsert_func = None
        self.get_loc_func = None

        create_pkey_fname = 'create_pkey_' + self.pkeystr + '_jit'
        if hasattr(TableIndexJitFunctions, create_pkey_fname):
            self.create_index_func = getattr(TableIndexJitFunctions, create_pkey_fname)
        else:
            raise Exception('create_pkey function not found for database %s!'
                            % (self.table.database))

        upsert_fname = 'upsert_' + self.pkeystr + '_jit'
        if hasattr(TableIndexJitFunctions, upsert_fname):
            self.upsert_func = getattr(TableIndexJitFunctions, upsert_fname)
        else:
            raise Exception('upsert function not found for database %s!'
                            % (self.table.database))

        get_loc_fname = 'get_loc_' + self.pkeystr + '_jit'
        if hasattr(TableIndexJitFunctions, get_loc_fname):
            self.get_loc_func = getattr(TableIndexJitFunctions, get_loc_fname)
        else:
            raise Exception('get_loc function not found for database %s!'
                            % (self.table.database))        

    def malloc(self):
        """
        Allocates shared memory and initializes index structures based on the primary key configuration.
        
        This method uses the shared memory name from the associated table to allocate memory for the primary key.
        It conditionally allocates additional indices depending on the presence of specific keywords in the primary key string:
        - Allocates a date index if 'date' is included.
        - Allocates a symbol index if 'symbol' is included and there is more than one primary key column.
        - Allocates a portfolio index if either 'portfolio' or 'tag' is included.
        """
        shm_name = self.table.shm_name
        self.malloc_pkey(shm_name)
        if 'date' in self.pkeystr:
            self.malloc_dateidx(shm_name)
        if ('symbol' in self.pkeystr) & (len(self.pkeycolumns) > 1):
            self.malloc_symbolidx(shm_name)
        if ('portfolio' in self.pkeystr) | ('tag' in self.pkeystr):
            self.malloc_portfolioidx(shm_name)        

    def malloc_pkey(self, shm_name):
        # TODO: bug when records.size is 0
        """
        Allocate or map a primary key array for the table, using shared memory or a memory-mapped file depending on the table type.
        
        Parameters:
            shm_name (str): The base name for the shared memory segment.
        
        Behavior:
        - Calculates the size of the primary key array based on the number of records.
        - For tables of type 2, attempts to allocate or attach to a shared memory segment named '{shm_name}#pkey'.
          If the segment does not exist, it creates one and marks the index as not created.
        - For tables of type 1, uses a memory-mapped file named by replacing 'data.bin' with 'pkey.bin' in the table's filepath.
          If the file does not exist or its size is incorrect, it creates or resets the file and marks the index as not created.
        - Initializes the primary key array as a numpy ndarray or memmap of int64.
        - If the index is marked as not created, initializes all primary key values to -1.
        
        Note:
        - There is a known bug when the number of records is zero.
        """
        keysize = int(self.table.records.size*3)
        keysize_bytes = int(keysize * 8)
                
        if self.table.type==2:
            [self.pkeyshm, ismalloc] = self.shareddata.malloc(shm_name+'#pkey')
            if not ismalloc:
                [self.pkeyshm, ismalloc] = self.shareddata.malloc(shm_name+'#pkey',
                    create=True, size=keysize_bytes)
                self.table.hdr['isidxcreated'] = 0
            self.pkey = np.ndarray((keysize,), dtype=np.int64,
                               buffer=self.pkeyshm.buf)
        elif self.table.type==1:
            self.pkeypath = str(self.table.filepath)\
                .replace('data.bin', 'pkey.bin')
            
            resetfile = False
            if (not os.path.exists(self.pkeypath)):
                resetfile = True
            elif os.path.getsize(self.pkeypath) != keysize_bytes:
                resetfile = True            

            if resetfile:
                self.create_file(self.pkeypath,keysize_bytes)
                self.table.hdr['isidxcreated'] = 0
                        
            self.pkey = np.memmap(self.pkeypath, np.int64, 'r+', 0, (keysize,))

        if self.table.hdr['isidxcreated'] == 0:
            self.pkey[:] = -1

    def malloc_dateidx(self, shm_name):
        # date index
        """
        Allocate and initialize memory-mapped date index arrays for the table based on shared memory name.
        
        This method calculates the size of the date index and associated lists based on the table's date range and period,
        then creates or resets a memory-mapped file to store these indices. It supports only tables with nanosecond precision dates.
        For table type 1, it manages a date index file, creating or resizing it as needed, and initializes the index arrays.
        Raises an exception if the date precision is not nanoseconds or if the table type is not implemented.
        
        Parameters:
            shm_name (str): The name of the shared memory segment (currently unused in the method).
        
        Raises:
            Exception: If date precision is not nanoseconds or if the table type is not supported.
        """
        dtunit = str(self.table.records.dtype[0]).split('[')[-1].split(']')[0]
        if dtunit != 'ns':
            raise Exception('Only dates with ns precision are supported!')
        
        mindate = self.table.mindate.astype(np.int64)
        maxdate = self.table.maxdate.astype(np.int64)

        dateidxsize = (maxdate-mindate) // self.periodns
        hashtblsize_bytes = int(dateidxsize * 8)
        listsize = self.table.records.size
        listsize_bytes = int(listsize * 8)
        size_bytes = int(hashtblsize_bytes+listsize_bytes)

        if self.table.type==2:
            #TODO
            raise Exception('Not implemented yet!')
        elif self.table.type==1:
            self.dateidxpath = str(self.table.filepath).replace('data.bin', 'dateidx.bin')
            
            resetfile = False
            if (not os.path.exists(self.dateidxpath)):
                resetfile = True                
            elif os.path.getsize(self.dateidxpath) != size_bytes:
                resetfile = True

            if resetfile:
                self.create_file(self.dateidxpath,size_bytes)
                self.table.hdr['isidxcreated'] = 0
            
            self.datelastidx = np.memmap(self.dateidxpath, np.int64, 'r+', 0, (dateidxsize,))
            self.dateprevidx = np.memmap(self.dateidxpath, np.int64, 'r+', hashtblsize_bytes, (listsize,))
            
        if self.table.hdr['isidxcreated'] == 0:
            self.datelastidx[:] = -1
            self.dateprevidx[:] = -1

    def malloc_symbolidx(self, shm_name):
        """
        Allocate and initialize symbol index structures in shared memory or a memory-mapped file based on the table type.
        
        For table type 2, this method allocates shared memory segments for symbol indices with sizes derived from the number of records. If the shared memory segment does not exist, it creates a new one and marks the index as not created.
        
        For table type 1, it manages a memory-mapped file for symbol indices. If the file does not exist or its size is incorrect, it creates or resets the file and marks the index as not created.
        
        The method initializes two numpy arrays, `symbollastidx` and `symbolprevidx`, which represent hash table and linked list indices respectively. If the index is newly created or reset, all entries in these arrays are initialized to -1.
        
        Parameters:
            shm_name (str): Base name for the shared memory segment or file used for symbol indices.
        
        Side Effects:
            - Creates or resets shared memory segments or memory-mapped files.
            - Updates `self.table.hdr['isidxcreated']` flag to indicate index creation status.
            - Initializes `self.symbollastidx` and `self.symbolprevidx` numpy arrays for symbol indexing.
        """
        hashtblsize = int(self.table.records.size*3)
        hashtblsize_bytes = int(hashtblsize * 8)
        listsize = self.table.records.size
        listsize_bytes = int(listsize * 8)
        size_bytes = int(hashtblsize_bytes+listsize_bytes)

        # symbol index
        
        if self.table.type==2:
            [self.symbolidxshm, ismalloc] = self.shareddata.malloc(
                shm_name+'#symbolidx')
            if not ismalloc:
                [self.symbolidxshm, ismalloc] = self.shareddata.malloc(shm_name+'#symbolidx',
                    create=True, size=size_bytes)
                self.table.hdr['isidxcreated'] = 0

            self.symbollastidx = np.ndarray(
                (hashtblsize,), dtype=np.int64, buffer=self.symbolidxshm.buf)
            self.symbolprevidx = np.ndarray((listsize,), dtype=np.int64, buffer=self.symbolidxshm.buf,
                                            offset=hashtblsize_bytes)
        elif self.table.type==1:
            self.symbolidxpath = str(self.table.filepath).replace('data.bin', 'symbolidx.bin')
            
            resetfile = False
            if (not os.path.exists(self.symbolidxpath)):
                resetfile = True                
            elif os.path.getsize(self.symbolidxpath) != size_bytes:
                resetfile = True

            if resetfile:
                self.create_file(self.symbolidxpath,size_bytes)
                self.table.hdr['isidxcreated'] = 0

            
            self.symbollastidx = np.memmap(self.symbolidxpath, np.int64, 'r+', 0, (hashtblsize,))
            self.symbolprevidx = np.memmap(self.symbolidxpath, np.int64, 'r+', hashtblsize_bytes, (listsize,))

        if self.table.hdr['isidxcreated'] == 0:
            self.symbollastidx[:] = -1
            self.symbolprevidx[:] = -1

    def malloc_portfolioidx(self, shm_name):
        """
        Allocate or map shared memory or memory-mapped files for portfolio index arrays based on the table type.
        
        For table type 2, it allocates shared memory segments for the portfolio index using the shareddata.malloc method.
        For table type 1, it creates or opens a memory-mapped file for the portfolio index.
        
        Initializes two numpy arrays, `portlastidx` and `portprevidx`, which represent the portfolio index hash table and a linked list of previous indices, respectively.
        
        If the index is newly created (indicated by `isidxcreated` flag), both arrays are initialized with -1.
        
        Parameters:
            shm_name (str): Base name for the shared memory segment or memory-mapped file.
        
        Side Effects:
            - May create or reset the portfolio index file or shared memory.
            - Updates `self.table.hdr['isidxcreated']` flag.
            - Sets `self.portlastidx` and `self.portprevidx` numpy arrays or memmaps.
        """
        hashtblsize = int(self.table.records.size*3)
        hashtblsize_bytes = int(hashtblsize * 8)
        listsize = self.table.records.size
        listsize_bytes = int(listsize * 8)
        size_bytes = int(hashtblsize_bytes+listsize_bytes)

        # portfolio index
        
        if self.table.type==2:
            [self.portidxshm, ismalloc] = self.shareddata.malloc(
                shm_name+'#portidx')
            if not ismalloc:
                [self.portidxshm, ismalloc] = self.shareddata.malloc(shm_name+'#portidx',
                    create=True, size=size_bytes)
                self.table.hdr['isidxcreated'] = 0

            self.portlastidx = np.ndarray(
                (hashtblsize,), dtype=np.int64, buffer=self.portidxshm.buf)
            self.portprevidx = np.ndarray((listsize,), dtype=np.int64, buffer=self.portidxshm.buf,
                                        offset=hashtblsize_bytes)
        elif self.table.type==1:
            self.portidxpath = str(self.table.filepath).replace('data.bin', 'portidx.bin')
            
            resetfile = False
            if (not os.path.exists(self.portidxpath)):
                resetfile = True                
            elif os.path.getsize(self.portidxpath) != size_bytes:
                resetfile = True
            if resetfile:
                self.create_file(self.portidxpath,size_bytes)
                self.table.hdr['isidxcreated'] = 0
            
            self.portlastidx = np.memmap(self.portidxpath, np.int64, 'r+', 0, (hashtblsize,))
            self.portprevidx = np.memmap(self.portidxpath, np.int64, 'r+', hashtblsize_bytes, (listsize,))            

        if self.table.hdr['isidxcreated'] == 0:
            self.portlastidx[:] = -1
            self.portprevidx[:] = -1    

    def create_index(self,start=0,update=False):
        """
        Creates or updates an index for the table's records based on primary key columns.
        
        Parameters:
            start (int): The starting index for the indexing process. Defaults to 0.
            update (bool): If True, updates an existing index; otherwise, creates a new index. Defaults to False.
        
        This method performs the following steps:
        - Prints status messages indicating whether the index is being created or updated.
        - Resets the primary key array.
        - Identifies and removes records with null primary keys.
        - Deduplicates records based on primary key columns, keeping the first occurrence.
        - Removes records outside the specified date range if applicable.
        - Initializes and updates various index arrays depending on the primary key string pattern.
        - Calls a specialized index creation function (`create_index_func`) with appropriate parameters.
        - Logs warnings and errors if null or duplicated records are found or if the index creation fails.
        - Prints the completion message with the processing speed in lines per second.
        
        Raises:
            Exception: If the primary key type is unsupported, if the index creation function is not enabled,
                       or if the index creation fails.
            ValueError: If filtering by date is required but `mindate` or `maxdate` is not set.
        """
        ti = time.time()
        if self.table.records.count > 0:
            if not update:
                print('Creating index %s %i lines...' %
                    (self.table.relpath, self.table.records.count))                
            else:
                print('Updating index %s %i lines...' %
                    (self.table.relpath, self.table.records.count))
            time.sleep(0.001)
    
            # TODO: CREATE AN UPDATE METHOD
            start = 0
            self.pkey[:] = -1            
                
            arr = self.table.records.records
            count = self.table.hdr['count']
            
            # check all null pkeys
            isnullpkey = np.ones(count, dtype=np.bool_)
            for pkeycol in self.pkeycolumns:
                if str(arr.dtype[pkeycol]) == 'datetime64[ns]':
                    # fix for datetime not 0 to nan conversions
                    isnullpkey = isnullpkey & (arr[:count][pkeycol].astype(int) == 0)
                elif str(arr.dtype[pkeycol]).startswith('|S'):
                    isnullpkey = isnullpkey & (arr[:count][pkeycol] == b'')
                else:
                    raise Exception(f'pkey type {arr.dtype[pkeycol]} not supported for indexing!')
            
            # remove null pkeys
            if np.any(isnullpkey):
                Logger.log.warning('Null records found in index %s!' % self.table.relpath)
                newcount = np.sum(~isnullpkey)
                arr[:newcount] = arr[:count][~isnullpkey]
                self.table.hdr['count'] = newcount
                count = newcount


            # deduplicate array
            if len(self.pkeycolumns)==1:
                unique, indices, inverse = np.unique(
                    arr[:count][self.pkeycolumns],
                    return_index=True, return_inverse=True
                    )
            else:
                unique, indices, inverse = np.unique(
                    arr[:count][self.pkeycolumns], axis=0, 
                    return_index=True, return_inverse=True
                    )
            # get the indices of the not duplicated rows 
            # while keeping the first element of the duplicated rows
            uniquecount = len(unique)
            if uniquecount < count:
                Logger.log.warning(f'Duplicated records found in {self.table.relpath}!')
                arr[:uniquecount] = arr[:count][indices]
                self.table.hdr['count'] = uniquecount
                count = uniquecount
                
            # remove outside date range
            if 'date' in self.pkeystr:
                if self.table.mindate is None or self.table.maxdate is None:
                    raise ValueError('mindate and maxdate must be set to filter by date')
                vidx = (arr[:count]['date']>=self.table.mindate) & (arr[:count]['date']<self.table.maxdate)
                if not np.all(vidx):
                    Logger.log.warning(f'Records outside date range {np.sum(~vidx)} found in {self.table.relpath}!')
                    lenvalid = np.sum(vidx)
                    arr[:lenvalid] = arr[:count][vidx]
                    self.table.hdr['count'] = lenvalid
            
            success=False
            if ('date_portfolio_symbol' in self.pkeystr) | ('date_tag_symbol' in self.pkeystr):
                self.datelastidx[:] = -1
                self.dateprevidx[:] = -1
                self.symbollastidx[:] = -1
                self.symbolprevidx[:] = -1
                self.portlastidx[:] = -1
                self.portprevidx[:] = -1
                success = self.create_index_func(arr, self.table.records.count, self.pkey,
                                                self.datelastidx, self.dateprevidx, self.table.mindate, self.periodns, \
                                                self.portlastidx, self.portprevidx, \
                                                self.symbollastidx, self.symbolprevidx,  start)
            elif 'date_symbol' in self.pkeystr:
                self.datelastidx[:] = -1
                self.dateprevidx[:] = -1
                self.symbollastidx[:] = -1
                self.symbolprevidx[:] = -1
                success = self.create_index_func(arr, self.table.records.count, self.pkey,
                                                self.datelastidx, self.dateprevidx, self.table.mindate, self.periodns, \
                                                self.symbollastidx, self.symbolprevidx, start)
            elif 'date_portfolio' in self.pkeystr:
                self.datelastidx[:] = -1
                self.dateprevidx[:] = -1
                self.portlastidx[:] = -1
                self.portprevidx[:] = -1
                success = self.create_index_func(arr, self.table.records.count, self.pkey,
                                                self.datelastidx, self.dateprevidx, self.table.mindate, self.periodns, \
                                                self.portlastidx, self.portprevidx, start)
            elif 'symbol' in self.pkeystr:                
                success = self.create_index_func(arr, self.table.records.count, self.pkey, start)
            else:
                errmsg = 'TableIndex.create_index(): create_index_func not enabled!'
                Logger.log.error(errmsg)
                raise Exception(errmsg)
            
            if not success:
                errmsg = ('Error creating index %s!!!' % (self.table.relpath))
                Logger.log.error(errmsg)
                raise Exception(errmsg)
                                    
            Logger.log.debug('Creating index %s %i lines/s DONE!' %
                  (self.table.relpath, self.table.records.count/(time.time()-ti)))

    def update_index(self, start):                
        """
        Updates the index starting from the specified position.
        
        Parameters:
        start (int): The position from which to begin updating the index.
        
        This method invokes the create_index method with the update parameter set to True,
        signifying that the existing index should be updated instead of being created from scratch.
        """
        self.create_index(start,update=True)        

    def sort_index(self, shnumpy, start=0):
        
        """
        Sorts the entries in `shnumpy` starting from the specified index `start` based on the primary key columns in reverse order.
        
        This method ensures thread safety by acquiring a lock on `self.table` during the sorting process. It uses `np.lexsort` to determine the sorted order of the entries. If the current order differs from the sorted order, it updates `shnumpy` by reordering the entries starting from `start`, updates the minimum change ID (`minchgid`), and refreshes the index accordingly. Header flags are updated to reflect the sorting and indexing status.
        
        Parameters:
            shnumpy (structured numpy array): The data array to be sorted.
            start (int, optional): The starting index from which to begin sorting. Defaults to 0.
        
        Exceptions:
            Logs an error message if any exception occurs during sorting.
        
        Thread Safety:
            Uses `self.table.acquire()` and `self.table.release()` to manage concurrent access.
        """
        try:
            self.table.acquire()
            
            keys = tuple(shnumpy[column][start:]
                         for column in self.pkeycolumns[::-1])
            idx = np.lexsort(keys)

            shift_idx = np.roll(idx, 1)
            if len(shift_idx) > 0:
                shift_idx[0] = -1
                idx_diff = idx - shift_idx
                unsortered_idx = np.where(idx_diff != 1)[0]
                if np.where(idx_diff != 1)[0].any():
                    _minchgid = np.min(unsortered_idx) + start
                    shnumpy.minchgid = _minchgid
                    shnumpy[start:] = shnumpy[start:][idx]
                    self.table.hdr['isidxcreated'] = 0
                    self.update_index(_minchgid)                    
                    self.table.hdr['isidxcreated'] = 1
                        
            self.table.hdr['isidxsorted'] = 1
        except Exception as e:
            Logger.log.error('Error sorting index!\n%s' % (e))
        finally:
            self.table.release()

    def create_file(self,fpath,size):
        """
        Creates a file at the specified path with the given size.
        
        This method opens a file in binary write mode, seeks to the byte position size-1,
        and writes a single null byte to allocate the file space. On POSIX systems, it uses
        os.posix_fallocate to efficiently allocate disk space. On Windows systems, the allocation
        step is currently not implemented.
        
        Parameters:
            fpath (str): The file path where the file will be created.
            size (int): The desired size of the file in bytes.
        
        Raises:
            OSError: If file operations or allocation fail.
        """
        with open(fpath, 'wb') as f:
            # Seek to the end of the file
            f.seek(size-1)
            # Write a single null byte to the end of the file
            f.write(b'\x00')
            if os.name == 'posix':
                os.posix_fallocate(f.fileno(), 0, size)
            elif os.name == 'nt':
                pass # TODO: implement windows file allocation

    def rememmap(self):
        """
        Remap all memory-mapped index files when the table size changes externally.
        
        This method recreates memory-mapped arrays for primary keys and various indices (date, symbol, portfolio)
        to reflect changes in the underlying table size. It should be called when the table has been resized
        by another process or thread.
        
        The method remaps the following index structures based on the primary key configuration:
        - Primary key hash table (`pkey`)
        - Date indices (`datelastidx`, `dateprevidx`) if 'date' is in primary keys
        - Symbol indices (`symbollastidx`, `symbolprevidx`) if 'symbol' is in primary keys
        - Portfolio indices (`portlastidx`, `portprevidx`) if 'portfolio' or 'tag' is in primary keys
        
        This method ONLY remaps existing index files and infers sizes from the actual file sizes.
        It does NOT create new index files - if files don't exist, an error is raised.
        
        This method only works with disk-backed tables (type 1). For shared memory tables (type 2),
        the shared memory segments need to be recreated using malloc.
        
        Raises:
            Exception: If called on a table type other than 1 (disk-backed) or if index files don't exist.
        """
        if self.table.type != 1:
            raise Exception('rememmap() only supported for disk-backed tables (type 1)')
        
        # Remap primary key - must exist
        if not hasattr(self, 'pkeypath') or not os.path.exists(self.pkeypath):
            raise Exception(f'Primary key index file does not exist: {getattr(self, "pkeypath", "path not set")}')
        
        # Infer keysize from actual file size
        file_size = os.path.getsize(self.pkeypath)
        keysize = file_size // 8  # int64 = 8 bytes
        self.pkey = np.memmap(self.pkeypath, np.int64, 'r+', 0, (keysize,))
        
        # Remap date indices if present
        if 'date' in self.pkeystr:
            if not hasattr(self, 'dateidxpath') or not os.path.exists(self.dateidxpath):
                raise Exception(f'Date index file does not exist: {getattr(self, "dateidxpath", "path not set")}')
            
            mindate = self.table.mindate.astype(np.int64)
            maxdate = self.table.maxdate.astype(np.int64)
            dateidxsize = (maxdate - mindate) // self.periodns
            hashtblsize_bytes = int(dateidxsize * 8)
            listsize = self.table.size
            listsize_bytes = int(listsize * 8)
            expected_size = hashtblsize_bytes + listsize_bytes
            
            # Check if file size matches
            if os.path.getsize(self.dateidxpath) == expected_size:
                self.datelastidx = np.memmap(self.dateidxpath, np.int64, 'r+', 0, (dateidxsize,))
                self.dateprevidx = np.memmap(self.dateidxpath, np.int64, 'r+', hashtblsize_bytes, (listsize,))
            else:
                raise Exception(f'Date index file size does not match expected size: {self.dateidxpath}')
        
        # Remap symbol indices if present
        if ('symbol' in self.pkeystr) and (len(self.pkeycolumns) > 1):
            if not hasattr(self, 'symbolidxpath') or not os.path.exists(self.symbolidxpath):
                raise Exception(f'Symbol index file does not exist: {getattr(self, "symbolidxpath", "path not set")}')
                        
            hashtblsize = int(self.table.size * 3)
            hashtblsize_bytes = int(hashtblsize * 8)
            listsize = self.table.size
            listsize_bytes = int(listsize * 8)
            expected_size = hashtblsize_bytes + listsize_bytes
            
            # Check if file size matches
            if os.path.getsize(self.symbolidxpath) == expected_size:
                self.symbollastidx = np.memmap(self.symbolidxpath, np.int64, 'r+', 0, (hashtblsize,))
                self.symbolprevidx = np.memmap(self.symbolidxpath, np.int64, 'r+', hashtblsize_bytes, (listsize,))
            else:
                raise Exception(f'Symbol index file size does not match expected size: {self.symbolidxpath}')
        
        # Remap portfolio indices if present
        if ('portfolio' in self.pkeystr) or ('tag' in self.pkeystr):
            if not hasattr(self, 'portidxpath') or not os.path.exists(self.portidxpath):
                raise Exception(f'Portfolio index file does not exist: {getattr(self, "portidxpath", "path not set")}')
            
            hashtblsize = int(self.table.size * 3)
            hashtblsize_bytes = int(hashtblsize * 8)
            listsize = self.table.size
            listsize_bytes = int(listsize * 8)
            expected_size = hashtblsize_bytes + listsize_bytes
            
            # Check if file size matches
            if os.path.getsize(self.portidxpath) == expected_size:
                self.portlastidx = np.memmap(self.portidxpath, np.int64, 'r+', 0, (hashtblsize,))
                self.portprevidx = np.memmap(self.portidxpath, np.int64, 'r+', hashtblsize_bytes, (listsize,))
            else:
                raise Exception(f'Portfolio index file size does not match expected size: {self.portidxpath}')
        
    def flush(self):        
        """
        Flushes memory-mapped arrays related to the primary key and updates their file modification times.
        
        If the primary key size is greater than one, this method flushes the memory-mapped arrays (`pkey`, `datelastidx`, `dateprevidx`, `symbollastidx`, `symbolprevidx`, `portlastidx`, `portprevidx`) based on the presence of the substrings 'date', 'symbol', and 'portfolio' in the primary key string (`pkeystr`). After flushing each relevant memory-mapped array, it updates the corresponding file's modification time to match the modification time stored in the table header (`self.table.hdr['mtime']`).
        
        This ensures that all changes to the memory-mapped arrays are persisted to disk and that the file timestamps remain consistent with the table's metadata.
        """
        if self.pkey.size>1:
            mtime = self.table.hdr['mtime']
            if isinstance(self.pkey,np.memmap):
                self.pkey.flush()
                os.utime(self.pkeypath, (mtime, mtime))
            
            if 'date' in self.pkeystr:
                if isinstance(self.datelastidx,np.memmap):
                    self.datelastidx.flush()
                if isinstance(self.dateprevidx,np.memmap):
                    self.dateprevidx.flush()
                    os.utime(self.dateidxpath, (mtime, mtime))
            
            if 'symbol' in self.pkeystr:
                if isinstance(self.symbollastidx,np.memmap):
                    self.symbollastidx.flush()
                if isinstance(self.symbolprevidx,np.memmap):
                    self.symbolprevidx.flush()
                    os.utime(self.symbolidxpath, (mtime, mtime))

            if 'portfolio' in self.pkeystr:
                if isinstance(self.portlastidx,np.memmap):
                    self.portlastidx.flush()
                if isinstance(self.portprevidx,np.memmap):
                    self.portprevidx.flush()
                    os.utime(self.portidxpath, (mtime, mtime))
        
    def free(self):        
        """
        Releases resources associated with the object's primary key and related indices.
        
        This method attempts to flush any pending operations, then checks if the primary key (`pkey`) exists and has a size greater than zero.
        If so, it sets the primary key to None and conditionally clears index attributes based on the contents of `pkeystr`:
        - If 'date' is in `pkeystr`, clears date-related indices.
        - If 'date_symbol' is in `pkeystr`, clears symbol-related indices.
        - If 'portfolio' is in `pkeystr`, clears portfolio-related indices.
        
        Any exceptions encountered during this process are caught and logged as errors.
        """
        try:
            self.flush()
            if self.pkey.size>0:
                self.pkey = None      
                if 'date' in self.pkeystr:      
                    self.datelastidx = None
                    self.dateprevidx = None
                if 'date_symbol' in self.pkeystr:
                    self.symbollastidx = None                
                    self.symbolprevidx = None            
                if 'portfolio' in self.pkeystr:
                    self.portlastidx = None                
                    self.portprevidx = None
        except Exception as e:
            Logger.log.error(f"TableIndex.free() {self.table.relpath}: {e}")

    @staticmethod
    def get_pkeycolumns(database):    
        """
        Retrieve the primary key columns for a specified database.
        
        Parameters:
            database (str): The name of the database to retrieve primary key columns for.
        
        Returns:
            list: A list containing the names of the primary key columns for the given database.
        
        Raises:
            Exception: If the specified database is not found in the predefined DATABASE_PKEYS mapping.
        """
        if database in DATABASE_PKEYS:
            return DATABASE_PKEYS[database]
        else:
            raise Exception('Database not implemented!')
