import os
import pymongo
from pymongo import MongoClient
from pymongo.collection import Collection

class MongoDBClient:
    """
    MongoDBClient is a handler for managing MongoDB connections safely in forking environments.
    It lazily initializes the MongoClient to avoid fork-safety warnings and supports optimized
    connection strings for both single server and replica set configurations with automatic
    retry on failover. Provides dictionary-like access to collections within a specified user
    namespace and includes a method to execute operations with automatic retry on connection
    failures. Also includes a static method to ensure the existence of a specific index on a collection.
    """

    def __init__(self, user: str = 'SharedData') -> None:
        """
        Initialize MongoDB client handler by constructing the appropriate connection string.
        
        This constructor sets up the MongoDB connection string based on environment variables.
        If the environment variable 'MONGODB_REPLICA_SET' is not present, it creates a connection
        string for a single MongoDB server. Otherwise, it creates a connection string optimized
        for a replica set with failover and retry options enabled.
        
        Args:
            user (str): The database user namespace. Defaults to 'SharedData'.
        
        Attributes:
            _user (str): The user namespace for the database.
            mongodb_conn_str (str): The constructed MongoDB connection string.
            _client: Placeholder for the MongoDB client instance, initialized on first use.
        """
        self._user = user
        mongodb_host = os.environ["MONGODB_HOST"]
        if not ':' in mongodb_host:
            mongodb_host += ':' + os.environ.get("MONGODB_PORT", "27017")

        if not 'MONGODB_REPLICA_SET' in os.environ:
            # Single server connection (MONGODB_HOST includes port: '10.0.0.50:27017')
            self.mongodb_conn_str = (
                f'mongodb://{os.environ["MONGODB_USER"]}:'
                f'{os.environ["MONGODB_PWD"]}@'
                f'{mongodb_host}/'
                f'?retryWrites=true'  # Automatically retry writes on failover
                f'&retryReads=true'  # Automatically retry reads on failover
            )
        else:
            # Replica set connection string optimized for fast failover with aggressive timeouts
            self.mongodb_conn_str = (
                f'mongodb://{os.environ["MONGODB_USER"]}:'
                f'{os.environ["MONGODB_PWD"]}@'
                f'{mongodb_host}/'
                f'?replicaSet={os.environ["MONGODB_REPLICA_SET"]}'
                f'&authSource={os.environ["MONGODB_AUTH_DB"]}'
                f'&retryWrites=true'  # Automatically retry writes on failover
                f'&retryReads=true'  # Automatically retry reads on failover
                f'&readPreference=primary'  # REQUIRED: Force reads from primary only
                f'&w=1'  # REQUIRED: Write to primary only (explicit override)
                f'&serverSelectionTimeoutMS=10000'  # Allow time for failover detection
            )
        self._client = None  # Client will be created on first access
        self._pid = None  # Track process ID for fork detection

    @property
    def client(self) -> MongoClient:
        """
        Lazily initialize the MongoClient for this process with fork detection.
        
        Ensures process-safety by detecting fork events (when Gunicorn creates worker processes)
        and creating a new client instance per process. This prevents sharing MongoDB connections
        across processes, which would cause errors. PyMongo's built-in connection pool (default 100
        connections) is automatically process-safe with this pattern.
        """
        current_pid = os.getpid()
        
        # Detect if we're in a new process (fork event) or client hasn't been created yet
        if self._client is None or self._pid != current_pid:
            # Close old client if it exists (from parent process)
            if self._client is not None:
                try:
                    self._client.close()
                except:
                    pass  # Ignore errors closing stale client
            
            # Create new client for this process with built-in connection pooling
            self._client = MongoClient(
                self.mongodb_conn_str,
                connect=False,  # Delay connection until first operation (lazy)
            )
            self._pid = current_pid
        
        return self._client

    @client.setter
    def client(self, value: MongoClient) -> None:
        """
        Set the MongoDB client instance.
        
        Parameters:
            value (MongoClient): An instance of MongoClient to be used as the database client.
        
        Returns:
            None
        """
        self._client = value

    def __getitem__(self, collection_name: str) -> Collection:
        """
        Retrieve a MongoDB collection from the user's database using dictionary-like access.
        
        Args:
            collection_name (str): The name of the collection to access.
        
        Returns:
            Collection: The MongoDB collection corresponding to the given name.
        """
        return self.client[self._user][collection_name]
    
    def execute_with_retry(self, operation, max_retries: int = 3, delay: float = 0.5):
        """
        Execute a MongoDB operation with automatic retries on connection-related failures.
        
        This method attempts to execute the provided MongoDB operation callable. If the operation
        raises a connection-related exception (such as ServerSelectionTimeoutError, NetworkTimeout,
        or AutoReconnect), it will retry the operation up to `max_retries` times with exponential
        backoff delay between attempts. On each retry, the MongoDB client is closed and reset to
        force a fresh connection.
        
        Args:
            operation (callable): A callable that performs the MongoDB operation.
            max_retries (int, optional): Maximum number of retry attempts. Defaults to 3.
            delay (float, optional): Initial delay between retries in seconds. Defaults to 0.5.
        
        Returns:
            The result of the MongoDB operation if successful.
        
        Raises:
            Exception: Re-raises the last connection-related exception if all retries fail.
            Exception: Immediately raises any non-connection-related exceptions encountered during operation.
        """
        import time
        
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                return operation()
            except (pymongo.errors.ServerSelectionTimeoutError, 
                    pymongo.errors.NetworkTimeout,
                    pymongo.errors.AutoReconnect) as e:
                last_exception = e
                if attempt < max_retries:
                    # Force client recreation on connection errors
                    if self._client:
                        self._client.close()
                        self._client = None
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    continue
                raise
            except Exception as e:
                # Don't retry on non-connection errors
                raise
        
        raise last_exception
        
    @staticmethod
    def ensure_index(coll, index_fields, **kwargs):
        """
        Ensure that a specified index exists on the given MongoDB collection.
        
        This method checks if an index with the specified fields and options already exists on the collection.
        If the index does not exist, it creates the index using the provided fields and options.
        
        Parameters:
            coll (pymongo.collection.Collection): The MongoDB collection to operate on.
            index_fields (list of tuples): A list of (field, direction) pairs specifying the index keys,
                e.g., [('status', pymongo.ASCENDING)].
            **kwargs: Additional keyword arguments to pass to the create_index method, such as 'name' or 'unique'.
        
        Returns:
            None
        """
        existing_indexes = coll.index_information()

        # Normalize input index spec for comparison
        target_index = pymongo.helpers._index_list(index_fields)

        for index_name, index_data in existing_indexes.items():
            if pymongo.helpers._index_list(index_data['key']) == target_index:
                return  # Index already exists

        coll.create_index(index_fields, **kwargs)