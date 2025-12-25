import argparse
import asyncio
import pandas as pd
import time
import multiprocessing
from SharedData.SharedData import SharedData
from SharedData.Logger import Logger

def cache_stream_process(streams):
    """
    Launches an asynchronous event loop to concurrently process and cache multiple data streams.
    
    Each stream descriptor in the input list should be a string formatted as 'user/database/period/source/container/tablename'. For each stream, an asynchronous caching task is created and run concurrently using asyncio.
    
    Parameters:
        streams (list of str): List of stream descriptor strings specifying the streams to process.
    
    This function initializes shared data access, creates asynchronous tasks for caching each stream, and runs them concurrently until completion.
    """
    shdata = SharedData(__file__, quiet=True)
    async def cache_stream_task():
        """
        Asynchronously creates and runs caching tasks for multiple data streams.
        
        For each stream descriptor in the global `streams` list, this function:
        - Parses the descriptor into user, database, period, source, container, and tablename.
        - Initializes a stream object with aiokafka enabled.
        - Initializes a corresponding cache object.
        - Creates an asynchronous task to cache the stream data.
        
        All tasks are then executed concurrently using `asyncio.gather`.
        
        Assumes `streams` and `shdata` are defined in the global scope.
        """
        tasks = []
        for stream_descr in streams:
            user, database, period, source, container, tablename = stream_descr.split('/')
            stream = shdata.stream(database, period, source, tablename, user=user, use_aiokafka=True)
            cache = shdata.cache(database, period, source, tablename, user=user)
            tasks.append(asyncio.create_task(stream.async_cache_stream_task(cache)))
        # Run the asyncio tasks concurrently
        await asyncio.gather(*tasks)

    # Run the asyncio event loop
    asyncio.run(cache_stream_task())

def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for configuring the stream cache worker launcher.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments containing:
            - num_process (int): Number of worker processes to spawn (default: 4).
            - stream_paths (List[str]): List of stream paths specified in USER/DB/PERIOD/SRC/CONTAINER/TABLE format.
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
    Main function to initialize and manage stream caching processes.
    
    This function parses command-line arguments to determine the number of processes and stream paths to handle. It creates a shared data interface and distributes stream partitions evenly across multiple subprocesses that run the caching logic concurrently. It also initializes cache objects and tracks per-stream statistics, periodically logging cache and stream message rates. The function runs indefinitely until interrupted, at which point it gracefully terminates all subprocesses.
    """
    args = parse_args()
    shdata = SharedData("SharedData.IO.StreamsCache", user='master')
    Logger.log.info('Starting stream cache and persis processes...')    
    
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
        proc = (multiprocessing.Process(target=cache_stream_process, args=(process_streams[p],)))
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
            "stream_cache": int(cache.header.get('stream->cache-group->cache_counter', 0)),            
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
                cache_counter = int(cache.header.get('cache->counter', 0))
                stream_cache_counter = int(cache.header.get('stream->cache-group->cache_counter', 0))                

                log_lines.append(
                    f"{stream_descr}: "
                    f"{(cache_counter - prev['cache'])/telapsed:.0f} cache/sec, "
                    f"{(stream_cache_counter - prev['stream_cache'])/telapsed:.0f} stream/sec, "
                    f"{stream_cache_counter} cached msgs"
                )

                # Update previous values:
                last_counters[stream_descr] = {
                    "cache": cache_counter,
                    "stream_cache": stream_cache_counter,
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