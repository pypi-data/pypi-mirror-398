import os
import logging
import threading
import boto3
import time
import pytz
import json
from io import StringIO
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta, timezone
import numpy as np
import hashlib
import pymongo
from filelock import FileLock

from botocore.exceptions import ClientError
from SharedData.IO.MongoDBClient import MongoDBClient
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT


def add_auth_header(request, **kwargs):
    """
    Adds a custom authorization header to the provided HTTP request object.
    
    Retrieves the token from the environment variable 'SHAREDDATA_TOKEN' and sets it
    as the value of the 'X-Custom-Authorization' header in the request.
    
    Parameters:
    - request: An HTTP request object that supports header modification.
    - **kwargs: Additional keyword arguments for future use (currently unused).
    
    Raises:
    - KeyError: If the 'SHAREDDATA_TOKEN' environment variable is not set.
    """
    # Add the Authorization header
    token = os.environ['SHAREDDATA_TOKEN']
    request.headers['X-Custom-Authorization'] = token

def KinesisGetSession():
    """
    Create and return a boto3 Kinesis client configured using environment variables.
    
    The function establishes a boto3 session for AWS Kinesis by checking environment variables
    in the following order:
    
    1. Uses 'KINESIS_ACCESS_KEY_ID' and 'KINESIS_SECRET_ACCESS_KEY' with optional 'KINESIS_DEFAULT_REGION'.
    2. Uses 'AWS_ACCESS_KEY_ID' and 'AWS_SECRET_ACCESS_KEY' with optional 'AWS_DEFAULT_REGION'.
    3. Uses the AWS profile specified by 'KINESIS_AWS_PROFILE'.
    
    If none of these credentials or profile settings are found, it raises an Exception.
    
    If 'KINESIS_ENDPOINT_URL' is set, the Kinesis client is configured to use this custom endpoint URL.
    
    If 'SHAREDDATA_TOKEN' is present, a custom authentication header is added by registering the
    'add_auth_header' function to the client's 'before-sign.kinesis' event.
    
    Returns:
        botocore.client.Kinesis: A boto3 Kinesis client instance configured with the specified credentials and settings.
    
    Raises:
        Exception: If required AWS credentials or profile environment variables are not set.
    """
    if 'KINESIS_ACCESS_KEY_ID' in os.environ and 'KINESIS_SECRET_ACCESS_KEY' in os.environ:        
        _session = boto3.Session(
            aws_access_key_id=os.environ['KINESIS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['KINESIS_SECRET_ACCESS_KEY'],
            region_name=os.environ.get('KINESIS_DEFAULT_REGION','us-east-1'),
            botocore_session=boto3.Session()._session,  
        )                
    elif 'AWS_ACCESS_KEY_ID' in os.environ and 'AWS_SECRET_ACCESS_KEY' in os.environ:        
        _session = boto3.Session(
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            region_name=os.environ.get('AWS_DEFAULT_REGION','us-east-1'),
            botocore_session=boto3.Session()._session,  # Use a separate botocore session
        )        
    elif 'KINESIS_AWS_PROFILE' in os.environ:
        _session = boto3.Session(profile_name=os.environ['KINESIS_AWS_PROFILE'])
    else:
        raise Exception('KINESIS_ACCESS_KEY_ID and KINESIS_SECRET_ACCESS_KEY or AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY or KINESIS_AWS_PROFILE must be set in environment variables')

    if 'KINESIS_ENDPOINT_URL' in os.environ:
        _kinesis = _session.client(
            'kinesis', endpoint_url=os.environ['KINESIS_ENDPOINT_URL'])
    else:
        _kinesis = _session.client('kinesis')

    if 'SHAREDDATA_TOKEN' in os.environ:
        _kinesis.meta.events.register(
            'before-sign.kinesis', add_auth_header)
    
    return _kinesis

# LOGS BUS
class KinesisLogHandler(logging.Handler):
    # reference: https://docs.python.org/3/library/logging.html#logging.LogRecord
    """
    A custom logging handler that sends log records to an AWS Kinesis data stream.
    
    This handler initializes a Kinesis client session, creates a Kinesis stream if it does not exist,
    and buffers log records before sending them to the specified Kinesis stream. Each log record is
    formatted as a JSON object containing the user name, timestamp, logger name, log level, and message.
    
    Attributes:
        user (str): The user identifier for the log handler, default is 'guest'.
        stream_buffer (list): Buffer to hold log records before sending to Kinesis.
        client: AWS Kinesis client session.
        stream_name (str): Name of the Kinesis stream obtained from environment variable 'LOG_STREAMNAME'.
    
    Methods:
        get_client(): Attempts to establish a Kinesis client session with retries.
        create_stream(): Creates a Kinesis stream with a single shard in provisioned mode.
        emit(record): Formats and sends a log record to the Kinesis stream, handling errors and reconnecting if needed.
    
    Raises:
        Exception: If unable to establish a Kinesis client session during initialization or emit.
    """
    def __init__(self, user='guest'):
        """
        Initializes the logging handler instance.
        
        Parameters:
            user (str): The username associated with the logging session. Defaults to 'guest'.
        
        Sets up the logging stream by:
        - Initializing the parent class.
        - Storing the user.
        - Preparing an empty buffer for log streams.
        - Retrieving the log stream name from the environment variable 'LOG_STREAMNAME'.
        - Attempting to initialize the client; raises an exception if client initialization fails.
        - Creating the log stream.
        """
        super().__init__()
        self.user = user
        self.stream_buffer = []        
        self.client = None
        self.stream_name = os.environ['LOG_STREAMNAME']

        if not self.get_client():
            raise Exception('Logging failed check aws credentials!')

        self.create_stream()
        
    def get_client(self):
        """
        Attempts to establish a connection to Kinesis by creating a KinesisGetSession client.
        
        Retries up to 3 times, waiting 1 second between attempts if a failure occurs.
        On successful creation, assigns the client to self.client and returns True.
        Returns False if all attempts fail.
        
        Returns:
            bool: True if the client was successfully created, False otherwise.
        """
        success = False
        trials = 3
        while trials>0:
            trials-=1
            try:                
                self.client = KinesisGetSession()
                success = True
                break
            except Exception as e:
                print('Failed to connect to kinesis retying 1/%i\n%s' % (trials, e))
                time.sleep(1)
                pass
        return success

    def create_stream(self):
        """
        Creates a new provisioned stream with one shard using the client's create_stream method.
        Waits for 10 seconds to allow the stream to become active.
        Suppresses any exceptions that occur during the creation process.
        """
        try:
            self.client.create_stream(
                StreamName=self.stream_name,
                ShardCount=1,
                StreamModeDetails={
                    'StreamMode': 'PROVISIONED'
                }
            )
            time.sleep(10)
        except Exception as e:
            pass

    def emit(self, record):
        """
        Emit a log record to an AWS Kinesis stream.
        
        Formats the log record into a JSON message containing the user name (from the USER_COMPUTER environment variable),
        timestamp in ISO 8601 UTC format, logger name, log level, and the log message with single quotes replaced by double quotes.
        The message is UTF-8 encoded and appended to an internal buffer with a partition key based on the user name.
        
        If a Kinesis client is available and the buffer is not empty, all buffered records are sent to the configured Kinesis stream,
        and the buffer is cleared.
        
        Thread safety is maintained by acquiring and releasing a lock during the operation.
        
        If an exception occurs during processing, the error is handled. If the Kinesis client cannot be obtained,
        an exception is raised indicating a possible AWS credentials issue.
        """
        try:
            self.acquire()
            # msg = self.format(record)
            user = os.environ['USER_COMPUTER']
            dt = datetime.fromtimestamp(record.created, timezone.utc)
            asctime = dt.strftime('%Y-%m-%dT%H:%M:%S%z')
            msg = {
                'user_name': user,
                'asctime': asctime,
                'logger_name': record.name,
                'level': record.levelname,
                'message': str(record.msg).replace('\'', '\"'),
            }
            msg = json.dumps(msg).encode(encoding="UTF-8", errors="strict")
            self.stream_buffer.append({
                'Data': msg,
                'PartitionKey': user,
            })
            if self.client and self.stream_buffer:
                self.client.put_records(
                    StreamName=self.stream_name,
                    Records=self.stream_buffer
                )
                self.stream_buffer.clear()
                        
        except Exception:
            self.handleError(record)
            if not self.get_client():
                raise Exception('Logging failed check aws credentials!')
                        
        finally:            
            self.release()

class KinesisLogStreamConsumer():
    """
    '''
    Class to consume and process log streams from AWS Kinesis, with optional saving to MongoDB and local log files.
    
    Attributes:
        user (str): Username associated with the log consumer.
        save_to_db (bool): Flag to enable saving logs to MongoDB.
        mongodb (MongoDBClient or None): MongoDB client instance if saving to DB.
        db (Database): MongoDB database instance.
        dflogs (pd.DataFrame): DataFrame holding logs read from files or stream.
        lastlogfilepath (Path): Path to the previous day's log file.
        last_day_read (bool): Flag indicating if last day's logs have been read.
        logfilepath (Path): Path to the current day's log file.
        logfileposition (int): Position in the current log file to continue reading.
        client: AWS Kinesis client session.
        stream (dict): Description and shard information of the Kinesis stream.
    
    Methods:
        read_last_day_logs():
            Reads logs from the previous day's log file and appends them to the DataFrame.
    
        readLogs():
            Reads new logs from the current day's log file, updating the DataFrame.
    
        getLogs():
            Returns the current logs DataFrame, filtering and sorting heartbeat messages.
    
        connect():
            Establish
    """
    def __init__(self, user='guest', save_to_db=False):
        """
        Initialize the logger instance.
        
        Parameters:
            user (str): The username associated with the logs. Defaults to 'guest'.
            save_to_db (bool): Flag indicating whether to save logs to a MongoDB database. Defaults to False.
        
        Initializes:
            - MongoDB connection and ensures a time-series 'logs' collection exists if saving to DB.
            - An empty pandas DataFrame to hold log entries with predefined columns.
            - Paths for the current and previous day's log files based on environment variable 'DATABASE_FOLDER'.
            - A flag to track if the previous day's logs have been read.
            - The file position marker for reading the current log file.
        
        Automatically calls:
            - self.readLogs() to load existing logs from the log files.
        """
        self.user = user        
        self.save_to_db = save_to_db

        self.mongodb = None
        if self.save_to_db:
            self.mongodb = MongoDBClient()
            self.db = self.mongodb.client['SharedData']
            if 'logs' not in self.db.list_collection_names():
                # Create logs collection as timeseries collection
                self.db.create_collection("logs", timeseries={
                    'timeField': "asctime",
                    'metaField': "metadata",
                    'granularity': "seconds"
                })

        self.dflogs = pd.DataFrame(
            [],
            columns=['shardid', 'sequence_number', 'user_name', 'asctime', 'logger_name', 'level', 'message']
        )

        self.lastlogfilepath = Path(os.environ['DATABASE_FOLDER']) / 'Logs'
        self.lastlogfilepath = self.lastlogfilepath / \
            ((pd.Timestamp.utcnow() + timedelta(days=-1)).strftime('%Y%m%d')+'.log')
        self.last_day_read = False

        self.logfilepath = Path(os.environ['DATABASE_FOLDER']) / 'Logs'
        self.logfilepath = self.logfilepath / \
            (pd.Timestamp.utcnow().strftime('%Y%m%d')+'.log')
        self.logfileposition = 0

        self.readLogs()

    def read_last_day_logs(self):
        """
        Reads log entries from the last day's log file and appends them to the existing logs DataFrame.
        
        If the file at `lastlogfilepath` exists, attempts to read it as a semicolon-separated CSV, skipping malformed lines.
        Assigns predefined column names to the loaded data and concatenates it with the existing `dflogs` DataFrame.
        Sets the attribute `last_day_read` to True to indicate that the last day's logs have been processed.
        Any exceptions encountered during file reading are silently ignored.
        """
        self.last_day_read = True
        if self.lastlogfilepath.is_file():
            try:
                _dflogs = pd.read_csv(self.lastlogfilepath, header=None, sep=';',
                                      engine='python', on_bad_lines='skip')
                _dflogs.columns = ['shardid', 'sequence_number',
                                   'user_name', 'asctime', 'logger_name', 'level', 'message']
                self.dflogs = pd.concat([_dflogs, self.dflogs], axis=0)
            except:
                pass

    def readLogs(self):
        """
        Reads new log entries from the current day's log file and appends them to the existing logs DataFrame.
        
        If the previous day's logs have not been read yet, it reads those first. The method constructs the log file path based on the current UTC date and resets the file read position if the log file has changed. It then reads any new lines from the log file starting from the last read position, parses them into a DataFrame with predefined columns, and appends them to the existing logs DataFrame.
        
        Returns:
            pd.DataFrame: The updated DataFrame containing all read log entries.
        """
        if not self.last_day_read:
            self.read_last_day_logs()

        _logfilepath = Path(os.environ['DATABASE_FOLDER']) / 'Logs'
        _logfilepath = _logfilepath / \
            (pd.Timestamp.utcnow().strftime('%Y%m%d')+'.log')
        if self.logfilepath != _logfilepath:
            self.logfileposition = 0
            self.logfilepath = _logfilepath

        if self.logfilepath.is_file():
            try:
                with open(self.logfilepath, 'r') as file:
                    file.seek(self.logfileposition)
                    newlines = '\n'.join(file.readlines())
                    dfnewlines = pd.read_csv(StringIO(newlines), header=None, sep=';',
                                             engine='python', on_bad_lines='skip')
                    dfnewlines.columns = [
                        'shardid', 'sequence_number', 'user_name', 'asctime', 'logger_name', 'level', 'message']
                    self.dflogs = pd.concat([self.dflogs, dfnewlines])
                    self.logfileposition = file.tell()
            except:
                pass

        return self.dflogs

    def getLogs(self):
        """
        Retrieve and filter log entries from the data source.
        
        This method reads log data into a DataFrame, identifies entries containing the string '#heartbeat#',
        and limits the number of such heartbeat entries to the most recent 100 if there are more than 100.
        It then combines these filtered heartbeat entries with all other log entries, sorts them by their
        original order, and returns the resulting DataFrame.
        
        Returns:
            pandas.DataFrame: A DataFrame containing all non-heartbeat log entries along with up to the last
            100 heartbeat entries, preserving the original order.
        """
        df = self.readLogs()
        if not df.empty:
            idxhb = np.array(['#heartbeat#' in s for s in df['message'].astype(str)])
            idshb = np.where(idxhb)[0]
            if len(idshb > 100):
                idshb = idshb[-100:]
            ids = np.where(~idxhb)[0]
            ids = np.sort([*ids, *idshb])
            df = df.iloc[ids, :]
        return df

    def connect(self):
        """
        Establishes a connection to an AWS Kinesis stream, creating the stream if it does not exist, and initializes shard iterators for reading data.
        
        The method performs the following steps:
        1. Attempts to create a Kinesis client session.
        2. Tries to create a Kinesis stream with the name specified in the environment variable 'LOG_STREAMNAME'. If the stream already exists, it continues without error.
        3. Retrieves the stream description to access shard information.
        4. For each shard in the stream:
           - Determines whether to start reading from the last known sequence number stored in `self.dflogs` or from the start of the stream.
           - If reading from the start, uses either the latest record or the start of the current day as the iterator starting point, depending on the environment.
           - Stores the shard iterator in the stream's shard description for subsequent data retrieval.
        
        Returns:
            bool: True if the connection and stream setup were successful, False otherwise.
        """
        try:            
            self.client = KinesisGetSession()
        except:
            print('Could not connect to AWS!')
            return False

        try:
            print("Trying to create stream %s..." %
                  (os.environ['LOG_STREAMNAME']))
            self.client.create_stream(
                StreamName=os.environ['LOG_STREAMNAME'],
                ShardCount=1,
                StreamModeDetails={
                    'StreamMode': 'PROVISIONED'
                }
            )
            time.sleep(10)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print("Stream already exists")
            else:
                print("Trying to create stream unexpected error: %s" % e)
                pass

        try:
            self.stream = self.client.describe_stream(
                StreamName=os.environ['LOG_STREAMNAME'])
        except:
            print('Could not describe stream!')
            return False

        if self.stream and 'StreamDescription' in self.stream:
            self.stream = self.stream['StreamDescription']
            for i in range(len(self.stream['Shards'])):
                readfromstart = True
                shardid = self.stream['Shards'][i]['ShardId']
                if not self.dflogs.empty and (shardid in self.dflogs['shardid'].values):
                    readfromstart = False
                    seqnum = self.dflogs[self.dflogs['shardid']
                                         == shardid].iloc[-1]['sequence_number']
                    try:
                        shard_iterator = self.client.get_shard_iterator(
                            StreamName=self.stream['StreamName'],
                            ShardId=self.stream['Shards'][i]['ShardId'],
                            ShardIteratorType='AFTER_SEQUENCE_NUMBER',
                            StartingSequenceNumber=seqnum
                        )
                    except:
                        print(
                            'Failed retrieving shard iterator, reading from start...')
                        readfromstart = True
                
                if readfromstart:
                    print('############### READING FROM START ###############')                    
                    if 'KINESALITE' in os.environ:
                        shard_iterator = self.client.get_shard_iterator(
                            StreamName=self.stream['StreamName'],
                            ShardId=self.stream['Shards'][i]['ShardId'],                            
                            ShardIteratorType='LATEST'                            
                        )
                        
                    else:
                        start_of_day = pd.Timestamp.utcnow().floor('D').timestamp()

                        shard_iterator = self.client.get_shard_iterator(
                                            StreamName=self.stream['StreamName'],
                                            ShardId=self.stream['Shards'][i]['ShardId'],
                                            ShardIteratorType='AT_TIMESTAMP',
                                            Timestamp=start_of_day
                                        )
                    
                self.stream['Shards'][i]['ShardIterator'] = shard_iterator['ShardIterator']
        else:
            print('Failed connecting StreamDescriptor not found!')
            return False

        return True

    def consume(self):
        """
        Consumes records from each shard in the stream, processes and logs them to daily log files, and optionally saves them to a MongoDB database.
        
        For each shard in the stream:
        - Retrieves up to 1000 records using the shard iterator.
        - Updates the shard iterator to the next position.
        - Decodes and parses each record's data from JSON format.
        - Formats the record into a semicolon-separated log line.
        - Writes the log line to a daily log file in a thread-safe manner using file locking.
        - If enabled, inserts the log record into a MongoDB collection with structured fields.
        
        Returns:
            bool: True if the consumption and processing completed without unhandled exceptions, False otherwise.
        """
        try:
            for i in range(len(self.stream['Shards'])):
                response = self.client.get_records(
                    ShardIterator=self.stream['Shards'][i]['ShardIterator'],
                    Limit=1000)
                self.stream['Shards'][i]['ShardIterator'] = response['NextShardIterator']
                if len(response['Records']) > 0:
                    for r in response['Records']:
                        try:
                            rec = r['Data'].decode(
                                encoding="UTF-8", errors="strict")
                            rec = json.loads(rec.replace(
                                "\'", "\"").replace(';', ','))

                            line = '%s;%s;%s;%s;%s;%s;%s' % (self.stream['Shards'][i]['ShardId'],
                                                             r['SequenceNumber'], rec['user_name'], rec['asctime'],
                                                             rec['logger_name'], rec['level'], str(rec['message']).replace(';', ','))

                            dt = datetime.strptime(
                                rec['asctime'][:-5], '%Y-%m-%dT%H:%M:%S')

                            logfilepath = Path(
                                os.environ['DATABASE_FOLDER']) / 'Logs'
                            logfilepath = logfilepath / \
                                (dt.strftime('%Y%m%d')+'.log')
                            if not logfilepath.parents[0].is_dir():
                                os.makedirs(logfilepath.parents[0])
                            
                            lock_path = str(logfilepath) + ".lock"
                            with FileLock(lock_path):  # This acquires an OS-level lock
                                with open(logfilepath, 'a+', encoding='utf-8') as f:
                                    f.write(line.replace('\n', ' ').replace('\r', ' ')+'\n')
                                    f.flush()

                            if self.save_to_db:
                                # Parse asctime string to datetime with timezone info
                                asctime_str = rec['asctime']
                                asctime = datetime.strptime(asctime_str, '%Y-%m-%dT%H:%M:%S%z')
                                # Insert into MongoDB
                                document = {
                                    "asctime": asctime,
                                    "metadata": {
                                        "user_name": rec['user_name'].replace('\\','/'),
                                        "logger_name": rec['logger_name'].replace('\\','/'),
                                        "level": rec['level']
                                    },
                                    "message": rec['message'],
                                    "shard_id": self.stream['Shards'][i]['ShardId'],
                                    "sequence_number": r['SequenceNumber']
                                }
                                # unique_string = asctime_str + document['sequence_number'] + document['shard_id']
                                # _id = hashlib.sha256(unique_string.encode('utf-8')).hexdigest()
                                # document['_id'] = _id
                                try:
                                    self.db.logs.insert_one(document)
                                except Exception as e:
                                    print(f"An error occurred inserting logs to mongodb: {e}")

                        except Exception as e:
                            print('Invalid record:%s\nerror:%s' %
                                  (str(rec), str(e)))
            return True
        except:
            return False


# WORKER BUS
class KinesisStreamProducer():
    """
    Class to produce and send records to an AWS Kinesis stream.
    
    Attributes:
        stream_name (str): The name of the Kinesis stream.
        client: The Kinesis client session used to interact with the stream.
        stream_buffer (list): Buffer to hold records before sending.
    
    Methods:
        __init__(stream_name):
            Initializes the Kinesis client and attempts to create the stream if it does not exist.
        produce(record, partitionkey):
            Adds a record to the buffer and attempts to send all buffered records to the Kinesis stream,
            retrying up to three times on failure.
    """
    def __init__(self, stream_name):
        """
        Initializes the instance with a Kinesis stream client and attempts to create a new Kinesis stream.
        
        Parameters:
            stream_name (str): The name of the Kinesis stream to create.
        
        Attributes:
            stream_name (str): Stores the name of the stream.
            client (KinesisGetSession or None): The Kinesis client session object, or None if initialization failed.
            stream_buffer (list): A buffer list for stream data.
        
        Behavior:
            - Tries to initialize the Kinesis client session.
            - Attempts to create a Kinesis stream with the given name, a single shard, and provisioned mode.
            - Waits for 10 seconds after stream creation to allow the stream to become active.
            - Suppresses exceptions during client initialization and stream creation, printing an error message only if client initialization fails.
        """
        self.stream_name = stream_name
        self.client = None
        self.stream_buffer = []
        try:            
            self.client = KinesisGetSession()
        except Exception:
            print('Kinesis client initialization failed.')

        try:
            self.client.create_stream(
                StreamName=stream_name,
                ShardCount=1,
                StreamModeDetails={
                    'StreamMode': 'PROVISIONED'
                }
            )
            time.sleep(10)
        except Exception as e:
            pass

    def produce(self, record, partitionkey):        
        """
        Adds a JSON-serialized record to the internal buffer and attempts to send all buffered records to an AWS Kinesis stream. Retries up to three times on failure, refreshing the Kinesis client session each time.
        
        Parameters:
            record (dict): The data record to send to the Kinesis stream.
            partitionkey (str): The partition key used by Kinesis to group data records.
        
        Behavior:
            - Serializes the record to a JSON string and encodes it as UTF-8 bytes.
            - Appends the encoded record and partition key to the internal stream buffer.
            - Attempts to send all buffered records to the specified Kinesis stream.
            - On failure, refreshes the Kinesis client session and retries up to three times.
            - Clears the stream buffer after a successful send or after exhausting retries.
        """
        _rec = json.dumps(record)
        self.stream_buffer.append({
            'Data': str(_rec).encode(encoding="UTF-8", errors="strict"),
            'PartitionKey': partitionkey,
        })
        trials = 3
        while trials > 0:
            try:
                self.client.put_records(
                    StreamName=self.stream_name,
                    Records=self.stream_buffer
                )
                break
            except:
                self.client = KinesisGetSession()
                trials -= 1
        self.stream_buffer = []

class KinesisStreamConsumer():
    """
    Class to consume records from an AWS Kinesis stream.
    
    Initializes a connection to the specified Kinesis stream, creating it if it does not exist,
    and manages shard iterators to continuously consume new records from the stream.
    
    Attributes:
        stream_name (str): Name of the Kinesis stream.
        stream_buffer (list): Buffer to store consumed records.
        last_sequence_number (str or None): Sequence number of the last consumed record.
        client (KinesisGetSession): Client session for interacting with Kinesis.
        stream (dict): Description of the Kinesis stream and shard iterators.
    
    Methods:
        get_stream():
            Connects to the Kinesis stream, creates it if necessary, waits for it to become active,
            and initializes shard iterators for reading records.
    
        consume():
            Retrieves records from all shards using the current shard iterators,
            updates the shard iterators, and appends valid records to the stream buffer.
    
    Returns:
        consume() returns True if records were successfully fetched from any shard, False otherwise.
    """
    def __init__(self, stream_name):
        """
        Initializes a new instance with the given stream name.
        
        Parameters:
            stream_name (str): The name of the stream to be processed.
        
        Attributes initialized:
            stream_name (str): Stores the name of the stream.
            stream_buffer (list): A buffer to hold stream data.
            last_sequence_number (int or None): Tracks the last processed sequence number, initialized to None.
        
        Calls:
            get_stream(): Method to retrieve or initialize the stream data.
        """
        self.stream_name = stream_name
        self.stream_buffer = []
        self.last_sequence_number = None
        self.get_stream()

    def get_stream(self):
        """
        Initializes a Kinesis client session, ensures the specified Kinesis stream exists and is active, and sets shard iterators.
        
        This method attempts to create the Kinesis stream if it does not already exist, then repeatedly polls the stream's description until the stream status becomes 'ACTIVE'. For each shard in the stream, it obtains a shard iterator positioned either at the latest record or just after a stored sequence number. If the stored sequence number is invalid, the shard iterator is reset to the latest position.
        
        Returns:
            bool: True if the stream is successfully described, active, and shard iterators are assigned.
        
        Exceptions during stream creation are silently ignored. Failures to describe the stream or obtain shard iterators trigger retries with a new client session.
        """
        self.client = KinesisGetSession()

        try:
            self.client.create_stream(
                StreamName=self.stream_name,
                ShardCount=1,
                StreamModeDetails={
                    'StreamMode': 'PROVISIONED'
                }
            )
            time.sleep(10)
        except Exception as e:
            pass
        
        while True:
            try:
                self.stream = self.client.describe_stream(StreamName=self.stream_name)
                if self.stream and 'StreamDescription' in self.stream:
                    self.stream = self.stream['StreamDescription']
                    i = 0
                    for i in range(len(self.stream['Shards'])):
                        shardid = self.stream['Shards'][i]['ShardId']
                        if self.last_sequence_number is None:
                            shard_iterator = self.client.get_shard_iterator(
                                StreamName=self.stream['StreamName'],
                                ShardId=shardid,
                                ShardIteratorType='LATEST'
                            )
                        else:
                            try:
                                shard_iterator = self.client.get_shard_iterator(
                                    StreamName=self.stream['StreamName'],
                                    ShardId=shardid,
                                    ShardIteratorType='AFTER_SEQUENCE_NUMBER',
                                    StartingSequenceNumber=self.last_sequence_number
                                )
                            except:
                                print('############### RESETING SHARD ITERATOR SEQUENCE ###############')
                                shard_iterator = self.client.get_shard_iterator(
                                    StreamName=self.stream['StreamName'],
                                    ShardId=shardid,
                                    ShardIteratorType='LATEST'
                                )

                        self.stream['Shards'][i]['ShardIterator'] = shard_iterator['ShardIterator']

                if self.stream['StreamStatus'] != 'ACTIVE':
                    raise Exception('Stream status %s' % (self.stream['StreamStatus']))                
                
                return True
            except Exception as e:
                print('Failed connecting StreamDescriptor not found!')
                print('Exception: %s' % (e))
                self.client = KinesisGetSession()
                time.sleep(1)                
        

    def consume(self):
        """
        Consumes records from each shard in the Kinesis stream, updating shard iterators and buffering valid records.
        
        Attempts to retrieve up to 100 records per shard using the current shard iterator. For each record retrieved, it tries to parse the JSON data and appends it to the stream buffer. Updates the last processed sequence number accordingly. If an error occurs while fetching records from a shard, the process stops and returns False. If at least one shard is successfully consumed, returns True.
        
        Returns:
            bool: True if records were successfully consumed from at least one shard, False otherwise.
        """
        success = False

        for i in range(len(self.stream['Shards'])):
            try:
                response = self.client.get_records(
                    ShardIterator=self.stream['Shards'][i]['ShardIterator'],
                    Limit=100)
                success = True
                self.stream['Shards'][i]['ShardIterator'] = response['NextShardIterator']
                if len(response['Records']) > 0:
                    for r in response['Records']:
                        try:
                            rec = json.loads(r['Data'])
                            self.last_sequence_number = r['SequenceNumber']
                            self.stream_buffer.append(rec)
                        except Exception as e:
                            print('Invalid record:'+str(r['Data']))
                            print('Invalid record:'+str(e))

            except Exception as e:
                print('Kinesis consume exception:%s' % (e))
                break

        return success
