from fnmatch import fnmatch
import pandas as pd
import numpy as np
import time
import os
import queue
from redis import Redis
from redis.cluster import RedisCluster, ClusterNode
from redis.asyncio import Redis as RedisAsync
from redis.asyncio.cluster import RedisCluster as RedisClusterAsync
from redis.asyncio.cluster import ClusterNode as ClusterNodeAsync
from redis.exceptions import WatchError    
from typing import Set, Dict
import bson
import asyncio

from datetime import datetime, timezone

from SharedData.Logger import Logger
from SharedData.Database import DATABASE_PKEYS

class CacheRedis:
    """
    A Redis-backed cache manager supporting synchronous and asynchronous operations with BSON-encoded data.
    
    This class provides an interface to store, retrieve, update, and manage cached data entries in a Redis or Redis Cluster environment. It uses a structured key namespace based on database, period, source, and table name, ensuring keys are grouped for cluster slot affinity.
    
    Features:
    - Initialization connects to Redis or Redis Cluster based on environment configuration.
    - Supports single and multiple key retrieval with automatic BSON decoding.
    - Maintains a local cache dictionary for quick access.
    - Provides recursive dictionary merging for updates to preserve nested data.
    - Supports asynchronous batch updates via an internal queue and flush loop.
    - Manages a Redis set of primary keys for efficient key listing and scanning.
    - Implements concurrency-safe updates using Redis transactions and WATCH.
    - Allows clearing the entire cache and associated metadata.
    - Supports iteration over cached keys.
    
    Attributes:
        database (str): Database name.
        period (str): Period identifier.
        source (str): Data source identifier.
        tablename (str): Table name.
        user (str): User identifier, defaults to 'master'.
        path (str): Redis key prefix path for this cache.
        data (dict): Local in-memory cache of decoded data.
        queue (asyncio
    """
    def __init__(self, database, period, source, tablename, user='master'):
        """
        Initialize a RedisCluster connection and set up caching parameters.
        
        Parameters:
            database (str): The name of the database.
            period (str): The time period for the cache.
            source (str): The data source identifier.
            tablename (str): The name of the table to cache.
            user (str, optional): The user name, defaults to 'master'.
        
        Raises:
            Exception: If the environment variable 'REDIS_CLUSTER_NODES' is not defined.
        
        Initializes:
            - Redis or RedisCluster connections (synchronous and asynchronous) based on environment configuration.
            - Cache path and internal data structures.
            - Cache header and primary key columns.
            - Asyncio queue and lock for managing cache flush operations.
        """
        self.database = database
        self.period = period
        self.source = source
        self.tablename = tablename
        self.user = user

        self.path = f'{user}/{database}/{period}/{source}/cache/{tablename}'
        self.data = {}                
        self.queue = asyncio.Queue()
        self._flush_task = None
        self._flush_lock = asyncio.Lock()        
        self.pkeycolumns = DATABASE_PKEYS[database]
        self.mtime = datetime(1970,1,1, tzinfo=timezone.utc)

        if not 'REDIS_CLUSTER_NODES' in os.environ:
            raise Exception('REDIS_CLUSTER_NODES not defined')
        startup_nodes = []
        for node in os.environ['REDIS_CLUSTER_NODES'].split(','):
            startup_nodes.append( (node.split(':')[0], int(node.split(':')[1])) )
        if len(startup_nodes)>1:
            startup_nodes = [ClusterNode(node[0], int(node[1])) 
                             for node in startup_nodes]
            self.redis = RedisCluster(startup_nodes=startup_nodes, decode_responses=False)            
            self.redis_async = RedisClusterAsync(startup_nodes=startup_nodes, decode_responses=False)
        else:
            node = startup_nodes[0]
            host, port = node[0], int(node[1])
            self.redis = Redis(host=host, port=port, decode_responses=False)
            self.redis_async = RedisAsync(host=host, port=port, decode_responses=False)

        self.header = CacheHeader(self)

        if not self.header['cache->counter']:
            self.header['cache->counter'] = 0

        self.set_pkeys = f"{{{self.path}}}#pkeys"
                
    def __getitem__(self, pkey):
        """
        Retrieve the value associated with the given primary key from Redis.
        
        Parameters:
            pkey (str): The primary key to look up. Must be a string and cannot contain the '#' character.
        
        Returns:
            dict: The decoded BSON object stored in Redis for the given key, or an empty dictionary if the key does not exist.
        
        Raises:
            Exception: If pkey is not a string or contains the '#' character.
        """
        if not isinstance(pkey, str):
            raise Exception('pkey must be a string')
        if '#' in pkey:
            raise Exception('pkey cannot contain #')
        _bson = self.redis.get(self.get_hash(pkey))
        if _bson is None:
            return {}
        value = bson.BSON.decode(_bson)        
        self.data[pkey] = value
        return value
    
    def get(self, pkey):        
        """
        Retrieve the item associated with the given primary key.
        
        Parameters:
        pkey: The primary key used to identify the item to retrieve.
        
        Returns:
        The item corresponding to the specified primary key.
        
        This method is a wrapper around the __getitem__ method, allowing
        access to items using the get method interface.
        """
        return self.__getitem__(pkey)
    
    def mget(self, pkeys: list[str]) -> list[dict]:
        """
        Retrieve multiple entries from Redis using a list of primary keys.
        
        Each primary key is converted to a Redis hash key, and the corresponding values are fetched in a single Redis MGET call. The returned list contains decoded dictionaries for each key; if a key is missing in Redis, an empty dictionary is returned in its place. The internal cache `self.data` is updated with the retrieved values.
        
        :param pkeys: List of primary keys as strings. Keys must not contain the '#' character.
        :return: List of dictionaries corresponding to the retrieved entries. Empty dicts represent missing keys.
        :raises Exception: If `pkeys` is not a list or contains keys with '#'.
        """
        if len(pkeys) == 0:
            return []
        if not isinstance(pkeys, list):
            raise Exception('pkeys must be a list of strings')
        if any('#' in pkey for pkey in pkeys):
            raise Exception('pkeys cannot contain #')        
        redis_keys = [self.get_hash(pkey) for pkey in pkeys]
        vals = self.redis.mget(redis_keys)
        result = []
        for pkey, _bson in zip(pkeys, vals):
            if _bson is None:
                result.append({})
            else:
                value = bson.BSON.decode(_bson)
                self.data[pkey] = value
                result.append(value)
        return result

    def load(self) -> dict:
        """
        Load all data from Redis into the cache dictionary.
        
        This method retrieves all keys matching the pattern '*' from Redis,
        fetches their corresponding values efficiently using the mget command,
        and stores the results in the cache dictionary.
        
        Returns:
            dict: A dictionary containing all key-value pairs loaded from Redis.
        """
        pkeys = self.list_keys('*')
        self.mget(pkeys)
        return self.data

    def get_pkey(self, value):
        """
        Generate a primary key string by concatenating the values of specified columns.
        
        The method extracts the values from the input `value` dictionary for the columns
        listed in `self.pkeycolumns` that are among 'symbol', 'portfolio', or 'tag'.
        These values are converted to strings and joined with commas to form the key.
        
        Parameters:
            value (dict): A dictionary containing column-value pairs.
        
        Returns:
            str: A comma-separated string representing the primary key.
        """
        key_parts = [
            str(value[col])
            for col in self.pkeycolumns
            if col in ['symbol','portfolio','tag']
        ]        
        return ','.join(key_parts)

    def get_hash(self, pkey: str) -> str:
        """
        Generate a Redis key by combining the instance's path attribute and the provided pkey,
        enclosed in curly braces to ensure keys with the same path hash to the same Redis cluster slot.
        
        Args:
            pkey (str): The partial key to append to the path.
        
        Returns:
            str: The full Redis key formatted as "{path}:pkey".
        """
        return f"{{{self.path}}}:{pkey}"
     
    def update_keys(self, keyword='*', count=None):
        """
        Scan Redis keys matching the pattern "{self.path}:<pkey>" and update the set of pkeys for consistency.
        
        Args:
            keyword (str): Pattern for matching the pkey part of the keys (supports wildcards, defaults to '*').
            count (int or None): Batch size for scanning keys. If None, the default scan count is used.
        
        Returns:
            list: A list of pkeys that were added to the set.
        
        This method scans all keys in Redis that match the pattern formed by combining self.path and the keyword.
        It collects the pkeys from these keys, clears the existing set of pkeys stored at self.set_pkeys,
        and adds the collected pkeys to this set in a single operation for efficiency.
        """

        pattern = f"{{{self.path}}}:{keyword}"
        result = []
        
        # Gather the pkeys to add
        scan_iter_kwargs = {'match': pattern}
        if count is not None:
            scan_iter_kwargs['count'] = count

        for key in self.redis.scan_iter(**scan_iter_kwargs):
            # key may be bytes
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            parts = key.split(':', 1)
            if len(parts) > 1:
                pkey = parts[1]
                result.append(pkey)

        # Add all the pkeys to the set in one command for efficiency
        self.redis.delete(self.set_pkeys)
        if result:
            self.redis.sadd(self.set_pkeys, *result)

        return result
    
    def list_keys(self, keyword='*', count=None):
        """
        Retrieve a list of primary keys from the Redis set, optionally filtered by a keyword pattern.
        
        Parameters:
            keyword (str): A pattern to filter keys, supports '*' as a wildcard. Defaults to '*' (no filtering).
            count (int or None): Maximum number of keys to return. If None, returns all matching keys.
        
        Returns:
            list: A list of decoded string keys matching the filter criteria, limited by count if specified.
        """
        # Get all pkeys (members of the set)
        keys = self.redis.smembers(self.set_pkeys)
        # smembers returns bytes, so decode
        decoded_keys = [k.decode('utf-8') if isinstance(k, bytes) else k for k in keys]
        
        # Replace '*' with real wildcard filter
        if keyword == '*' or not keyword:
            filtered_keys = decoded_keys
        else:
            filtered_keys = [k for k in decoded_keys if fnmatch(k, keyword)]

        # Respect the count argument if present
        if count is not None:
            filtered_keys = filtered_keys[:count]

        return filtered_keys

    # def __setitem__(self, pkey, new_value):
    #     if ':' in pkey:
    #         raise Exception('pkey cannot contain :')
    #     if pkey in self.data:
    #         self.data[pkey] = self.recursive_update(self.data[pkey],new_value)
    #     else:
    #         self.data[pkey] = new_value
    #     _bson = bson.BSON.encode(self.data[pkey])
    #     self.redis.set(self.get_hash(pkey), _bson)
    #     self.redis.sadd(self.set_pkeys, pkey)

    
    def __setitem__(self, pkey, new_value):
        """
        Set the value associated with the given primary key in a Redis-backed store with optimistic concurrency control.
        
        Parameters:
            pkey (str): The primary key to set. Must be a string and cannot contain ':' or '#'.
            new_value (dict): The new value to merge with the existing value stored under the key.
        
        Raises:
            Exception: If `pkey` is not a string or contains invalid characters.
            Exception: If the value cannot be set after multiple concurrent update retries.
        
        This method attempts to update the stored value for `pkey` by merging `new_value` with the existing value in Redis.
        It uses a Redis transaction with WATCH to handle concurrent writes, retrying up to 16 times in case of conflicts.
        On successful update, the merged value is also cached locally.
        """
        if not isinstance(pkey, str):
            raise Exception('pkey must be a string')
        if ':' in pkey or '#' in pkey:
            raise Exception('pkey cannot contain : or #')

        rhash = self.get_hash(pkey)

        # Retry on concurrent writers
        for _ in range(16):
            # Use transactional pipeline so WATCH is supported in RedisCluster
            pipe = self.redis.pipeline(transaction=True)
            try:
                pipe.watch(rhash)
                prev = pipe.get(rhash)
                current = bson.BSON.decode(prev) if prev else {}

                # Merge with the latest value from Redis (not only local cache)
                merged = (self.recursive_update(current, new_value)
                          if current else dict(new_value))

                _bson = bson.BSON.encode(merged)

                pipe.multi()
                pipe.set(rhash, _bson)
                pipe.sadd(self.set_pkeys, pkey)  # same hash tag => same slot
                pipe.execute()

                # Commit to local cache after successful write
                self.data[pkey] = merged
                return
            except WatchError:
                # Key changed; retry
                try:
                    pipe.reset()
                except Exception:
                    pass
                continue
            finally:
                try:
                    pipe.reset()
                except Exception:
                    pass

        raise Exception('Concurrent update conflict: failed to set value after retries')
    
    def recursive_update(self, original, updates):
        """
        Recursively updates the original dictionary with values from the updates dictionary.
        
        For each key in updates:
        - If the corresponding value is a dictionary and the original dictionary has a dictionary at that key,
          the function recursively merges the nested dictionaries.
        - Otherwise, the value from updates overwrites the value in the original dictionary.
        
        This method preserves keys in the original dictionary that are not present in updates,
        performing a deep merge rather than a shallow overwrite.
        
        Parameters:
            original (dict): The dictionary to be updated.
            updates (dict): The dictionary containing updates.
        
        Returns:
            dict: The updated original dictionary after merging.
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

    def set(self, new_value, pkey=None):
        """
        Sets the value associated with a primary key in the container.
        
        If the primary key (`pkey`) is not provided, it is determined by calling `self.get_pkey(new_value)`.
        The method then stores `new_value` in the container using the primary key.
        
        Parameters:
            new_value: The value to be stored.
            pkey (optional): The primary key under which to store the value. If None, it will be derived from `new_value`.
        """
        if pkey is None:
            pkey = self.get_pkey(new_value)
        self.__setitem__(pkey, new_value)

    async def async_set(self, new_value):
        """
        Asynchronously updates the cache with a new value and triggers the flush loop if not already running.
        
        If the new value is a list, each item is enqueued individually; otherwise, the single value is enqueued.
        
        This method ensures that only one flush task runs at a time by acquiring a lock before starting the flush loop.
        
        Raises:
            Exception: If any error occurs during the enqueueing or task creation process.
        """
        async with self._flush_lock:
            if self._flush_task is None or self._flush_task.done():
                self._flush_task = asyncio.create_task(self.async_flush_loop())
        
        if isinstance(new_value, list):
            for item in new_value:
                await self.queue.put(item)
        else:
            await self.queue.put(new_value)
        
    # async def async_flush_loop(self, conflate_ms = 50) -> None:
    #     """Flush the queue to Redis asynchronously."""        
    #     try:
    #         while True:            
    #             flush_pkeys = set()
                
    #             new_value = await self.queue.get()

    #             tini = time.time_ns()

    #             pkey = self.get_pkey(new_value)
    #             flush_pkeys.add(pkey)
    #             if pkey in self.data:
    #                 self.data[pkey] = self.recursive_update(self.data[pkey], new_value)
    #             else:
    #                 self.data[pkey] = new_value
                                
    #             # Keep draining the queue until empty
    #             while not self.queue.empty() and (time.time_ns() - tini) < conflate_ms * 1_000_000:
    #                 new_value = await self.queue.get()
    #                 pkey = self.get_pkey(new_value)
    #                 flush_pkeys.add(pkey)
    #                 if pkey in self.data:
    #                     self.data[pkey] = self.recursive_update(self.data[pkey], new_value)
    #                 else:
    #                     self.data[pkey] = new_value
                                                    
    #             pipe = self.redis_async.pipeline()
    #             try:
    #                 for pkey in flush_pkeys:
    #                     rhash = self.get_hash(pkey)
    #                     _bson = bson.BSON.encode(self.data[pkey])
    #                     pipe.set(rhash, _bson)  
    #                 pipe.sadd(self.set_pkeys, *flush_pkeys)
    #                 await pipe.execute()                    
    #             except Exception as e:
    #                 Logger.log.error(f"Redis pipeline error: {e}")
    #             finally:
    #                 await pipe.reset()
    #             await self.header.async_incrby("cache->counter", len(flush_pkeys))
    #     except Exception as e:
    #         Logger.log.error(f"Error in async_flush_loop: {e}")

    async def async_flush_loop(self, conflate_ms = 50) -> None:
        """
        Asynchronously flushes updates from an internal queue to Redis, batching multiple updates within a specified conflation window.
        
        This coroutine continuously processes items from an asynchronous queue, merges updates by primary key, and writes the consolidated data to Redis using a pipeline for efficiency. It ensures local cache consistency by loading keys before updating and handles exceptions during Redis operations gracefully.
        
        Parameters:
            conflate_ms (int): The time window in milliseconds to batch multiple queue items before flushing to Redis. Defaults to 50 ms.
        
        Returns:
            None
        """
        try:
            while True:            
                flush_pkeys = set()
                get_pkeys = set()
                
                new_value = await self.queue.get()

                tini = time.time_ns()

                pkey = self.get_pkey(new_value)
                flush_pkeys.add(pkey)
                get_pkeys.add(pkey)
                self.__getitem__(pkey)  # Ensure the key is loaded into local cache
                if pkey in self.data:
                    self.data[pkey] = self.recursive_update(self.data[pkey], new_value)
                else:
                    self.data[pkey] = new_value
                                
                # Keep draining the queue until empty
                while not self.queue.empty() and (time.time_ns() - tini) < conflate_ms * 1_000_000:                    
                    new_value = await self.queue.get()
                    pkey = self.get_pkey(new_value)
                    flush_pkeys.add(pkey)
                    if not pkey in get_pkeys:
                        get_pkeys.add(pkey)
                        self.__getitem__(pkey)
                    if pkey in self.data:
                        self.data[pkey] = self.recursive_update(self.data[pkey], new_value)
                    else:
                        self.data[pkey] = new_value
                                                    
                pipe = self.redis_async.pipeline()
                try:
                    for pkey in flush_pkeys:
                        rhash = self.get_hash(pkey)
                        _bson = bson.BSON.encode(self.data[pkey])
                        pipe.set(rhash, _bson)  
                    pipe.sadd(self.set_pkeys, *flush_pkeys)
                    await pipe.execute()                    
                except Exception as e:
                    Logger.log.error(f"Redis pipeline error: {e}")
                finally:
                    await pipe.reset()
                await self.header.async_incrby("cache->counter", len(flush_pkeys))
        except Exception as e:
            Logger.log.error(f"Error in async_flush_loop: {e}")

    def __delitem__(self, pkey: str):
        """
        Delete the item identified by the primary key from the Redis store.
        
        This method removes the hash associated with the given primary key from Redis,
        and also removes the primary key from the set of all primary keys.
        
        Args:
            pkey (str): The primary key of the item to delete.
        """
        self.redis.delete(self.get_hash(pkey))
        self.redis.srem(self.set_pkeys, pkey)

    def clear(self):
        """
        Clear all cached data both in Redis and the local cache.
        
        This method performs the following steps:
        1. Retrieves all primary keys (pkeys) from the cache.
        2. Deletes all associated Redis hash keys in batches of 1000 to avoid command size limits.
        3. Deletes the Redis set that stores all pkeys.
        4. Clears the local in-memory cache dictionary.
        5. Deletes all Redis hash keys associated with cached headers.
        
        This ensures that the entire cache, including headers and data, is fully cleared.
        """
        # Get all pkeys
        pkeys = self.list_keys('*')
        # Delete all redis hash keys
        if pkeys:
            redis_keys = [self.get_hash(pkey) for pkey in pkeys]
            for i in range(0, len(redis_keys), 1000):
                self.redis.delete(*redis_keys[i:i+1000])
        # Delete the set of pkeys itself
        self.redis.delete(self.set_pkeys)
        # Clear local cache
        self.data = {}
        header_keys = list(self.header)
        if header_keys:
            redis_header_keys = [self.header.get_hash(k) for k in header_keys]
            self.redis.delete(*redis_header_keys)
    
    def __iter__(self):
        """
        Iterate over the keys in the collection.
        
        Yields:
            Each key obtained from the list_keys() method, one at a time.
        """
        for key in self.list_keys():
            yield key
       
class CacheHeader():    
    """
    A dictionary-like interface for managing cached headers stored in Redis.
    
    This class provides methods to get, set, delete, and iterate over cached header values using Redis as the backend storage. Keys are namespaced using a hash format based on the cache path and the provided key.
    
    Attributes:
        cache: An object containing Redis clients (`redis` for synchronous and `redis_async` for asynchronous operations) and a `path` attribute used for key namespacing.
    
    Methods:
        get_hash(pkey: str) -> str:
            Constructs a Redis key by combining the cache path and the provided key.
    
        __getitem__(pkey: str):
            Retrieves the value associated with the given key from Redis.
    
        get(pkey: str, default=None):
            Retrieves the value for the given key, returning a default if the key does not exist.
    
        __setitem__(pkey: str, value):
            Sets the value for the given key in Redis.
    
        set(pkey, value):
            Sets the value for the given key in Redis.
    
        __delitem__(pkey: str):
            Deletes the given key from Redis.
    
        __iter__():
            Iterates over all keys stored in Redis under the current cache path.
    
        incrby(field, value):
    """
    def __init__(self, cache):
        """
        Initializes the instance with a given cache.
        
        Parameters:
            cache (any): The cache object to be stored in the instance.
        """
        self.cache = cache

    def get_hash(self, pkey: str) -> str:
        """
        Generate a hash string combining the cache path and a provided key.
        
        Parameters:
        pkey (str): The key to be appended to the cache path.
        
        Returns:
        str: A string in the format "{cache_path}#pkey", where cache_path is the path attribute of the cache.
        """
        return f"{{{self.cache.path}}}#{pkey}"

    def __getitem__(self, pkey: str):
        """
        Retrieve the value associated with the given primary key from the Redis cache.
        
        Parameters:
        pkey (str): The primary key used to generate the hash for retrieving the cached value.
        
        Returns:
        The value stored in the Redis cache corresponding to the hashed primary key, or None if the key does not exist.
        """
        val = self.cache.redis.get(self.get_hash(pkey))
        return val
    
    def get(self, pkey: str, default=None):
        """
        Retrieve the value associated with the given header key.
        
        Parameters:
            pkey (str): The key of the header to retrieve.
            default (optional): The value to return if the key is not found. Defaults to None.
        
        Returns:
            The value corresponding to the header key if it exists; otherwise, returns the default value.
        """
        val = self.__getitem__(pkey)
        return val if val is not None else default

    def __setitem__(self, pkey: str, value):
        """
        Set the value of a header identified by the given primary key.
        
        Parameters:
        pkey (str): The primary key of the header to set.
        value: The value to associate with the specified header key.
        
        This method stores the value in the Redis cache using a hashed version of the primary key.
        """
        self.cache.redis.set(self.get_hash(pkey), value)

    def set(self, pkey, value):
        """
        Set a header value in the Redis cache using the provided primary key.
        
        Parameters:
        pkey (str): The primary key used to generate the hash key for storing the value.
        value (str): The value to be stored in the cache.
        
        Returns:
        None
        """
        self.cache.redis.set(self.get_hash(pkey), value)

    def __delitem__(self, pkey: str):
        """
        Delete the header associated with the given primary key from the Redis cache.
        
        Parameters:
        pkey (str): The primary key of the header to be deleted.
        """
        self.cache.redis.delete(self.get_hash(pkey))

    def __iter__(self):
        """
        Iterate over header keys stored in the Redis cache.
        
        Generates header keys by scanning the Redis keys that match the pattern
        constructed from the cache path, decoding them if necessary, and extracting
        the portion after the '#' character.
        
        Yields:
            str: Each header key found in the Redis cache.
        """
        pattern = f"{{{self.cache.path}}}#*"
        for key in self.cache.redis.scan_iter(match=pattern):
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            _, header_key = key_str.split('#', 1)
            yield header_key
    
    def incrby(self, field, value):
        """
        Increment the integer value of a hash field by the given amount in the Redis cache.
        
        Parameters:
            field (str): The field name whose value is to be incremented.
            value (int): The amount by which to increment the field's value.
        
        Returns:
            None
        """
        _pkey = self.get_hash(field)
        self.cache.redis.incrby(_pkey,value)
    
    async def async_incrby(self, field, value):
        """
        Asynchronously increments the integer value of a hash field by the given amount.
        
        Args:
            field (str): The field name within the hash to increment.
            value (int): The amount by which to increment the field's value.
        
        Returns:
            None
        """
        _pkey = self.get_hash(field)
        await self.cache.redis_async.incrby(_pkey,value)
    
    def list_keys(self, keyword = '*', count=None):
        # keys look like {self.path}:pkey
        """
        Retrieve a list of keys from the Redis cache matching a specified pattern.
        
        Args:
            keyword (str): Pattern to match keys against, supports wildcards. Defaults to '*'.
            count (int, optional): Maximum number of keys to return. If None, returns all matching keys.
        
        Returns:
            list: A list of key suffixes (pkey) extracted from the matched Redis keys.
        
        Notes:
            The keys in Redis are expected to have the format '{path}#pkey', where 'path' is derived from self.cache.path.
            The method scans Redis keys matching the pattern '{path}#{keyword}' and extracts the part after the '#' character.
        """
        pattern = f"{{{self.cache.path}}}#{keyword}"
        result = []
        if count is None:
            for key in self.cache.redis.scan_iter(match=pattern):
                # Extract pkey part after colon
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                # {user/db/period/source/cache/table}:pkey            
                parts = key.split('#', 1)
                if len(parts) > 1:
                    result.append(parts[1])
        else:
            for key in self.cache.redis.scan_iter(match=pattern,count=count):
                # Extract pkey part after colon
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                # {user/db/period/source/cache/table}:pkey            
                parts = key.split('#', 1)
                if len(parts) > 1:
                    result.append(parts[1])

        return result
