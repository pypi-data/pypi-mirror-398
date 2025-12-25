import pandas as pd
import numpy as np
import datetime
import math
import bson
from bson import ObjectId
import hashlib
import json
import asyncio

from SharedData.Database import *
from SharedData.Utils import datetype
from pymongo import ASCENDING, DESCENDING,UpdateOne
from SharedData.Logger import Logger
from SharedData.IO.MongoDBClient import MongoDBClient

class CollectionMongoDB:

    # TODO: create partitioning option yearly, monthly, daily
    """
    A class to manage MongoDB collections with support for upsert and append operations,
    automatic index handling, and data serialization/deserialization between MongoDB documents
    and pandas DataFrames.
    
    Attributes:
        type (int): Storage type of the collection (1: DISK, 2: MEMORY).
        shareddata: Shared data object containing MongoDB client.
        user (str): User namespace for MongoDB client.
        database (str): Database name.
        period (str): Period identifier (e.g., 'D1', 'M15', 'M1') used for date normalization.
        source (str): Source identifier.
        tablename (str): Collection name.
        subscription_thread: Placeholder for subscription thread (not implemented).
        publish_thread: Placeholder for publish thread (not implemented).
        names (list): Optional list of field names.
        formats (list): Optional list of field formats.
        size (int): Optional size parameter.
        hasindex (bool): Whether the collection has an index on primary keys.
        overwrite (bool): Whether to overwrite existing data.
        partitioning: Partitioning option (currently not implemented).
        _collection: The underlying pymongo collection object.
        mongodb: MongoDB shared data interface.
        mongodb_client: MongoDB
    """
    def __init__(self, shareddata, database, period, source, tablename,
                 hasindex=True,create_if_not_exists = True,overwrite=False, 
                 user='master', partitioning=None):
        # tabletype 1: DISK, 2: MEMORY
        """
        Initialize a MongoDB collection handler with specified configuration.
        
        Parameters:
            shareddata (object): Shared resources container, including MongoDB client.
            database (str): Name of the database.
            period (str): Time period identifier for the data.
            source (str): Source identifier for the data.
            tablename (str): Name of the collection.
            hasindex (bool, optional): Whether to create and maintain indexes on the collection. Defaults to True.
            create_if_not_exists (bool, optional): Whether to create the collection if it does not exist. Defaults to True.
            overwrite (bool, optional): Whether to overwrite existing collection data. Defaults to False.
            user (str, optional): MongoDB user or namespace. Defaults to 'master'.
            partitioning (optional): Partitioning scheme or parameter. Defaults to None.
        
        Raises:
            Exception: If the collection does not exist and create_if_not_exists is False.
        
        This constructor sets up the MongoDB collection, creates it if necessary, and manages indexes based on primary key columns and modification time.
        """

        self.shareddata = shareddata
        self.user = user
        self.database = database
        self.period = period
        self.source = source
        self.tablename = tablename
        self.subscription_thread = None
        self.publish_thread = None
        
        self.hasindex = hasindex
        self.overwrite = overwrite
        self.partitioning = partitioning
                
        self._collection = None

        self.mongodb = MongoDBClient(self.user)
        
        self.path = f'{user}/{database}/{period}/{source}/collection/{tablename}'
        self.relpath = f'{database}/{period}/{source}/collection/{tablename}'
        self.pkey_columns = DATABASE_PKEYS[self.database]
        self.exists = self.relpath in self.mongodb.client[self.user].list_collection_names()
        if (not self.exists) and (not create_if_not_exists):
            raise Exception(f'Collection {self.relpath} does not exist')
        
        if not self.exists:
            if self.overwrite:
                self.mongodb.client[self.user].drop_collection(self.relpath)
            # Create collection
            self.mongodb.client[self.user].create_collection(self.relpath)
            self._collection = self.mongodb.client[self.user][self.relpath]
            if self.hasindex:
                pkey_fields = [(f"{field}", ASCENDING) for field in self.pkey_columns]
                pkey_name = '_'.join(f"{field}_1" for field in self.pkey_columns)
                self.mongodb.client[self.user][self.relpath].create_index(pkey_fields, unique=True, name=pkey_name)
                # Create index on mtime for timestamp queries
                self.mongodb.client[self.user][self.relpath].create_index([("mtime", DESCENDING)])
        else:
            self._collection = self.mongodb.client[self.user][self.relpath]
            pkey_fields = [(f"{field}", ASCENDING) for field in self.pkey_columns]
            pkey_name = '_'.join(f"{field}_1" for field in self.pkey_columns)            
            # Get collection indexes information
            index_info = self._collection.index_information()
            # Check for indexes other than the default _id index
            self.hasindex = any(index_name == pkey_name for index_name in index_info)
        
    @property
    def collection(self):
        """
        Property that returns the value of the private attribute `_collection`.
        """
        return self._collection    

    def upsert(self, data):
        """
        Perform upsert operations on the collection, handling single or multiple documents.
        
        This method inserts new documents or updates existing ones based on the primary key columns.
        It supports input as a dictionary, a list of dictionaries, or a pandas DataFrame. Documents missing
        any primary key fields are skipped and logged as errors.
        
        Key features:
        - Validates presence of primary key fields in each document.
        - Removes MongoDB restricted fields like '_id'.
        - Adds or updates the modification time ('mtime') to the current UTC timestamp if not present.
        - Normalizes or floors 'date' fields according to the collection's period setting ('D1', 'M15', 'M1').
        - Cleans field names by removing dots and replacing empty strings with spaces.
        - Performs bulk upsert operations using MongoDB's UpdateOne with upsert=True.
        
        Parameters:
            data (dict, list of dict, or pandas.DataFrame): Document(s) to upsert into the collection.
        
        Returns:
            pymongo.results.BulkWriteResult or list: Result of the bulk write operation if performed,
            otherwise an empty list.
        
        Raises:
            ValueError: If the collection does not have an index, upsert is not supported.
        """
        if not self.hasindex:
            raise ValueError("Upsert operation is not supported for collections without index.")
        
        # If data is a DataFrame, serialize it into a list of dictionaries
        if isinstance(data, pd.DataFrame):
            data = self.df2documents(data)
        # If data is a dictionary, convert it into a list so both cases are handled uniformly
        if isinstance(data, dict):
            data = [data]

        operations = []
        missing_pkey_items = []
        for item in data:
            # Check if the item contains all primary key columns
            if not all(field in item for field in self.pkey_columns):
                missing_pkey_items.append(item)
                continue  # Skip this item if it doesn't contain all primary key columns
            
            # Remove '_id' field if present
            if '_id' in item:
                del item['_id']

            # Add modification time if not present
            if 'mtime' not in item:
                item['mtime'] = pd.Timestamp.utcnow()

            # Check if date needs to be floored to specific intervals
            if 'date' in item:
                if self.period == 'D1':
                    item = item.copy()
                    item['date'] = pd.Timestamp(item['date']).normalize()
                elif self.period == 'M15':
                    item = item.copy()
                    item['date'] = pd.Timestamp(item['date']).floor('15T')                
                elif self.period == 'M1':
                    item = item.copy()
                    item['date'] = pd.Timestamp(item['date']).floor('T')

            # MongoDB does not allow '.' in field names, so replace them with spaces
            item = {k.replace('.', ''): v for k, v in item.items()}
                
            # MongoDB does not allow '' field names, change to ' ' if name == ''
            item = {k if k != '' else ' ': v for k, v in item.items()}

            # Construct the filter condition using the primary key columns
            filter_condition = {field: item[field] for field in self.pkey_columns if field in item}
            
            # Prepare the update operation
            update_data = {'$set': item}

            # Add the upsert operation to the operations list
            operations.append(UpdateOne(filter_condition, update_data, upsert=True))
        
        # Execute all operations in bulk if more than one, otherwise perform single update
        result = []
        if len(operations) > 0:
            # Use ordered=False for parallel execution and better performance
            # PROS: 10-100x faster, parallel execution, better resource utilization
            # CONS: Operations may complete out of order, partial failures more complex
            # Safe for upserts where operations are independent (unique date+symbol pairs)
            try:
                result = self._collection.bulk_write(operations, ordered=False)
                
                # Check for write errors (even with ordered=False, some ops may succeed)
                if hasattr(result, 'bulk_api_result') and result.bulk_api_result.get('writeErrors'):
                    error_count = len(result.bulk_api_result['writeErrors'])
                    Logger.log.warning(f"upsert:{self.relpath} {error_count}/{len(operations)} operations had errors (check for duplicates or constraint violations)")
                    
            except Exception as e:
                Logger.log.error(f"upsert:{self.relpath} bulk_write failed: {e}")
                raise

        if len(missing_pkey_items) > 0:
            Logger.log.error(f"upsert:{self.relpath} {len(missing_pkey_items)}/{len(data)} missing pkey!")
        
        return result
    
    def extend(self, data):
        """
        Appends one or more documents to the collection after preprocessing.
        
        Parameters:
            data (dict, list of dict, or pd.DataFrame): A single document as a dictionary,
                multiple documents as a list of dictionaries, or a DataFrame to be serialized
                into documents.
        
        Raises:
            ValueError: If the collection has an index, as extend operation is not supported.
        
        Behavior:
            - Converts a DataFrame input into a list of dictionaries.
            - Ensures input is a list of documents.
            - Removes the '_id' field from each document if present.
            - Adds a modification timestamp ('mtime') if missing.
            - Normalizes or floors the 'date' field based on the collection's period attribute:
                - 'D1': normalize to midnight.
                - 'M15': floor to nearest 15 minutes.
                - 'M1': floor to nearest minute.
            - Inserts all processed documents into the underlying collection.
        
        Returns:
            The result of the insert_many operation, or an empty list if no documents were inserted.
        """
        if self.hasindex:
            raise ValueError("Extend operation is not supported for collections with index.")
        
        # Check if data is a DataFrame and serialize it into a list of dictionaries
        if isinstance(data, pd.DataFrame):
            data = self.serialize(data)
        # Convert a single dictionary into a list for uniform handling
        if isinstance(data, dict):
            data = [data]

        documents_to_insert = []
        for item in data:
            # Remove '_id' field if present
            if '_id' in item:
                del item['_id']
                
            # Add modification time if not present
            if 'mtime' not in item:
                item['mtime'] = pd.Timestamp.utcnow()
            
            # Check and adjust date if necessary
            if 'date' in item:
                if self.period == 'D1':
                    item = item.copy()
                    item['date'] = pd.Timestamp(item['date']).normalize()
                elif self.period == 'M15':
                    item = item.copy()
                    item['date'] = pd.Timestamp(item['date']).floor('15T')
                elif self.period == 'M1':
                    item = item.copy()
                    item['date'] = pd.Timestamp(item['date']).floor('T')

            documents_to_insert.append(item)

        # Insert all prepared documents into the collection        
        result = []
        if documents_to_insert:
            result = self._collection.insert_many(documents_to_insert)
        
        return result        
    
    def find(self, query, projection=None, sort=None, limit=None, skip=None):
        """
        Retrieve documents from the collection that match the given query criteria.
        
        Args:
            query (dict): A dictionary specifying the filter conditions for the documents.
            projection (dict, optional): A dictionary specifying the fields to include or exclude in the returned documents.
            sort (list, optional): A list of tuples specifying the fields and directions to sort the results by.
            limit (int, optional): The maximum number of documents to return.
            skip (int, optional): The number of documents to skip before returning results.
        
        Returns:
            list: A list of documents matching the query, optionally filtered, sorted, skipped, and limited.
        """
        if projection:
            cursor = self._collection.find(query, projection)
        else:
            cursor = self._collection.find(query)
        
        if sort:
            cursor = cursor.sort(sort)
        elif self.hasindex:
            # If no sort is specified, sort by the primary key(s) to ensure consistent order.
            sort = [(pkey, 1) for pkey in DATABASE_PKEYS[self.database]]
            cursor = cursor.sort(sort)
        elif not self.hasindex:
            # If no sort is specified, sort by the primary key(s) to ensure consistent order.
            sort = {'_id': 1}
            cursor = cursor.sort(sort)

        if skip:
            cursor = cursor.skip(skip)
        
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)
    
    def delete(self, query):
        """
        Delete documents from the collection that match the specified query.
        
        Args:
            query (dict): A dictionary representing the filter criteria for documents to delete.
        
        Returns:
            int: The count of documents that were deleted.
        """
        result = self._collection.delete_many(query)
        return result.deleted_count
    
    @staticmethod
    def serialize(obj, iso_dates=False):
        """
        Recursively serialize a Python object into a nested dictionary or list structure,
        removing any "empty" values as defined by the is_empty() method.
        
        Supports special handling for pandas Timestamps, datetime objects, dictionaries,
        pandas DataFrames, lists, tuples, sets, objects with __dict__, and ObjectId instances.
        
        Parameters:
            obj (any): The Python object to serialize.
            iso_dates (bool): If True, datetime and Timestamp objects are converted to ISO 8601 strings.
        
        Returns:
            dict, list, str, or None: A serialized representation of the input object with empty values removed,
            or None if the entire structure is empty.
        """

        # 1) Special-case Timestamps so they don't get recursed:
        if isinstance(obj, pd.Timestamp):
            # Return None if it's considered 'empty' (e.g. NaT),
            # otherwise treat it as a scalar (string, raw Timestamps, etc.)
            if iso_dates:
                return None if CollectionMongoDB.is_empty(obj) else obj.isoformat()
            else:
                return None if CollectionMongoDB.is_empty(obj) else obj

        # # Handle Python datetime.datetime objects
        if isinstance(obj, datetime.datetime):
            if iso_dates:        
                return None if CollectionMongoDB.is_empty(obj) else obj.isoformat()
            else:
                return None if CollectionMongoDB.is_empty(obj) else obj
        
        # 2) Dict
        if isinstance(obj, dict):
            new_dict = {}
            for k, v in obj.items():
                # Recurse
                serialized_v = CollectionMongoDB.serialize(v, iso_dates)
                # Only keep non-empty values
                if serialized_v is not None and not CollectionMongoDB.is_empty(serialized_v):
                    new_dict[k] = serialized_v

            # If the resulting dict is empty, return None instead of {}
            return new_dict if new_dict else None

        # 3) DataFrame
        if isinstance(obj, pd.DataFrame):
            records = obj.to_dict(orient='records')
            # Each record is a dict, so we re-serialize it
            return [
                r for r in (CollectionMongoDB.serialize(rec, iso_dates) for rec in records)
                if r is not None and not CollectionMongoDB.is_empty(r)
            ]

        # 4) List/tuple/set
        if isinstance(obj, (list, tuple, set)):
            new_list = [
                CollectionMongoDB.serialize(item, iso_dates)
                for item in obj
                if not CollectionMongoDB.is_empty(item)
            ]
            # If the list ends up empty, return None
            return new_list if new_list else None

        # 5) For other objects with __dict__, treat them like a dict
        if hasattr(obj, "__dict__"):
            return CollectionMongoDB.serialize(vars(obj), iso_dates)
        
        # 6) Convert ObjectId to string for JSON serialization
        if isinstance(obj, ObjectId):
            return str(obj)

        # 7) Otherwise, just return the raw value if it's not "empty"
        return obj if not CollectionMongoDB.is_empty(obj) else None

    EMPTY_VALUES = {
        str: ["", "1.7976931348623157E308", "nan", "NaN",],
        int: [2147483647],
        float: [1.7976931348623157e+308, np.nan, np.inf, -np.inf],
        datetime.datetime: [datetime.datetime(1, 1, 1, 0, 0)],
        # pd.Timestamp: [pd.Timestamp("1970-01-01 00:00:00")],
        pd.NaT: [pd.NaT],
        pd.Timedelta: [pd.Timedelta(0)],
        pd.Interval: [pd.Interval(0, 0)],
        type(None): [None],
        bool: [False],
    }
    
    @staticmethod
    def is_empty(value):
        """
        Determine if the given value should be considered empty or a sentinel value.
        
        This method checks for various conditions that signify emptiness, including:
        - Floating point NaN, infinity, zero, and maximum float values.
        - Pandas Timestamp objects that are NaT (Not a Time).
        - Values contained in predefined empty sets specific to their type.
        - Empty containers such as lists, tuples, sets, and dictionaries.
        - Pandas NaTType instances.
        
        Parameters:
            value (any): The value to check for emptiness.
        
        Returns:
            bool: True if the value is considered empty or a sentinel, False otherwise.
        """
        # Special handling for floats
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return True
            if value == 1.7976931348623157e+308:
                return True

        # If it's a Timestamp and is NaT, treat as empty
        if isinstance(value, pd.Timestamp):
            if pd.isna(value):  # True for pd.NaT
                return True

        # Check if value is in our known empty sets
        value_type = type(value)
        if value_type in CollectionMongoDB.EMPTY_VALUES:
            if value in CollectionMongoDB.EMPTY_VALUES[value_type]:
                return True

        # Empty containers
        if isinstance(value, (list, tuple, set)) and len(value) == 0:
            return True
        if isinstance(value, dict) and len(value) == 0:
            return True
        if isinstance(value, pd._libs.tslibs.nattype.NaTType):
            return True

        return False

    def flatten_dict(self, d, parent_key='', sep='->'):
        """
        Recursively flattens a nested dictionary by concatenating keys with a specified separator.
        
        Parameters:
            d (dict): The dictionary to flatten.
            parent_key (str, optional): The base key string to prepend to keys during recursion. Defaults to ''.
            sep (str, optional): The separator string used between concatenated keys. Defaults to '->'.
        
        Returns:
            dict: A new dictionary with nested keys flattened into single-level keys joined by the separator.
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def documents2df(self, documents, flatten=True, drop_empty=True, serialize=True):
        """
        Convert a list of document dictionaries into a pandas DataFrame.
        
        Parameters:
            documents (list): A list of dictionaries representing documents.
            flatten (bool): If True, flatten nested dictionaries within each document. Default is True.
            drop_empty (bool): If True, drop columns that contain only None values. Default is True.
            serialize (bool): If True, serialize ObjectId and datetime objects before processing. Default is True.
        
        Returns:
            pandas.DataFrame: A DataFrame representation of the documents, with optional flattening,
            serialization, and empty column removal. If primary key columns are present, they are set as the DataFrame index.
        """
        if len(documents) == 0:
            return pd.DataFrame()
        # Serialize ObjectId and datetime objects
        if serialize:
            documents = self.serialize(documents)
        # Flatten each document
        if flatten:
            documents = [self.flatten_dict(doc) for doc in documents]
        
        # Convert the list of dictionaries into a DataFrame 
        df = pd.DataFrame(documents)
        
        if drop_empty:
            # Remove columns with all None values
            df = df.dropna(axis=1, how='all')
        
        # Set primary key as index        
        pkey_columns = DATABASE_PKEYS[self.database]
        if all(col in df.columns for col in pkey_columns):
            df.set_index(pkey_columns, inplace=True)

        return df
    
    def df2documents(self, df, unflatten=True, drop_empty=True):
        """
        Convert a pandas DataFrame into a list of dictionary documents suitable for MongoDB insertion.
        
        Parameters:
            df (pandas.DataFrame): The DataFrame to convert.
            unflatten (bool, optional): If True, unflatten nested keys in the documents. Defaults to True.
            drop_empty (bool, optional): If True, drop rows and columns that are completely empty and remove empty fields from documents. Defaults to True.
        
        Returns:
            list of dict: A list of documents representing the DataFrame rows, with primary key validation, cleaned column names, and optional unflattening.
        
        Raises:
            ValueError: If the DataFrame's primary key columns do not match the expected primary key columns for the database.
        """
        if df.empty:
            return []
        # Retrieve the expected primary key columns for this database
        pkey_columns = DATABASE_PKEYS[self.database]
        # Convert index to columns
        df = df.reset_index()
        if len(df.columns) >= len(pkey_columns):
            for icol, col in enumerate(pkey_columns):
                if df.columns[icol]!=pkey_columns[icol]:
                    raise ValueError(f"df2documents:Expected primary key column {pkey_columns}!")


        # MongoDB does not allow '.' in field names, so replace them with spaces
        df.columns = [str(s).replace('.','') for s in df.columns]

        # Drop rows and columns with all None/NaN values
        if drop_empty:
            df = df.dropna(axis=0, how='all').dropna(axis=1, how='all')

        # Convert DataFrame to list of dictionaries
        documents = df.to_dict(orient='records')

        if drop_empty:
            # Remove empty fields in the documents
            for doc in documents:
                keys_to_remove = [key for key, value in doc.items() if CollectionMongoDB.is_empty(value)]
                for key in keys_to_remove:
                    del doc[key]

        # Unflatten the documents if needed
        if unflatten:
            documents = [self.unflatten_dict(doc) for doc in documents]

        return documents
    
    def unflatten_dict(self, d, sep='->'):
        """
        Convert a flat dictionary with compound keys into a nested dictionary.
        
        Each key in the input dictionary `d` is split by the specified separator `sep` to create a hierarchy of nested dictionaries. The values are assigned to the innermost keys.
        
        Parameters:
            d (dict): The flat dictionary with compound keys.
            sep (str): The separator string used to split keys into nested levels. Default is '->'.
        
        Returns:
            dict: A nested dictionary constructed from the flat dictionary.
        """
        result = {}
        for key, value in d.items():
            parts = key.split(sep)
            current = result
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                    current = current[part]

                else:
                    if not isinstance(current[part], dict):
                        current[part] = {}
                    current = current[part]
            current[parts[-1]] = value
        return result
            
    def documents2json(self, documents, serialize=True, drop_empty=True):
        """
        Convert a list of document dictionaries to a JSON string.
        
        This method optionally serializes special data types such as ObjectId and datetime
        to JSON-compatible formats and can remove keys with empty values from each document.
        
        Parameters:
            documents (list): A list of document dictionaries to be converted.
            serialize (bool): If True, serialize special types like ObjectId and datetime to JSON-compatible formats. Default is True.
            drop_empty (bool): If True, remove keys with empty values from each document before conversion. Default is True.
        
        Returns:
            str: A JSON-formatted string representing the list of documents.
        """
        if len(documents) == 0:
            return json.dumps([])
        # Serialize ObjectId and datetime objects
        if serialize:
            documents = self.serialize(documents, iso_dates=True)

        if drop_empty:
            # Remove empty fields in the documents
            for doc in documents:
                keys_to_remove = [key for key, value in doc.items() if CollectionMongoDB.is_empty(value)]
                for key in keys_to_remove:
                    del doc[key]

        return json.dumps(documents)

    def recursive_update(self, original, updates):
        """
        Recursively updates the original dictionary with values from the updates dictionary.
        
        For each key in updates:
        - If the corresponding value is a dictionary and the original dictionary has a dictionary at that key,
          the update is applied recursively.
        - Otherwise, the value from updates overwrites the value in the original dictionary.
        
        This method preserves keys in the original dictionary that are not present in updates.
        
        Args:
            original (dict): The dictionary to be updated.
            updates (dict): The dictionary containing updates.
        
        Returns:
            dict: The updated original dictionary.
        """
        for key, value in updates.items():
            if isinstance(value, dict):
                # Get existing nested dictionary or use an empty dict if not present
                original_value = original.get(key, {})
                if isinstance(original_value, dict):
                    # Merge recursively
                    original[key] = self.recursive_update(original_value, value)
                else:
                    # Directly assign if original is not a dict
                    original[key] = value
            else:
                # Non-dict values are directly overwritten
                original[key] = value
        return original
        