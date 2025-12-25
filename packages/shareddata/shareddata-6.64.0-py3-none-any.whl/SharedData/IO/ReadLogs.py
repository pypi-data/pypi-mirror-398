import time
import numpy as np
import os


from SharedData.IO.AWSKinesis import KinesisLogStreamConsumer
from SharedData.Logger import Logger
from SharedData.SharedData import SharedData
shdata = SharedData('SharedData.IO.ReadLogs', user='worker')

SLEEP_TIME = 2


def run():    
    """
    Continuously consumes log data from a Kinesis stream using a KinesisLogStreamConsumer instance.
    
    The function initializes the consumer with an option to save logs to a database based on the 'SAVE_LOGS_DB' environment variable.
    It attempts to connect the consumer and logs the startup status. Then, it enters an infinite loop where it consumes log entries.
    If consumption is successful, it periodically logs a heartbeat message every 15 seconds.
    If consumption fails, it attempts to reconnect the consumer and logs the restart status.
    The loop includes randomized sleep intervals to avoid constant polling.
    
    Environment Variables:
        SAVE_LOGS_DB (str): If set to a truthy value, enables saving logs to the database.
    
    Dependencies:
        - os
        - time
        - numpy as np
        - KinesisLogStreamConsumer
        - Logger
        - SLEEP_TIME (float): Base sleep duration in seconds.
    """
    save_to_db = bool(os.environ.get('SAVE_LOGS_DB', False))
    consumer = KinesisLogStreamConsumer(user='worker', save_to_db=save_to_db)
    lastheartbeat = time.time()
    try:
        if consumer.connect():
            Logger.log.info('Logger reader process STARTED!')
    except Exception as e:
        Logger.log.warning('Logger reader process failed to start! Error: {}'.format(e))

    Logger.log.info('ROUTINE STARTED!')
    while True:
        success = False
        try:
            success = consumer.consume()
            if (success) & (time.time()-lastheartbeat >= 15):
                lastheartbeat = time.time()
                Logger.log.debug('#heartbeat#')
        except:
            pass

        if not success:
            Logger.log.info('Logger reader process error! Restarting...')
            try:
                success = consumer.connect()
            except:
                pass
            if success:
                Logger.log.info('Logger reader process RESTARTED!')
            else:
                Logger.log.info('Logger reader failed RESTARTING!')
                time.sleep(SLEEP_TIME*5)
        else:
            time.sleep(SLEEP_TIME + SLEEP_TIME*np.random.rand() - SLEEP_TIME/2)


if __name__ == "__main__":
    run()
