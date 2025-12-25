import numpy as np
import pandas as pd
import os
import time
import uuid
import threading
import bson
import lz4.frame
import asyncio
import queue
import multiprocessing

from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import Consumer, KafkaError        
from confluent_kafka import Producer

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

from SharedData.Database import DATABASE_PKEYS
from SharedData.Logger import Logger

class StreamKafka:

    """
    Class for managing Kafka streaming with support for both synchronous (confluent_kafka) and asynchronous (aiokafka) modes.
    
    This class handles topic creation, producing and consuming messages with optional compression and BSON encoding,
    and provides utilities for retention configuration, topic deletion, and background tasks for caching and persisting streams.
    
    Attributes:
        shdata: Shared data handler used for persistence.
        user (str): Kafka user prefix for topic naming.
        database (str): Database name used in topic naming.
        period (str): Period identifier used in topic naming.
        source (str): Source identifier used in topic naming.
        tablename (str): Table name used in topic naming.
        use_aiokafka (bool): Flag to use asynchronous aiokafka instead of synchronous confluent_kafka.
        bootstrap_servers (str): Kafka bootstrap servers.
        replication (int): Number of Kafka topic replication factor.
        partitions (int): Number of Kafka topic partitions.
        retention_ms (int): Topic retention period in milliseconds.
        topic (str): Kafka topic name constructed from parameters.
        pkeys (list): Primary keys required in messages for the database.
        _producer: Kafka producer instance (sync or async).
        consumers (dict): Dictionary of Kafka consumers keyed by
    """
    def __init__(
        self, shdata,
        database, period, source, tablename,
        user='master',
        bootstrap_servers=None,
        replication=None,
        partitions=None,
        retention_ms=None, 
        use_aiokafka=False,        
        create_if_not_exists=True,        
    ):
        """
        '''
        Initialize a Kafka topic handler with configuration and optional topic creation.
        
        Parameters:
            shdata: Shared data or context object.
            database (str): Name of the database.
            period (str): Time period identifier.
            source (str): Data source identifier.
            tablename (str): Name of the table.
            user (str, optional): User identifier, default is 'master'.
            bootstrap_servers (str or None, optional): Kafka bootstrap servers; if None, read from environment variable 'KAFKA_BOOTSTRAP_SERVERS'.
            replication (int or None, optional): Replication factor; if None, read from environment variable 'KAFKA_REPLICATION'.
            partitions (int or None, optional): Number of partitions; if None, read from environment variable 'KAFKA_PARTITIONS'.
            retention_ms (int or None, optional): Retention time in milliseconds; if None, read from environment variable 'KAFKA_RETENTION'.
            use_aiokafka (bool, optional): Whether to use aiokafka library, default is False.
            create_if_not_exists (bool, optional): Whether to create the Kafka topic if it does not exist, default is True.
        
        Raises:
            FileNotFoundError: If create_if_not_exists is
        """
        self.shdata = shdata
        self.user = user
        self.database = database
        self.period = period
        self.source = source
        self.tablename = tablename
        self.use_aiokafka = use_aiokafka
        self.topic = f'{user}/{database}/{period}/{source}/stream/{tablename}'.replace('/','-')


        if bootstrap_servers is None:
            bootstrap_servers = os.environ['KAFKA_BOOTSTRAP_SERVERS']
        self.bootstrap_servers = bootstrap_servers
        
        self.exists = False
        admin = AdminClient({'bootstrap.servers': self.bootstrap_servers})
        # create topic if not exists
        if self.topic in admin.list_topics().topics:
            self.exists = True
        
        if not create_if_not_exists and not self.exists:
            raise FileNotFoundError(f'Topic {self.topic} does not exist')
                        
        if replication is None:
            self.replication = int(os.environ['KAFKA_REPLICATION'])
        else:
            self.replication = replication
        
        if partitions is None:
            self.partitions = int(os.environ['KAFKA_PARTITIONS'])
        else:
            self.partitions = partitions

        if retention_ms is None:
            self.retention_ms = int(os.environ['KAFKA_RETENTION'])
        else:
            self.retention_ms = retention_ms

        self.lock = threading.Lock()
        self.pkeys = DATABASE_PKEYS[database]

        self._producer = None                
        self.consumers = {}
        
        # create topic if not exists
        if not self.exists:
            new_topic = NewTopic(
                self.topic, 
                num_partitions=self.partitions, 
                replication_factor=self.replication,
                config={"retention.ms": str(self.retention_ms)} 
            )
            fs = admin.create_topics([new_topic])
            for topic, f in fs.items():
                try:
                    f.result()
                    time.sleep(2)
                    Logger.log.info(f"Topic {topic} created.")
                except Exception as e:
                    if not 'already exists' in str(e):
                        raise e
        
        #get number of partitions
        self.num_partitions = len(admin.list_topics(topic=self.topic).topics[self.topic].partitions)        

    #
    # Producer sync (confluent) and async (aiokafka)
    #
    @property
    def producer(self):
        """
        Lazily initializes and returns a synchronous Kafka producer instance.
        
        If the instance is configured to use aiokafka (asynchronous Kafka client),
        accessing this property will raise a RuntimeError, instructing to use the
        asynchronous method `get_async_producer()` instead.
        
        Thread-safe: ensures that the producer is created only once using a lock.
        
        Returns:
            Producer: A synchronous Kafka producer instance.
        
        Raises:
            RuntimeError: If called when `use_aiokafka` is True.
        """
        if self.use_aiokafka:
            raise RuntimeError("Use 'await get_async_producer()' in aiokafka mode.")
        with self.lock:
            if self._producer is None:                
                self._producer = Producer({'bootstrap.servers': self.bootstrap_servers})
            return self._producer

    async def get_async_producer(self):
        """
        Asynchronously retrieves an instance of AIOKafkaProducer.
        
        Raises:
            RuntimeError: If the method is called when not in aiokafka mode.
        
        Returns:
            AIOKafkaProducer: An initialized and started AIOKafkaProducer instance.
        """
        if not self.use_aiokafka:
            raise RuntimeError("This method is only available in aiokafka mode.")
        if self._producer is None:            
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,                
            )            
            await self._producer.start()
        return self._producer

    #
    # Extend (produce) sync/async
    #
    def extend(self, data):
        """
        Extend the producer with new messages by compressing and encoding them, then sending to the configured topic.
        
        Parameters:
            data (list or dict): The message(s) to be sent. Each message must contain all primary keys specified in self.pkeys.
        
        Raises:
            RuntimeError: If called when use_aiokafka is True, instructing to use async_extend instead.
            Exception: If any message is missing required primary keys.
            Exception: If data is not a list or dict.
            Exception: If flushing messages to the producer fails.
        
        Notes:
            - Messages are encoded using BSON and compressed with lz4 before being produced.
            - The method waits up to 5 seconds for the producer to flush messages.
        """
        if self.use_aiokafka:
            raise RuntimeError("Use 'await async_extend(...)' in aiokafka mode.")
        
        if isinstance(data, list):
            for msg in data:
                for pkey in self.pkeys:
                    if not pkey in msg:
                        raise Exception(f'extend(): Missing pkey {pkey} in {msg}')                
                message = lz4.frame.compress(bson.BSON.encode(msg))                
                self.producer.produce(self.topic, value=message)
        elif isinstance(data, dict):
            for pkey in self.pkeys:
                if not pkey in data:
                    raise Exception(f'extend(): Missing pkey {pkey} in {data}')
            message = lz4.frame.compress(bson.BSON.encode(data))
            self.producer.produce(self.topic, value=message)
        else:
            raise Exception('extend(): Invalid data type')                
      
        # Wait up to 5 seconds
        result = self.producer.flush(timeout=5.0)
        if result > 0:
            raise Exception(f"Failed to flush {result} messages")
                
    async def async_extend(self, data):
        """
        Asynchronously extends the Kafka topic with the provided data using aiokafka.
        
        Parameters:
            data (list or dict): The data to be sent to the Kafka topic. Must be either a list of dictionaries or a single dictionary.
                                 Each dictionary must contain all primary keys specified in self.pkeys.
        
        Raises:
            RuntimeError: If called when not using aiokafka mode.
            Exception: If any primary key in self.pkeys is missing from the data.
            Exception: If the data type is neither a list nor a dictionary.
        
        Behavior:
            - Compresses the BSON-encoded data using lz4 before sending.
            - Sends each message asynchronously to the Kafka topic specified by self.topic.
        """
        if not self.use_aiokafka:
            raise RuntimeError("Use 'extend()' in confluent_kafka mode.")
        
        producer = await self.get_async_producer()                            
        if isinstance(data, list):
            for msg in data:

                for pkey in self.pkeys:
                    if not pkey in msg:
                        raise Exception(f'extend(): Missing pkey {pkey} in {msg}')
                                    
                message = lz4.frame.compress(bson.BSON.encode(msg))                
                await producer.send(self.topic, value=message)            

        elif isinstance(data, dict):

            for pkey in self.pkeys:
                if not pkey in data:
                    raise Exception(f'extend(): Missing pkey {pkey} in {data}')
                            
            message = lz4.frame.compress(bson.BSON.encode(data))
            await producer.send(self.topic, value=message)

        else:
            raise Exception('extend(): Invalid data type')
                    
    #
    # Flush/close producer
    #
    def flush(self, timeout=5.0):
        """
        Flushes the producer's message buffer, ensuring all messages are sent within the specified timeout.
        
        Raises:
            RuntimeError: If called in aiokafka mode; use 'async_flush()' instead.
            Exception: If flushing fails to send all messages within the timeout.
        
        Args:
            timeout (float): Maximum time in seconds to wait for the flush operation. Defaults to 5.0 seconds.
        """
        if self.use_aiokafka:
            raise RuntimeError("Use 'await async_flush()' in aiokafka mode.")
        if self._producer is not None:
            result = self._producer.flush(timeout=timeout)
            if result > 0:
                raise Exception(f"Failed to flush {result} messages")
    
    async def async_flush(self):
        """
        Asynchronously flushes the producer's messages if using aiokafka.
        
        Raises:
            RuntimeError: If called when not using aiokafka mode.
        """
        if not self.use_aiokafka:
            raise RuntimeError("Use 'flush()' in non-aiokafka mode.")
        if self._producer is not None:
            await self._producer.flush()            

    #
    # Consumer sync/async
    #
    def subscribe(self, groupid=None, offset = 'latest', autocommit=True, timeout=None):
        """
        Subscribe to a Kafka topic with a specified consumer group.
        
        Parameters:
            groupid (str, optional): The consumer group ID. If None, a new UUID is generated.
            offset (str, optional): Offset reset policy, e.g., 'latest' or 'earliest'. Defaults to 'latest'.
            autocommit (bool, optional): Whether to enable automatic offset commits. Defaults to True.
            timeout (float or None, optional): Maximum time in seconds to wait for partition assignment. If None, waits indefinitely.
        
        Raises:
            RuntimeError: If called in aiokafka mode; use async_subscribe() instead.
            TimeoutError: If partition assignment does not occur within the specified timeout.
        
        Behavior:
            Creates and subscribes a Kafka consumer to the specified topic under the given group ID.
            Waits for partition assignment up to the timeout duration if provided.
            Stores the consumer instance in self.consumers keyed by groupid.
        """
        if self.use_aiokafka:
            raise RuntimeError("Use 'await async_subscribe()' in aiokafka mode.")
        
        if groupid is None:
            groupid = str(uuid.uuid4())

        if groupid not in self.consumers:
            self.consumers[groupid] = []            
            consumer = Consumer({
                    'bootstrap.servers': self.bootstrap_servers,
                    'group.id': groupid,
                    'auto.offset.reset': offset,
                    'enable.auto.commit': autocommit
                })                            
            consumer.subscribe([self.topic])
            # Wait for partition assignment
            if timeout is not None:
                start = time.time()
                while not consumer.assignment():
                    if time.time() - start > timeout:
                        raise TimeoutError("Timed out waiting for partition assignment.")
                    consumer.poll(0.1)
                    time.sleep(0.1)
            self.consumers[groupid] = consumer

    async def async_subscribe(self, groupid=None, offset='latest', autocommit=True):
        """
        Asynchronously subscribes to a Kafka topic using aiokafka.
        
        If no consumer group ID is provided, a unique one is generated. Initializes and starts an AIOKafkaConsumer for the specified topic, bootstrap servers, and group ID, with configurable offset reset and auto-commit settings. Raises a RuntimeError if called when not using aiokafka mode.
        
        Parameters:
            groupid (str, optional): Consumer group ID. If None, a new UUID is generated. Defaults to None.
            offset (str, optional): Offset reset policy ('latest' or 'earliest'). Defaults to 'latest'.
            autocommit (bool, optional): Whether to enable auto-commit of offsets. Defaults to True.
        
        Raises:
            RuntimeError: If called when not using aiokafka mode.
        """
        if not self.use_aiokafka:
            raise RuntimeError("Use 'subscribe()' in confluent_kafka mode.")
        
        if groupid is None:
            groupid = str(uuid.uuid4())
        
        if groupid not in self.consumers:            
            consumer = AIOKafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=groupid,
                auto_offset_reset=offset,
                enable_auto_commit=autocommit
            )            
            await consumer.start()
            self.consumers[groupid] = consumer
                            
    #
    # Poll (consume one message) sync/async
    #
    def poll(self, groupid = None, timeout=None):
        """
        Polls a message from the Kafka consumer for the specified consumer group.
        
        Parameters:
            groupid (str, optional): The consumer group ID to poll from. If None, uses the first available consumer group.
            timeout (float or int, optional): The timeout in seconds for polling. If None, polls indefinitely.
        
        Returns:
            dict or None: The decoded message as a dictionary if a message is received; None if no message is available.
        
        Raises:
            RuntimeError: If called in aiokafka mode or if the consumer group is not subscribed.
            Exception: If a Kafka error occurs other than reaching the end of a partition.
        """
        if self.use_aiokafka:
            raise RuntimeError("Use 'async_poll()' in aiokafka mode.")
        
        if groupid is None:
            if len(self.consumers) == 0:
                raise RuntimeError("You must call 'await async_subscribe()' first.")
            groupid = list(self.consumers.keys())[0] # use first consumer        

        if self.consumers[groupid] is None:
            raise RuntimeError("You must call 'await async_subscribe()' first.")
        
        consumer = self.consumers[groupid]

        if timeout is None:
            msg = consumer.poll()
        else:
            msg = consumer.poll(timeout)
            
        if msg is None:
            return None
        
        if msg.error():            
            if msg.error().code() != KafkaError._PARTITION_EOF:
                raise Exception(f"Error: {msg.error()}")
            
        msgdict = bson.BSON.decode(lz4.frame.decompress(msg.value()))        
        return msgdict
    
    async def async_poll(
        self,
        groupid: str = None,
        timeout: int = 0,
        max_records: int = None,
        decompress: bool = True
    ):
        """
        Asynchronously polls all consumers for the specified consumer group ID in parallel using asyncio, retrieving messages from Kafka topics.
        
        Args:
            groupid (str, optional): The consumer group ID to poll. If None, uses the first available consumer group.
            timeout (int, optional): The timeout in milliseconds to wait for messages. Defaults to 0 (no wait).
            max_records (int, optional): The maximum number of records to fetch per partition. Defaults to None (no limit).
            decompress (bool, optional): Whether to decompress the message values using lz4 and decode BSON. Defaults to True.
        
        Returns:
            list: A combined list of all decoded messages received from all partitions of the specified consumer group.
        
        Raises:
            RuntimeError: If called in non-aiokafka mode or if the consumer group is not subscribed.
        """
        if not self.use_aiokafka:
            raise RuntimeError("Use 'poll()' in confluent_kafka mode.")

        if groupid is None:
            if len(self.consumers) == 0:
                raise RuntimeError("You must call 'await async_subscribe()' first.")
            groupid = list(self.consumers.keys())[0]  # use first consumer group

        if self.consumers[groupid] is None:
            raise RuntimeError("You must call 'await async_subscribe()' first.")
        
        msgs = []
        consumer = self.consumers[groupid]
        partitions = await consumer.getmany(timeout_ms=timeout, max_records=max_records)
        for partition, messages in partitions.items():
            for msg in messages:
                if msg.value is not None:
                    if decompress:
                        msgdict = bson.BSON.decode(lz4.frame.decompress(msg.value))
                    else:
                        msgdict = msg.value                     
                    msgs.append(msgdict)        
        return msgs
    
    async def async_commit(self, groupid: str) -> None:
        """
        Asynchronously commits the consumer offsets for the specified consumer group to Kafka.
        
        Parameters:
            groupid (str): The identifier of the consumer group whose offsets are to be committed.
        
        Raises:
            Exception: Propagates any exception encountered during the commit operation after logging the error.
        """
        try:
            await self.consumers[groupid].commit()
        except Exception as e:
            Logger.log.error(f"Failed to commit offsets for group {groupid}: {e}")
            raise
    #
    # Retention update (sync mode only)
    #
    def set_retention(self, retention_ms):
        """
        Set the retention period for the Kafka topic in milliseconds.
        
        This method updates the 'retention.ms' configuration for the specified topic using the Confluent Kafka AdminClient.
        It only supports synchronous mode (confluent_kafka) and will raise a RuntimeError if called in async mode (aiokafka).
        
        Parameters:
            retention_ms (int): The retention period in milliseconds to set for the topic.
        
        Returns:
            bool: True if the retention period was successfully updated, False otherwise.
        
        Raises:
            RuntimeError: If called when using aiokafka (async mode).
        """
        if self.use_aiokafka:
            raise RuntimeError("Set retention_ms only supported in sync mode (confluent_kafka).")
        from confluent_kafka.admin import AdminClient, ConfigResource
        admin = AdminClient({'bootstrap.servers': self.bootstrap_servers})
        config_resource = ConfigResource('topic', self.topic)
        new_config = {'retention.ms': str(retention_ms)}
        fs = admin.alter_configs([config_resource], new_configs=new_config)
        for resource, f in fs.items():
            try:
                f.result()
                Logger.log.debug(f"Retention period for topic {resource.name()} updated to {retention_ms} ms.")
                return True
            except Exception as e:
                Logger.log.error(f"Failed to update retention_ms period: {e}")
                return False

    #
    # Sync/async close for consumer (optional)
    #
    def close(self):
        """
        Stops all consumer instances managed by this object by calling their stop method.
        """
        for consumer in self.consumers.values():            
            consumer.stop()

    async def async_close(self):
        """
        Asynchronously stops and closes all consumer instances managed by this object.
        Iterates through all consumers stored in the `consumers` dictionary, awaits their `stop` coroutine to properly shut them down, and then clears the dictionary to remove all references.
        This ensures that all asynchronous consumers are cleanly closed and resources are released.
        """
        for consumer in self.consumers.values():            
            await consumer.stop()
        
        self.consumers.clear()

    def delete(self) -> bool:
        """
        Deletes the Kafka topic specified by the instance's topic attribute.
        
        Returns:
            bool: True if the topic was successfully deleted, False if the topic does not exist or if an error occurred during deletion.
        """
        
        admin = AdminClient({'bootstrap.servers': self.bootstrap_servers})
        if self.topic not in admin.list_topics(timeout=10).topics:
            Logger.log.warning(f"Topic {self.topic} does not exist.")
            return False
        fs = admin.delete_topics([self.topic])
        for topic, f in fs.items():
            try:
                f.result()  # Wait for operation to finish
                Logger.log.debug(f"Topic {topic} deleted.")
                return True
            except Exception as e:
                Logger.log.error(f"Failed to delete topic {topic}: {e}")
                return False
        return False
            
    async def async_cache_stream_task(self, cache, groupid = 'cache-group', offset = 'earliest'):
        """
        Asynchronously subscribes to a stream and continuously polls for messages to cache them.
        
        This method runs continuously and retries every 15 seconds if any error occurs, ensuring persistent operation.
        
        Args:
            cache: An asynchronous cache object with methods `async_set` and a `header` supporting `async_incrby`.
            groupid (str, optional): The consumer group ID for subscription. Defaults to 'cache-group'.
            offset (str, optional): The offset position to start consuming messages from. Defaults to 'earliest'.
        
        Behavior:
            - Subscribes to the stream with the specified consumer group and offset.
            - Continuously polls for messages asynchronously up to 50,000 records at a time.
            - Stores retrieved messages in the provided cache.
            - Commits the consumer group's offset after each batch.
            - Increments a counter tracking the number of cached messages.
            - On any error, logs the error and retries after 15 seconds.
        """
        subscribed = False
        
        while True:
            try:
                # Ensure we're subscribed
                if not subscribed:
                    Logger.log.info(f"Subscribing to stream {self.topic} with group {groupid}")
                    await self.async_subscribe(groupid=groupid, offset=offset, autocommit=False)
                    subscribed = True
                    Logger.log.info(f"Successfully subscribed to stream {self.topic}")
                
                # Poll for messages
                msgs = await self.async_poll(timeout=1.0, groupid=groupid, max_records=50000)
                if not msgs:
                    continue                
                
                # Cache messages and commit
                await cache.async_set(msgs)
                await self.async_commit(groupid=groupid)
                await cache.header.async_incrby(f'stream->{groupid}->cache_counter', len(msgs))
                
            except Exception as e:
                errmsg = f"Error in cache_stream_task for {self.topic}: {e}"
                Logger.log.error(errmsg)
                
                # Reset subscription status to force re-subscription on next iteration
                subscribed = False
                
                # Close existing consumers to clean up
                try:
                    if groupid in self.consumers:
                        await self.consumers[groupid].stop()
                        del self.consumers[groupid]
                except Exception as cleanup_error:
                    Logger.log.warning(f"Error during consumer cleanup: {cleanup_error}")
                
                # Wait 15 seconds before retrying
                Logger.log.info(f"Retrying cache_stream_task for {self.topic} in 15 seconds...")
                await asyncio.sleep(15)

    async def async_persist_stream_task(self, cache, partitioning='daily'):
        """
        Asynchronously subscribes to a data stream, continuously polls for new records, and persists them into a partitioned storage collection.
        
        This method runs continuously and retries every 15 seconds if any error occurs, ensuring persistent operation.
        
        Parameters:
            cache: An object providing asynchronous increment functionality for tracking persisted record counts.
            partitioning (str): The partitioning scheme for storing data. Supported values are 'daily', 'monthly', 'yearly', or None for no partitioning. Defaults to 'daily'.
        
        Behavior:
            - Subscribes to the stream with a fixed consumer group 'persist-group' starting from the earliest offset.
            - Continuously polls the stream for up to 50,000 records with a 1-second timeout.
            - Determines the partition key based on 'date' or 'mtime' fields in the data.
            - Converts timestamps to pandas datetime if necessary.
            - Constructs the target table name based on the partitioning scheme.
            - Extends the corresponding collection with the new data.
            - Commits the offset asynchronously.
            - Increments a persistence counter in the provided cache.
            - On any error, logs the error and retries after 15 seconds.
        """
        groupid = 'persist-group'
        offset = 'earliest'
        subscribed = False
        
        while True:
            try:
                # Ensure we're subscribed
                if not subscribed:
                    Logger.log.info(f"Subscribing to stream {self.topic} with group {groupid}")
                    await self.async_subscribe(offset=offset, groupid=groupid, autocommit=False)
                    subscribed = True
                    Logger.log.info(f"Successfully subscribed to stream {self.topic}")
                
                # Poll for data
                data = await self.async_poll(timeout=1.0, groupid=groupid, max_records=50000)
                if not data:
                    continue
                if len(data) == 0:
                    continue
                
                # Process data
                if 'date' in data[0]:
                    dateidx = data[0]['date']
                elif 'mtime' in data[0]:
                    dateidx = data[0]['mtime']
                    if isinstance(dateidx, (int, np.integer)):
                        dateidx = pd.to_datetime(dateidx, unit='ns')

                tablename = self.tablename                
                if not partitioning is None:
                    if partitioning=='daily':
                        tablename = f"{self.tablename}/{dateidx.strftime('%Y%m%d')}"
                    elif partitioning=='monthly':
                        tablename = f"{self.tablename}/{dateidx.strftime('%Y%m')}"
                    elif partitioning=='yearly':
                        tablename = f"{self.tablename}/{dateidx.strftime('%Y')}"

                collection = self.shdata.collection(self.database, self.period, self.source, tablename, user=self.user, hasindex=False)
                collection.extend(data)
                await self.async_commit(groupid=groupid)
                await cache.header.async_incrby(f'stream->{groupid}->persist_counter', len(data))                
                
            except Exception as e:
                errmsg = f"Error in persist_stream_task for {self.topic}: {e}"
                Logger.log.error(errmsg)
                
                # Reset subscription status to force re-subscription on next iteration
                subscribed = False
                
                # Close existing consumers to clean up
                try:
                    if groupid in self.consumers:
                        await self.consumers[groupid].stop()
                        del self.consumers[groupid]
                except Exception as cleanup_error:
                    Logger.log.warning(f"Error during consumer cleanup: {cleanup_error}")
                
                # Wait 15 seconds before retrying
                Logger.log.info(f"Retrying persist_stream_task for {self.topic} in 15 seconds...")
                await asyncio.sleep(15)

    
# ========== USAGE PATTERNS ==========

# --- Synchronous / confluent_kafka ---
"""
stream = StreamKafka(
    database="mydb", period="1m", source="agg", tablename="prices",
    self.bootstrap_servers="localhost:9092",
    KAFKA_PARTITIONS=1,
    use_aiokafka=False
)
stream.extend({'price': 100, 'ts': time.time()})
stream.subscribe()
msg = stream.poll(timeout=1.0)
print(msg)
stream.close()
"""

# --- Asynchronous / aiokafka ---
"""
import asyncio

async def main():
    stream = StreamKafka(
        database="mydb", period="1m", source="agg", tablename="prices",
        self.bootstrap_servers="localhost:9092",
        KAFKA_PARTITIONS=1,
        use_aiokafka=True
    )
    await stream.async_extend({'price': 200, 'ts': time.time()})
    await stream.async_subscribe()
    async for msg in stream.async_poll():
        print(msg)
        break
    await stream.async_flush()
    await stream.async_close()

asyncio.run(main())
"""