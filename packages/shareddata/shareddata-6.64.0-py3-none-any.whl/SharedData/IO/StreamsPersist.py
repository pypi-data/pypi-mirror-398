import argparse
import asyncio
import pandas as pd
import time
import multiprocessing
from SharedData.SharedData import SharedData
from SharedData.Logger import Logger

def persist_stream_process(streams):
    """
    Launches an asynchronous event loop to concurrently persist multiple data streams.
    
    Given a list of stream descriptors, this function initializes shared data resources and creates asynchronous tasks to persist each stream's data using aiokafka. Each stream descriptor should be a string formatted as 'user/database/period/source/container/tablename'. The function runs all persistence tasks concurrently within an asyncio event loop until completion.
    """
    shdata = SharedData(__file__, quiet=True)
    async def persist_stream_task():
        """
        Asynchronously creates and runs persistence tasks for multiple data streams.
        
        For each stream descriptor in the global `streams` list, this function:
        - Parses the descriptor into user, database, period, source, container, and tablename.
        - Initializes a stream object with AI Kafka enabled.
        - Initializes a corresponding cache object.
        - Creates an asynchronous task to persist the stream data into the cache.
        
        All tasks are then executed concurrently using `asyncio.gather`.
        
        This function requires the `streams` iterable and the `shdata` module to be defined in the surrounding scope.
        """
        tasks = []
        for stream_descr in streams:
            user, database, period, source, container, tablename = stream_descr.split('/')
            stream = shdata.stream(database, period, source, tablename, user=user, use_aiokafka=True)
            cache = shdata.cache(database, period, source, tablename, user=user)
            tasks.append(asyncio.create_task(stream.async_persist_stream_task(cache)))
        # Run the asyncio tasks concurrently
        await asyncio.gather(*tasks)

    # Run the asyncio event loop
    asyncio.run(persist_stream_task())

def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for configuring the stream cache worker launcher.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments containing:
            - num_process (int): Number of worker processes to spawn (default: 4).
            - stream_paths (List[str]): List of stream paths in USER/DB/PERIOD/SRC/CONTAINER/TABLE format.
    """
    parser = argparse.ArgumentParser(description="Stream cache worker launcher")
    parser.add_argument(
        "--num-process", type=int, default=4,
        help="Number of worker processes to spawn."
    )
    parser.add_argument(
        "--stream-paths", type=str, nargs='+', required=True,        
        help="List of stream paths in USER/DB/PERIOD/SRC/CONTAINER/TABLE format."
    )
    return parser.parse_args()

def main():
    """
    Main function to start and monitor stream persistence processes.
    
    This function parses command-line arguments to determine the number of processes and stream paths to persist. It initializes shared data access and distributes stream partitions evenly across multiple processes, each running the `persist_stream_process` function. It then continuously monitors and logs the persistence rates of each stream by reading counters from cache headers, providing periodic updates every 15 seconds. The function handles graceful termination of all child processes upon receiving a keyboard interrupt.
    """
    args = parse_args()
    # args = argparse.Namespace()
    # args.num_process = 4
    # args.stream_paths = ['master/MarketData/RT/IBKR/cache/TICKS']

    shdata = SharedData("SharedData.IO.StreamsPersist", user='master')
    Logger.log.info('Starting stream persist processes...')    
    
    num_process = args.num_process
    stream_paths = args.stream_paths    
    
    process_streams = {i: [] for i in range(num_process)}
    for s in range(len(stream_paths)):
        stream_descr = stream_paths[s]
        user, database, period, source, container, tablename = stream_descr.split('/')
        stream = shdata.stream(database,period,source,tablename,user=user,use_aiokafka=True)
        for p in range(stream.num_partitions):
            curproc = (s+p) % num_process
            process_streams[curproc].append(stream_descr)
    
    processes = []
    for p in process_streams:
        proc = (multiprocessing.Process(target=persist_stream_process, args=(process_streams[p],)))
        processes.append(proc)
        proc.start()        
        
    Logger.log.info('Processes started!')

     # Initialize cache objects and per-stream stats
    stream_caches = {}
    last_counters = {}
    for stream_descr in stream_paths:
        user, database, period, source, container, tablename = stream_descr.split('/')
        cache = shdata.cache(database, period, source, tablename, user=user)
        stream_caches[stream_descr] = cache
        last_counters[stream_descr] = {
            "cache": int(cache.header.get('cache->counter', 0)),
            "stream_cache": int(cache.header.get('stream->persist-group->persist_counter', 0)),            
        }
    try:
        lasttime = time.time()
        time.sleep(1)
        while True:
            tnow = time.time()
            telapsed = tnow - lasttime
            log_lines = []
            for stream_descr, cache in stream_caches.items():
                prev = last_counters[stream_descr]
                persist_counter = int(cache.header.get('cache->counter', 0))
                stream_persist_counter = int(cache.header.get('stream->persist-group->persist_counter', 0))                

                log_lines.append(
                    f"{stream_descr}: "
                    f"{(persist_counter - prev['cache'])/telapsed:.0f} cache/sec, "
                    f"{(stream_persist_counter - prev['stream_cache'])/telapsed:.0f} stream/sec, "
                    f"{stream_persist_counter} cached msgs"
                )

                # Update previous values:
                last_counters[stream_descr] = {
                    "cache": persist_counter,
                    "stream_cache": stream_persist_counter,
                }
            lasttime = tnow
            Logger.log.debug("#heartbeat# " + " | ".join(log_lines))
            time.sleep(15)
    except KeyboardInterrupt:
        print("Terminating processes...")
        for p in processes:
            p.terminate()
            p.join()

if __name__ == "__main__":
    main()