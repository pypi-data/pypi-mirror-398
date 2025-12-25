import os
import logging
from datetime import datetime, timezone
import requests
import json
import pandas as pd
import lz4
import lz4.frame as lz4f
import time

class LogHandlerAPI(logging.Handler):
    """
    A custom logging handler that sends log records to a remote server endpoint.
    
    This handler retrieves the endpoint URL and authorization token from the environment variables
    'SHAREDDATA_ENDPOINT' and 'SHAREDDATA_TOKEN', respectively. It formats log records into a JSON
    payload containing the user name (from 'USER_COMPUTER' environment variable), timestamp, logger name,
    log level, and message. The payload is compressed using LZ4 compression before being sent via an
    HTTP POST request to the specified endpoint with appropriate headers.
    
    Raises:
        Exception: If required environment variables ('SHAREDDATA_ENDPOINT' or 'SHAREDDATA_TOKEN') are missing.
    
    Methods:
        emit(record): Sends the given log record to the remote server, handling exceptions and ensuring
                       thread safety with acquire/release calls.
    """
    def __init__(self):
        """
        Initializes the instance by setting up the API endpoint and authentication token.
        
        Raises:
            Exception: If 'SHAREDDATA_ENDPOINT' or 'SHAREDDATA_TOKEN' environment variables are not set.
        
        Sets:
            self.endpoint (str): The API endpoint URL constructed from the 'SHAREDDATA_ENDPOINT' environment variable.
            self.token (str): The authentication token retrieved from the 'SHAREDDATA_TOKEN' environment variable.
        """
        super().__init__()
        if not 'SHAREDDATA_ENDPOINT' in os.environ:
            raise Exception('SHAREDDATA_ENDPOINT not in environment variables')
        self.endpoint = os.environ['SHAREDDATA_ENDPOINT']+'/api/logs'

        if not 'SHAREDDATA_TOKEN' in os.environ:
            raise Exception('SHAREDDATA_TOKEN not in environment variables')
        self.token = os.environ['SHAREDDATA_TOKEN']        

    def emit(self, record):
        """
        Emit a log record by sending it as a compressed JSON payload to a remote server.
        
        This method formats the log record into a JSON object containing the user name (from the USER_COMPUTER environment variable),
        timestamp in ISO 8601 format (UTC), logger name, log level, and the log message with single quotes replaced by double quotes.
        The JSON payload is then compressed using LZ4 compression and sent via an HTTP POST request to a specified endpoint with
        appropriate headers including a custom authorization token.
        
        Thread safety is ensured by acquiring and releasing a lock around the operation.
        
        If an exception occurs during this process, an error message is printed indicating the failure to send the log.
        
        Raises:
            None. Exceptions are caught and handled internally.
        """
        try:
            self.acquire()
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
            body = json.dumps(msg)
            compressed = lz4f.compress(body.encode('utf-8'))
            headers = {
                'Content-Type': 'application/json',
                'Content-Encoding': 'lz4',
                'X-Custom-Authorization': self.token,
            }
            trials = 3
            errmsg = None
            while trials > 0:
                try:
                    response = requests.post(
                        self.endpoint,
                        headers=headers,
                        data=compressed,
                        timeout=15
                    )
                    response.raise_for_status()
                    break
                except Exception as e:
                    trials -= 1
                    errmsg = str(e)
                    time.sleep(1)
            
            if errmsg is not None:
                raise Exception(errmsg)
            
        except Exception as e:
            # self.handleError(record)
            msg = {
                'user_name': user,
                'asctime': asctime,
                'logger_name': record.name,
                'level': record.levelname,
                'message': str(record.msg).replace('\'', '\"'),
            }       
            print(f"Could not send log to server:{msg}\n {e}")
        finally:            
            self.release()