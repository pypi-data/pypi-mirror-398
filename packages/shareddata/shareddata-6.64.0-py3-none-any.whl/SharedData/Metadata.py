import os
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import numpy as np
import time
import subprocess
from datetime import datetime, timedelta
import gzip
import io
import shutil
import hashlib


import SharedData.Defaults as Defaults
from SharedData.Logger import Logger
from SharedData.IO.AWSS3 import S3ListFolder, S3Download, S3Upload, S3DeleteFolder
from SharedData.IO.AWSS3 import UpdateModTime

# TODO: CREATE BSON MODE
class Metadata():

    """
    Class to manage metadata storage and synchronization between local files and S3.
    
    Attributes:
        user (str): User identifier, default is 'master'.
        name (str): Name identifier for the metadata.
        _records (np.ndarray): Internal numpy structured array holding the metadata records.
        records_chg (bool): Flag indicating if records have changed.
        _index_columns (np.ndarray): Array of index column names.
        _static (pd.DataFrame): Cached pandas DataFrame representation of the metadata.
        static_chg (bool): Flag indicating if static DataFrame has changed.
    
    Methods:
        static (property): Get or set the metadata as a pandas DataFrame, syncing with records.
        records (property): Get or set the metadata as numpy records, syncing with DataFrame.
        hasindex(): Returns True if the metadata has a valid index defined.
    """
    def __init__(self, name, user='master'):

        """
        Initialize the object with a specified name and user role.
        
        Parameters:
            name (str): The name identifier for the object.
            user (str, optional): The user role associated with the object. Defaults to 'master'.
        
        
        """
        self.user = user
        self.name = name

        self._records = np.array([])
        self.records_chg = False

        self._index_columns = np.array([])
        self._static = pd.DataFrame([])
        self.static_chg = False

        self.load()

    @property
    def static(self):
        if self.records_chg:
            self.records_chg = False
            self._static = self.records2df(self._records)
        self.static_chg = True
        return self._static

    @static.setter
    def static(self, df):
        """
        Set the static DataFrame and update related state flags and index columns.
        
        Parameters:
        df (pandas.DataFrame): The DataFrame to be set as the static data.
        
        Side Effects:
        - Sets the 'static_chg' flag to True indicating the static data has changed.
        - Resets the 'records_chg' flag to False.
        - Updates '_index_columns' with the index names of the provided DataFrame.
        - Stores the DataFrame in the '_static' attribute.
        """
        self.static_chg = True
        self.records_chg = False
        self._index_columns = np.array(df.index.names)
        self._static = df

    @property
    def records(self):
        if self.static_chg:
            self.static_chg = False
            self._records = self.df2records(self._static)
        self.records_chg = True
        return self._records

    @records.setter
    def records(self, value):
        """
        Setter for the 'records' property. Updates the internal '_records' attribute with the provided value and sets the 'records_chg' flag to True to indicate that the records have been modified.
        """
        self.records_chg = True
        self._records = value

    def hasindex(self):
        """
        Check if the object has a valid index.
        
        Returns True if the first element in the _index_columns attribute exists,
        is not None, and is not an empty string. Otherwise, returns False.
        """
        if self._index_columns.size > 0:
            if not self._index_columns[0] is None:
                if self._index_columns[0] != '':
                    return True
        return False

    def records2df(self, records):
        """
        Convert a list of records into a pandas DataFrame, decode byte string columns to UTF-8 strings, and set the DataFrame index if applicable.
        
        Parameters:
            records (list): A list of records (e.g., dictionaries or tuples) to be converted into a DataFrame.
        
        Returns:
            pd.DataFrame: A DataFrame constructed from the input records with byte string columns decoded and index set if defined.
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
        if self.hasindex():
            df = df.set_index(self._index_columns.tolist())
        return df

    def df2records(self, df):
        """
        Convert a pandas DataFrame into a contiguous numpy record array suitable for binary storage or processing.
        
        This method performs the following steps:
        - Stores the DataFrame's index column names.
        - Resets the index if the DataFrame has an index, ensuring all data is in columns.
        - Converts any datetime columns with timezone information to UTC naive datetime.
        - Converts object dtype columns to UTF-8 encoded byte strings.
        - Converts the DataFrame to a numpy record array without the index.
        - Checks for any remaining object dtype fields in the resulting record array and raises an error if found.
        
        Args:
            df (pandas.DataFrame): The DataFrame to convert.
        
        Returns:
            np.ndarray: A contiguous numpy record array representing the DataFrame data without index.
        
        Raises:
            Exception: If conversion to a binary-compatible record array fails due to unsupported data types.
        """
        self._index_columns = np.array(df.index.names)
        if self.hasindex():
            df = df.reset_index().copy()
        else:
            df = df.copy()
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
                Logger.log.error(f'df2records(): Could not convert {tag} : {e}!')
            df[tag] = df[tag].astype('|S')      
        
        rec = np.ascontiguousarray(df.to_records(index=False))
        type_descriptors = [field[1] for field in rec]
        if '|O' in type_descriptors:
            errmsg = 'df2records(): Could not convert type to binary'
            Logger.log.error(errmsg)
            raise Exception(errmsg)
                
        return rec

    def __setitem__(self, tag, value):
        """
        Sets the value for a specified tag in the static dictionary and flags the static data as changed.
        
        Parameters:
        tag (hashable): The key under which the value will be stored.
        value (any): The value to be assigned to the given tag.
        """
        self.static_chg = True
        self.static[tag] = value

    def __getitem__(self, tag):
        """
        Retrieve the value associated with the specified tag from the static dictionary.
        
        Parameters:
        tag (hashable): The key used to look up the value in the static dictionary.
        
        Returns:
        object: The value corresponding to the given tag.
        
        Raises:
        KeyError: If the tag does not exist in the static dictionary.
        """
        return self.static[tag]

    @staticmethod
    def list(keyword, user='master'):
        """
        Retrieve a list of metadata keys from an S3 bucket folder filtered by a keyword.
        
        Parameters:
            keyword (str): The keyword to filter the metadata files.
            user (str, optional): The user directory prefix in the S3 bucket. Defaults to 'master'.
        
        Returns:
            list: A list of metadata keys (filenames without extensions) that contain '.bin' in their names within the specified user's metadata folder.
        """
        mdprefix = user+'/Metadata/'
        keys = S3ListFolder(mdprefix+keyword)
        keys = keys[['.bin' in k for k in keys]]
        keys = [k.replace(mdprefix, '').split('.')[0] for k in keys]
        return keys

    # READ
    def load(self):
        """
        Load metadata for the current user and dataset, prioritizing local binary files but optionally downloading and reading from S3 or Excel files.
        
        The method performs the following steps:
        - Constructs file paths for binary and Excel metadata files based on environment variables and user attributes.
        - Creates necessary directories if saving locally.
        - Downloads and decompresses metadata from S3 if configured to do so.
        - Determines whether to read metadata from a local binary file or an Excel file, preferring the newer file.
        - Reads and processes metadata from the chosen source, updating local files and modification times as needed.
        - Logs debug information about loading progress and completion.
        
        
        """
        t = time.time()
        self.fpath = Path(os.environ['DATABASE_FOLDER']) / self.user
        self.pathxls = self.fpath / ('Metadata/'+self.name+'.xlsx')
        self.path = self.fpath / ('Metadata/'+self.name+'.bin')
        
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # update bin before comparing dates            
        [md_io_gzip, local_mtime, remote_mtime] = \
            S3Download(str(self.path)+'.gzip', str(self.path), False)

        readbin = True
        readxlsx = False

        # prefer read bin
        # but read excel if newer

        readbin = self.path.is_file()
        readxlsx = self.pathxls.is_file()
        if (readbin) & (readxlsx):
            readxlsx = os.path.getmtime(
                self.pathxls) > os.path.getmtime(self.path)
            readbin = not readxlsx

        if (not readxlsx):
            # read bin
            md_io = None
            if (not md_io_gzip is None):
                md_io = io.BytesIO()
                md_io_gzip.seek(0)
                with gzip.GzipFile(fileobj=md_io_gzip, mode='rb') as gz:
                    shutil.copyfileobj(gz, md_io)
                self.read_metadata_io(md_io)            
                # save local
                Metadata.write_file(md_io, self.path, remote_mtime)
                UpdateModTime(self.path, remote_mtime)

            if (md_io is None) & (self.path.is_file()):
                with open(str(self.path), 'rb') as md_io:
                    self.read_metadata_io(md_io)

        elif readxlsx:
            tini = time.time()

            xls = pd.read_excel(self.pathxls, sheet_name=None)
            if 'static' in xls:
                self.static = xls['static']

            if not self.static.empty:
                self.static = self.static.set_index(self.static.columns[0])

                    
    def read_metadata_io(self, bin_io):
        """
        Reads and validates metadata from a binary I/O stream, then parses and stores the metadata records.
        
        Parameters:
            bin_io (io.BytesIO or similar): A binary I/O stream containing the metadata.
        
        Process:
            - Seeks to the beginning of the binary stream.
            - Reads a 32-byte header containing metadata information.
            - Reads the descriptor string, data block, and MD5 hash from the stream.
            - Computes the MD5 hash of the descriptor string and data, and compares it to the read hash to verify integrity.
            - Raises an exception if the metadata file is corrupted (hash mismatch).
            - Decodes and parses the descriptor string to extract field names, formats, and index columns.
            - Constructs a NumPy structured array from the data using the parsed dtype.
            - Stores the index columns and records as instance attributes.
        """
        bin_io.seek(0)
        header = np.frombuffer(bin_io.read(32), dtype=np.int64)
        descr_str_b = bin_io.read(int(header[0]))
        data = bin_io.read(int(header[3]))
        md5hash_b = bin_io.read(16)

        m = hashlib.md5(descr_str_b)
        m.update(data)
        _md5hash_b = m.digest()
        #TODO: CHANGE THE COMPARE METHOD!
        if not md5hash_b == _md5hash_b:
            raise Exception('Metadata file corrupted!\n%s' % (self.path))

        descr_str = descr_str_b.decode(encoding='UTF-8', errors='ignore')
        descr = descr_str.split(';')
        names = descr[0].split(',')
        formats = descr[1].split(',')
        self._index_columns = np.array(descr[2].split(','))
        dtype = np.dtype({'names': names, 'formats': formats})
        self.records = np.ndarray((header[2],), dtype=dtype, buffer=data)

    # WRITE
    def save(self, save_excel=False):
        """
        Save the metadata object to local storage and optionally upload it to S3.
        
        Parameters:
            save_excel (bool): If True, save the metadata as an Excel file (.xlsx) before saving the binary file.
        
        Behavior:
        - Constructs file paths for Excel (.xlsx) and binary (.bin) metadata files based on the environment variable 'DATABASE_FOLDER' and the object's user and name attributes.
        - Creates necessary directories if they do not exist.
        - If save_excel is True, writes the metadata to an Excel file using pandas, setting the file's modification time to the current timestamp.        
        - Compresses and uploads the metadata file to S3 if the 's3write' attribute is True.
        - Logs the duration of the save operation if the environment variable 'LOG_LEVEL' is set to 'DEBUG'.
        """
        fpath = Path(os.environ['DATABASE_FOLDER']) / self.user
        self.pathxls = fpath / ('Metadata/'+self.name+'.xlsx')
        self.path = fpath / ('Metadata/'+self.name+'.bin')

        tini = time.time()
        mtime = datetime.now().timestamp()
        if not os.path.isdir(self.path.parents[0]):
            os.makedirs(self.path.parents[0])
        # save excel first so that last modified
        # timestamp is older
        if save_excel:
            with open(self.pathxls, 'wb') as f:
                writer = pd.ExcelWriter(f, engine='xlsxwriter')
                if self.hasindex():
                    self.static.to_excel(
                        writer, sheet_name='static', index=True)
                else:
                    self.static.to_excel(
                        writer, sheet_name='static', index=False)
                writer.close()
                f.flush()
            os.utime(self.pathxls, (mtime, mtime))
    
        io_obj = self.create_metadata_io()
        Metadata.write_file(io_obj, self.path, mtime)

        # Upload to S3
        io_obj.seek(0)
        gzip_io = io.BytesIO()
        with gzip.GzipFile(fileobj=gzip_io, mode='wb', compresslevel=1) as gz:
            shutil.copyfileobj(io_obj, gz)
        S3Upload(gzip_io, str(self.path)+'.gzip', mtime)
        
    def create_metadata_io(self):
        """
        Creates an in-memory bytes buffer containing metadata and binary data for the records.
        
        Constructs a header with metadata including the dtype description length, item size, total number of items,
        and total byte size. It then serializes the header, a string describing the dtype and optional index columns,
        the raw binary data, and an MD5 hash of the dtype description and data into a BytesIO object.
        
        Returns:
            io.BytesIO: A BytesIO object containing the serialized header, dtype description string, raw data bytes,
                        and an MD5 hash for integrity verification.
        """
        data = self.records
        descr = data.__array_interface__['descr']
        names = ','.join([item[0] for item in descr])
        dt = ','.join([item[1] for item in descr])
        if self.hasindex():
            index = ','.join([col for col in self._index_columns])
            descr_str = names+';'+dt+';'+index
        else:
            descr_str = names+';'+dt+';'
        descr_str_b = str.encode(descr_str, encoding='UTF-8', errors='ignore')
        header = [len(descr_str_b), data.itemsize,
                  data.size, data.itemsize*data.size]
        header = np.array(header).astype(np.int64)
        m = hashlib.md5(descr_str_b)
        m.update(data)
        md5hash_b = m.digest()
        io_obj = io.BytesIO()
        io_obj.write(header)
        io_obj.write(descr_str_b)
        io_obj.write(data)
        io_obj.write(md5hash_b)
        return io_obj

    @staticmethod
    def write_file(io_obj, path, mtime):
        """
        Write the contents of a BytesIO-like object to a file and update its modification time.
        
        Parameters:
        io_obj (io.BytesIO): An in-memory bytes buffer containing the data to write.
        path (str): The file system path where the data should be written.
        mtime (float): The modification time to set for the file, expressed as a Unix timestamp.
        
        This method opens the specified file in binary write mode, writes the contents of the provided
        io_obj to it, flushes the write buffer to ensure all data is written, and then sets the file's
        access and modification times to the given mtime.
        """
        with open(path, 'wb') as f:
            f.write(io_obj.getbuffer())
            f.flush()
        os.utime(path, (mtime, mtime))


    @staticmethod
    def delete(name, user='master'):
        """
        Deletes metadata files associated with the specified name for a given user.
        
        This static method removes the Excel (.xlsx) and binary (.bin) metadata files located in the user's directory
        within the path defined by the DATABASE_FOLDER environment variable. It also deletes the corresponding compressed
        (.gzip) file from an S3 storage location.
        
        Parameters:
            name (str): The base name of the metadata files to delete (without file extension).
            user (str, optional): The user directory under DATABASE_FOLDER. Defaults to 'master'.
        
        Returns:
            bool: True if all deletions succeed without exceptions, False otherwise.
        """
        try:            
            fpath = Path(os.environ['DATABASE_FOLDER']) / user
            pathxls = fpath / ('Metadata/'+name+'.xlsx')
            if pathxls.exists():
                os.remove(pathxls)
            path = fpath / ('Metadata/'+name+'.bin')
            if path.exists():
                os.remove(path)
            s3path = str(path)+'.gzip'
            s3path = s3path.replace(os.environ['DATABASE_FOLDER'],'')
            s3path = s3path.replace('\\','/')
            s3path = s3path.lstrip('/')
            S3DeleteFolder(s3path)
            return True
        except Exception as e:
            Logger.log.error(f'Delete {path} Error: {e}')
            return False

    # UTILS
    def mergeUpdate(self, newdf):
        """
        Merge and update the internal DataFrame `self.static` with a new DataFrame `newdf`.
        
        This method performs the following steps:
        1. Validates that the index names of `newdf` match those of `self.static`. Raises an exception if any index name is None or does not match.
        2. Adds any new index entries from `newdf` that are not already present in `self.static`.
        3. Adds any new columns from `newdf` that are not already present in `self.static`.
        4. Updates the existing entries in `self.static` with values from `newdf`.
        5. Sets the flag `self.static_chg` to True to indicate that `self.static` has been modified.
        
        Raises:
            Exception: If `newdf` index names are None or do not match `self.static` index names.
        """
        for i in range(len(newdf.index.names)):
            idxname = newdf.index.names[i]
            if idxname == None:
                Logger.log.error(
                    '%s metadata mergeUpdate newdf index is None!' % self.name)
                raise Exception(
                    '%s metadata mergeUpdate newdf index is None!' % self.name)
            elif idxname != self.static.index.names[i]:
                Logger.log.error(
                    '%s metadata mergeUpdate newdf index does not match!' % self.name)
                raise Exception(
                    '%s metadata mergeUpdate newdf index does not match!' % self.name)

        newidx = ~newdf.index.isin(self.static.index)
        if newidx.any():
            self.static = self.static.reindex(
                index=self.static.index.union(newdf.index))

        newcolsidx = ~newdf.columns.isin(self.static.columns)
        if newcolsidx.any():
            newcols = newdf.columns[newcolsidx]
            self.static = pd.concat([self.static, newdf[newcols]], axis=1)

        self.static.update(newdf)
        self.static_chg = True


def isnan(value):
    """
    Check if the given value represents a NaN (Not a Number).
    
    Parameters:
        value (str or float): The value to check.
    
    Returns:
        bool: True if the value is the string 'nan', an empty string, or a float NaN; False otherwise.
    """
    if isinstance(value, str):
        return ((value == 'nan') | (value == ''))
    elif isinstance(value, float):
        return np.isnan(value)