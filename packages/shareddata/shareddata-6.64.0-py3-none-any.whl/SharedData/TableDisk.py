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
import shutil

from SharedData.Logger import Logger
from SharedData.IO.AWSS3 import S3DeleteFolder
from SharedData.TableIndex import TableIndex
from SharedData.SharedNumpy import SharedNumpy
from SharedData.IO.ClientSocket import ClientSocket
from SharedData.Table import Table

from SharedData.Utils import cpp


class TableDisk(Table):    

    """
    A subclass of Table that manages disk-backed tables with memory-mapped file support.
    
    This class provides functionality to create, extend, and manage tables stored on disk using memory mapping for efficient access. It supports operations such as allocation (`malloc`), freeing resources (`free`), writing changes to disk (`write_file`), trimming unused space (`trim`), reloading data from disk (`reload`), and deleting both local and remote data (`delete_local`, `delete_remote`, `delete`).
    
    Attributes:
        type (int): Identifier for the table type, set to 1 for disk-backed tables.
        shf_hdr (np.memmap): Memory-mapped header of the table file.
        shf_data (np.memmap): Memory-mapped data section of the table file.
        records (SharedNumpy): Shared numpy array wrapper around the memory-mapped data.
        Other attributes inherited from Table.
    
    Methods:
        malloc(): Creates or extends the current file and memory maps the header and data sections.
        free(acquire=True): Flushes and frees memory-mapped resources and associated indexes.
        write_file(): Flushes header, data, and index to disk and updates file modification time.
        trim(): Reduces the file size to match the actual number of records
    """
    def __init__(self, shareddata, database, period, source, tablename,
                 records=None, names=None, formats=None, size=None,hasindex=True,
                 overwrite=False, user='master', partitioning=None, is_schemaless=False):
        """
        Initialize an instance with specified parameters and set up internal data structures.
        
        Parameters:
            shareddata: Shared data resource or context.
            database: Database connection or identifier.
            period: Time period or range for the data.
            source: Data source identifier.
            tablename: Name of the table to operate on.
            records (optional): Number of records to process or retrieve.
            names (optional): List of field names or column names.
            formats (optional): Data formats corresponding to the fields.
            size (optional): Size specification for the data structure.
            hasindex (bool, optional): Flag indicating if the table has an index. Defaults to True.
            overwrite (bool, optional): Flag to allow overwriting existing data. Defaults to False.
            user (str, optional): User identifier for access control. Defaults to 'master'.
            partitioning (optional): Partitioning scheme or configuration.
        
        Sets:
            self.type: Internal type identifier set to 1.
            self.shf_hdr: Initialized as an empty NumPy array for header data.
            self.shf_data: Initialized as an empty NumPy array for main data.
        
        Calls the superclass initializer with the provided parameters and additional internal type.
        """
        self.type = 1
        self.shf_hdr = np.array([])
        self.shf_data = np.array([])
        super().__init__(shareddata, database, period, source, tablename,
                         records=records, names=names, formats=formats, size=size,hasindex=hasindex,
                         overwrite=overwrite, user=user, tabletype=self.type, partitioning=partitioning, is_schemaless=is_schemaless)

    ############### MALLOC ###############
    def malloc(self,create=False):
        # create or extend currrent file
        """
        Allocate and initialize memory-mapped file storage for header and data records.
        
        This method creates or extends the current file, memory maps the header and data sections,
        updates the header with the current size, and initializes a SharedNumpy object to manage
        the data records.
        
        Attributes updated:
        - self.shf_hdr: memory-mapped header array
        - self.hdr: header data structure updated with record size
        - self.shf_data: memory-mapped data array
        - self.records: SharedNumpy instance managing the data records
        """
        self.create_file()
        
        # memory map header        
        self.shf_hdr = np.memmap(self.filepath,self.hdrdtype,'r+',0,(1,))        
        if create:
            self.shf_hdr[0] = self.hdr
            self.shf_hdr.flush()
        self.hdr = self.shf_hdr[0]
        self.hdr['recordssize'] = int(self.size)

        # memory map data
        offset = self.hdr.dtype.itemsize
        self.shf_data = np.memmap(self.filepath,self.recdtype,'r+',offset,(self.hdr['recordssize'],))
        self.records = SharedNumpy('DISK', self.shf_data)
        self.records.table = self        
    
    ############### FREE ###############
    def free(self, acquire=True):        
        """
        Release resources associated with the table, including header, data, and index.
        
        This method flushes any buffered data before freeing resources and removes the table's data from shared storage.
        It optionally acquires a lock before freeing resources to ensure thread safety.
        Exceptions during the process are caught and logged, and the 'isloaded' mutex flag is reset regardless of success.
        
        Parameters:
            acquire (bool): If True, acquires a lock before freeing resources and releases it afterward. Default is True.
        """
        try:
            if acquire:
                self.acquire()
            # flush & free header
            if (not self.shf_hdr is None):
                if (len(self.shf_hdr)>0):
                    self.shf_hdr.flush()
            self.shf_hdr = None
            # flush & free data
            if (not self.shf_data is None):
                if (len(self.shf_data)>0):
                    self.shf_data.flush()
            self.shf_data = None
            
            # flush & free BSON mmap
            if hasattr(self, 'bson_mmap') and self.bson_mmap is not None:
                self.bson_mmap.flush()
                self.bson_mmap.close()
                self.bson_mmap = None
            
            if hasattr(self, 'bson_file_handle') and self.bson_file_handle is not None:
                self.bson_file_handle.close()
                self.bson_file_handle = None
            
            # flush & free index
            if self.hasindex:
                self.index.free()            
            if self.relpath in self.shareddata.data:
                del self.shareddata.data[self.relpath]            
        except Exception as e:
            Logger.log.error(f"TableDisk.free() {self.relpath}: {e}")
        finally:
            self.mutex['isloaded'] = 0
            if acquire:
                self.release()

    ############### WRITE ###############
    def write_file(self):
        # flush header
        """
        Flushes the header, data, and index buffers to disk, updates the file's modification time based on the latest timestamps in the header, and applies this modification time to the file at the specified filepath.
        """
        # Safety check: ensure resources are still available (can be None if freed)
        if self.shf_hdr is None or self.shf_data is None:
            errmsg = f"write_file() called on closed table {self.relpath}"
            Logger.log.error(errmsg)
            raise Exception(errmsg)
            
        self.shf_hdr.flush()
        # flush data
        self.shf_data.flush()
        # set the modify time of the file
        mtime = max(self.hdr['mtime'],
                    self.hdr['mtimehead'], self.hdr['mtimetail'])
        self.hdr['mtime'] = mtime
        os.utime(self.filepath, (mtime, mtime))
        # flush index
        if self.hdr['hasindex']==1:
            self.index.flush()

    ############### TRIM ###############
    def trim(self):        

        """
        Trim the underlying data file to match the actual number of records.
        
        If the recorded size (`recordssize`) is greater than the current count of records (`count`), this method adjusts the header to reflect the correct size, resets relevant flags, and writes the updated header and records to a temporary file. It then replaces the original file with this trimmed version to free up unused space. On POSIX systems, it attempts to preallocate the file space for efficiency. If no trimming is needed, the original object is returned unchanged.
        
        Returns:
            The updated table object if trimming was performed; otherwise, returns self.
        """
        if self.hdr['recordssize'] > self.hdr['count']:
            if self.hdr['count']==0:
                self.hdr['recordssize'] = 2
            else:
                self.hdr['recordssize'] = self.hdr['count']
            self.hdr['isloaded'] = 0
            self.mutex['isloaded'] = 0
            self.hdr['isidxcreated'] = 0
            self.size = self.hdr['count']
            self.write_file()

            totalbytes = int(self.hdrdtype.itemsize
                    + self.recdtype.itemsize*self.size)

            self.filepathtmp = str(self.filepath)+'.tmp'
            if Path(self.filepathtmp).is_file():
                os.remove(self.filepathtmp)

            with open(self.filepathtmp, 'wb') as f:
                # Seek to the end of the file
                f.seek(totalbytes-1)
                # Write a single null byte to the end of the file
                f.write(b'\x00')
                if os.name == 'posix':
                    os.posix_fallocate(f.fileno(), 0, totalbytes)
                elif os.name == 'nt':
                    pass  # TODO: implement preallocation for windows in pyd
                
                f.seek(0)
                f.write(self.hdr.tobytes())
                f.write(self.records[:self.records.count].tobytes())
                f.flush()

            self.free()
            os.remove(self.filepath)
            os.rename(self.filepathtmp, self.filepath)
            tbl = self.shareddata.table(self.database, self.period, self.source, self.tablename)
            tbl.write()
            return tbl
        else:
            return self

    ############### RELOAD ###############
    def reload(self):
        """
        Reloads the table data from disk by performing a sequence of operations to ensure data consistency and resource management.
        
        The method:
        - Acquires necessary locks or resources to safely perform the reload.
        - Frees current resources without acquiring new ones to prepare for fresh data.
        - Downloads the latest table data from disk.
        - Allocates memory for the newly downloaded data.
        - If an index exists, resets its creation flag and initializes the index.
        - Updates shared data references to point to the reloaded table.
        - Marks the table as loaded in both header and mutex states.
        - Handles and logs any exceptions that occur during the reload process.
        - Ensures that all acquired resources are released after the operation, regardless of success or failure.
        
        Returns:
            The records of the reloaded table.
        """
        try:
            self.acquire()
            self.free(acquire=False)
            self.download()
            self.malloc()
            if self.hasindex:
                self.hdr['isidxcreated'] = 0
                self.index.initialize()
            self.shareddata.data[self.relpath] = self
            self.hdr['isloaded'] = 1
            self.mutex['isloaded'] = 1
        except Exception as e:
            errmsg = f"TableDisk.reload() {self.relpath}: {e}"
            Logger.log.error(errmsg)
            raise Exception(errmsg)
        finally:
            self.release()
        
        return self.records
    
    ############### DELETE ###############
    def delete_local(self):    
        """
        Deletes local data files and associated entries for the object's path.
        
        This method removes the data corresponding to `self.path` from the internal `self.data` dictionary,
        frees any allocated resources, and deletes specific binary files from the local filesystem if they exist.
        If the directory containing these files becomes empty after deletion, it removes the directory as well.
        
        Returns:
            bool: True if the deletion process completes successfully without exceptions, False otherwise.
        """
        success = False
        try:
            path = self.path
            # raise NotImplementedError(f'Delete {path} not implemented')
            if path in self.data.keys():
                self.data[path].free()
                del self.data[path]

            buff = np.full((1,),np.nan,dtype=self.schema.dtype)
            buff['symbol'] = path.replace('\\', '/')
            loc = self.shareddata.schema.get_loc(buff,acquire=False)
            if loc[0] != -1: # table exists
                folder_local = self.schema[loc[0]]['folder_local']
                database_folder = folder_local.decode('utf-8')
                localpath = Path(database_folder) / path
                if localpath.exists():
                    delfiles = ['data.bin','dateidx.bin','pkey.bin','symbolidx.bin','portidx.bin']
                    for file in delfiles:
                        delpath = Path(localpath/file)
                        if delpath.exists():
                            os.remove(delpath)
                # if folder is empty remove it
                if not any(localpath.iterdir()):
                    shutil.rmtree(localpath)            

            success = True
            
        except Exception as e:
            Logger.log.error(f'Delete {path} Error: {e}')
        finally:
            pass

        return success        
                
    def delete_remote(self):        
        """
        Deletes the remote folder in the S3 storage corresponding to the current instance's database, period, source, and tablename attributes.
        
        The S3 path is constructed in the format: "{database}/{period}/{source}/{tablename}". This method then calls the S3DeleteFolder function to remove the folder and all its contents from the S3 bucket.
        """
        s3_path = f"{self.database}/{self.period}/{self.source}/{self.tablename}"
        S3DeleteFolder(s3_path)
            
    def delete(self):
        """
        Deletes the table disk by performing both local and remote deletions safely.
        
        This method acquires necessary resources before attempting to delete the table disk locally and remotely.
        It ensures that resources are properly freed even if an error occurs during the deletion process.
        Any exceptions raised are logged with the table disk's relative path and then re-raised.
        
        Raises:
            Exception: If any error occurs during the deletion process.
        """
        try:
            self.acquire()
            self.delete_local()            
            self.delete_remote()
            self.free(acquire=False)
        except Exception as e:
            errmsg = f"TableDisk.delete() {self.relpath}: {e}"
            Logger.log.error(errmsg)
            raise Exception(errmsg)
        finally:
            self.release()