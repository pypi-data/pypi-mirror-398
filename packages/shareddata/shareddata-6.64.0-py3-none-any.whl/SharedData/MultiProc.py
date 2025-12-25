
# SuperFastPython.com
# load many files concurrently with processes and threads in batch
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
import threading
from cffi import FFI
from tqdm import tqdm
import time
from threading import Thread
from SharedData.Logger import Logger
import queue
from queue import Empty

# USAGE EXAMPLE:
# io_bound(thread_func, iterator, args)
# thread_func:define the task function to run parallel. Ie: read_files,days_trading_from_to
# iteration: single iteration items of parallel task
# args: commom task variables

# thread_func EXAMPLES

# IO BOUND EXAMPLE
# def read_files(iteration, args):
#     fileid = iteration[0]
#     file_list = args[0]
#     fpath = file_list[fileid]
#     df = pd.read_csv(fpath)
#     return [df]

# CPU BOUND EXAMPLE
# def days_trading_from_to(iteration, args):
#     cal = iteration[0]
#     start = iteration[1]
#     end = iteration[2]
#     calendars = args[0]
#     idx = (calendars[cal]>=start) & ((calendars[cal]<=end))
#     return [np.count_nonzero(idx)]

############## MULTI PROCESS MULTI THREAD ORDERED ##############


def io_bound(thread_func, iterator, args, maxproc=None, maxthreads=4):
    """
    Executes an I/O-bound function concurrently by distributing work across multiple processes, each managing a limited number of threads.
    
    This function partitions the input iterable into chunks and assigns each chunk to a separate process within a process pool. Each process runs the specified `thread_func` on its chunk using up to `maxthreads` threads to handle I/O-bound tasks efficiently. The number of worker processes is dynamically determined based on the CPU count, the size of the input iterable, and optional user-defined limits.
    
    Parameters:
        thread_func (callable): The function to execute concurrently on each chunk of data. It should accept the chunk, additional arguments, and the maximum number of threads.
        iterator (list or iterable): The collection of items to be processed.
        args (any): Additional arguments to pass to `thread_func`.
        maxproc (int, optional): Maximum number of processes to use. If None, no explicit limit is applied beyond CPU count and input size.
        maxthreads (int, optional): Maximum number of threads per process. Defaults to 4.
    
    Returns:
        list: A combined list of results returned by `thread_func` from all chunks.
    """
    results = []
    # determine chunksize
    niterator = len(iterator)
    if niterator > 0:
        n_workers = multiprocessing.cpu_count() - 2
        n_workers = min(n_workers, niterator)
        if not maxproc is None:
            n_workers = min(n_workers, maxproc)
        chunksize = round(niterator / n_workers)
        # create the process pool
        with ProcessPoolExecutor(n_workers) as executor:
            futures = list()
            # split the load operations into chunks
            for i in range(0, niterator, chunksize):
                # select a chunk of filenames
                proc_iterator = iterator[i:(i + chunksize)]
                # submit the task
                future = executor.submit(io_bound_process,
                                         thread_func, proc_iterator, args, maxthreads)
                futures.append(future)
            # process all results
            for future in futures:
                # open the file and load the data
                res = future.result()
                results = [*results, *res]
    return results


def io_bound_process(thread_func, proc_iterator, args, maxthreads):
    """
    Executes an I/O-bound function concurrently using a thread pool and aggregates the results.
    
    This function runs the provided `thread_func` across multiple threads, each receiving an item from
    `proc_iterator` and the shared `args`. It limits the number of concurrent threads to `maxthreads`
    and collects all results into a single list.
    
    Parameters:
        thread_func (callable): Function to execute in each thread. It must accept two arguments:
                                an element from `proc_iterator` and `args`.
        proc_iterator (iterable): Iterable supplying input values for each thread execution.
        args (any): Additional argument passed to each call of `thread_func`.
        maxthreads (int): Maximum number of threads to run concurrently.
    
    Returns:
        list: A combined list containing all results returned by each call to `thread_func`.
    """
    results = []
    # create a thread pool
    nthreads = len(proc_iterator)
    nthreads = min(nthreads, maxthreads)
    if nthreads > 0:
        with ThreadPoolExecutor(nthreads) as exe:
            # load files
            futures = [exe.submit(thread_func, iteration, args)
                       for iteration in proc_iterator]
            # collect data
            for future in futures:
                res = future.result()
                results = [*results, *res]

    return results

############## MULTI PROCESS MULTI THREAD UNORDERED ##############

def multiprocess_multithread_workers(thread_func, args, maxproc=2, maxthreads=2):
    """
    Starts multiple multiprocessing workers, each running multiple threads executing a given function.
    
    Parameters:
        thread_func (callable): The function to be executed by each thread within the worker processes.
        args (tuple): Arguments to pass to each thread function.
        maxproc (int, optional): Maximum number of worker processes to spawn. Defaults to 2.
        maxthreads (int, optional): Maximum number of threads per worker process. Defaults to 2.
    
    Returns:
        tuple: A tuple containing:
            - input_queue (multiprocessing.Queue): Queue for input tasks.
            - output_queue (multiprocessing.Queue): Queue for output results.
            - workers (list): List of multiprocessing.Process objects representing the worker processes.
    
    Notes:
        - The number of worker processes is determined by the number of CPU cores minus two, limited by maxproc.
        - Each worker process runs multiple threads executing the provided thread_func.
    """
    input_queue = multiprocessing.Queue()
    output_queue = multiprocessing.Queue()

    nworkers = multiprocessing.cpu_count() - 2
    if not maxproc is None:
        nworkers = min(nworkers, maxproc)
    
    workers = [multiprocessing.Process(target=multi_thread_worker_process,
                                       args=(thread_func, input_queue, output_queue, args, maxthreads))
               for _ in range(nworkers)]

    for w in workers:
        w.start()

    return input_queue, output_queue, workers

# def io_bound_unordered(thread_func, iterator, args, maxproc=None, maxthreads=1):
#     results = []
#     input_queue = multiprocessing.Queue()
#     output_queue = multiprocessing.Queue()
#     niterator = len(iterator)
#     nworkers = multiprocessing.cpu_count() - 2
#     if not maxproc is None:
#         nworkers = min(nworkers, maxproc)
#     if (niterator <= nworkers) \
#             | (niterator <= int(nworkers*maxthreads)):
#         maxthreads = 1
#         nworkers = niterator

#     workers = [multiprocessing.Process(target=multi_thread_worker_process,
#                                        args=(thread_func, input_queue, output_queue, args, maxthreads))
#                for _ in range(nworkers)]

#     for w in workers:
#         w.start()

#     for i in range(niterator):
#         input_queue.put(iterator.iloc[i])

#     desc = '%s(%i proc,%i threads)' % (thread_func.__name__,nworkers,maxthreads)
#     pbar = tqdm(range(niterator), desc=desc)
#     nresults = 0
#     watchdog = time.time()
#     while nresults < niterator:
#         try:
#             output = output_queue.get(block=False)
#             if output:
#                 results.extend(output)
#                 nresults += 1
#                 pbar.update(1)
#                 watchdog = time.time()
#         except Empty:
#             exitloop = False
#             for w in workers:
#                 if not w.is_alive():
#                     Logger.log.error('Worker stopped running %s' % (w.exitcode))
#                     exitloop=True
#                     break
#             if exitloop:
#                 for w in workers:
#                     try:
#                         w.terminate()
#                     except:
#                         pass
#                 raise Exception('Worker stopped running!')

#             if input_queue.qsize() == 0:
#                 if time.time()-watchdog > 300:
#                     Logger.log.error('Watchdog timeout!')
#                     break
#             time.sleep(0.1)
#         except Exception as e:
#             Logger.log.error('io_bound_unordered error %s' % (str(e)))

#     # Signal processes to terminate
#     for _ in range(nworkers):
#         input_queue.put(None)

#     for w in workers:
#         w.join()

#     if not input_queue.empty():
#         raise Exception('Input queue not totally consumed!')
    
#     if not output_queue.empty():
#         raise Exception('Output queue not totally consumed!')

#     return results


def io_bound_unordered(thread_func, iterator, args, maxproc=None, maxthreads=1, timeout=60):
    """
    Executes an I/O-bound function concurrently using multiple processes and threads, processing items from a given iterator in an unordered manner.
    
    Parameters:
        thread_func (callable): The function to be executed by each thread within the worker processes. It should accept items from the input queue and return results.
        iterator (pandas.DataFrame or similar): An iterable collection of items to be processed.
        args (tuple): Additional arguments to pass to the thread_func.
        maxproc (int, optional): Maximum number of worker processes to spawn. Defaults to None, which sets it based on CPU count.
        maxthreads (int, optional): Maximum number of threads per worker process. Defaults to 1.
        timeout (int, optional): Time in seconds to wait before terminating due to inactivity. Defaults to 60.
    
    Returns:
        list: A list containing the aggregated results returned by thread_func from all processed items.
    
    Notes:
        - The function dynamically adjusts the number of worker processes and threads based on the size of the input and CPU availability.
        - Uses multiprocessing.Manager queues for inter-process communication.
        - Displays a progress bar using tqdm to track processing progress.
        - Implements a watchdog timer to detect and handle stalled processing.
        - Ensures proper cleanup of worker
    """
    results = []
    with multiprocessing.Manager() as manager:
        input_queue = manager.Queue()
        output_queue = manager.Queue()
        niterator = len(iterator)
        nworkers = max(1, multiprocessing.cpu_count() - 2)
        if maxproc is not None:
            nworkers = min(nworkers, maxproc)
        if niterator <= nworkers or niterator <= int(nworkers * maxthreads):
            maxthreads = 1
            nworkers = niterator

        workers = [multiprocessing.Process(target=multi_thread_worker_process,
                                           args=(thread_func, input_queue, output_queue, args, maxthreads))
                   for _ in range(nworkers)]

        for w in workers:
            w.start()

        for i in range(niterator):
            input_queue.put(iterator.iloc[i])

        desc = f'{thread_func.__name__}({nworkers} proc,{maxthreads} threads)'
        with tqdm(total=niterator, desc=desc) as pbar:
            nresults = 0
            watchdog = time.time()
            while nresults < niterator:
                try:
                    output = output_queue.get(timeout=1)  # Wait for 1 second
                    if output:
                        results.extend(output)
                        nresults += 1
                        pbar.update(1)
                        watchdog = time.time()
                except Empty:
                    if not any(w.is_alive() for w in workers):
                        Logger.log.error('All workers stopped running')
                        break
                    if input_queue.empty() and time.time() - watchdog > timeout:
                        Logger.log.error('Watchdog timeout!')
                        break
                except Exception as e:
                    Logger.log.error(f'io_bound_unordered error: {str(e)}')

        # Signal processes to terminate
        for _ in range(nworkers):
            input_queue.put(None)

        for w in workers:
            w.join(timeout=5)  # Wait for 5 seconds for each worker to finish
            if w.is_alive():
                w.terminate()

        if not input_queue.empty():
            Logger.log.warning('Input queue not totally consumed!')
        
        if not output_queue.empty():
            Logger.log.warning('Output queue not totally consumed!')

    return results

def multi_thread_worker_process(thread_func, input_queue, output_queue, args, nthreads):
    """
    Creates and starts multiple worker threads to process tasks concurrently.
    
    Each thread runs the `worker_thread` function with the provided `thread_func`,
    `input_queue`, `output_queue`, and additional `args`. The function waits for all
    threads to complete before returning.
    
    Parameters:
        thread_func (callable): The function to be executed by each worker thread.
        input_queue (queue.Queue): Queue from which threads will retrieve tasks.
        output_queue (queue.Queue): Queue where threads will put their results.
        args (tuple): Additional arguments to pass to the `thread_func`.
        nthreads (int): Number of worker threads to create and run.
    """
    threads = [threading.Thread(target=worker_thread,
                                args=(thread_func, input_queue, output_queue, args))
               for _ in range(nthreads)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()


def worker_thread(thread_func, input_queue, output_queue, args):
    """
    Continuously processes items from an input queue using a specified worker function and places the results into an output queue.
    
    Args:
        thread_func (callable): The function to apply to each item retrieved from the input queue.
                                It should accept two arguments: the item and additional args.
        input_queue (queue.Queue): Queue from which items to process are retrieved. A None value signals termination.
        output_queue (queue.Queue): Queue where processed results are placed.
        args (any): Additional arguments passed to the worker function.
    
    Behavior:
        - Retrieves items from input_queue indefinitely until a None value is encountered, which stops the loop.
        - Applies thread_func to each item along with args.
        - Ensures the result is a list; if not, wraps it in a list.
        - Puts the result into output_queue.
        - Logs any exceptions raised during processing and puts [-1] into output_queue to indicate an error.
    """
    while True:
        iteration = input_queue.get()
        if iteration is None:
            break        
        try:
            result = thread_func(iteration, args)
            if not isinstance(result, list):
                result = [result]
            output_queue.put(result)
        except Exception as e:
            Logger.log.error('Error in worker %s : %s ,%s\n' \
                             % (thread_func.__name__, str(iteration),str(e)))
            output_queue.put([-1])
        

################# MULTI PROCESS ORDERED #################


def cpu_bound(thread_func, iterator, args, maxproc=None):
    """
    Executes a CPU-bound function concurrently across multiple processes using a process pool.
    
    This function divides the input iterable into chunks and processes each chunk in parallel using a specified function. It leverages multiple CPU cores to improve performance for CPU-intensive tasks.
    
    Parameters:
        thread_func (callable): The function to be executed in each process. It should accept an iterable chunk and additional arguments.
        iterator (iterable): The iterable containing items to be processed.
        args (tuple): Additional arguments to pass to `thread_func`.
        maxproc (int, optional): Maximum number of worker processes to use. Defaults to None, which allows using up to the number of CPU cores minus two.
    
    Returns:
        list: A combined list of results returned by `thread_func` for all chunks.
    
    Notes:
        - The number of worker processes is determined by the number of CPU cores minus two, capped by the length of the iterator and `maxproc` if provided.
        - The input iterable is split into chunks approximately equal in size to distribute the workload evenly.
    """
    results = []
    # determine chunksize
    niterator = len(iterator)
    if niterator > 0:
        n_workers = multiprocessing.cpu_count() - 2
        n_workers = min(n_workers, niterator)
        if not maxproc is None:
            n_workers = min(n_workers, maxproc)
        chunksize = round(niterator / n_workers)
        # create the process pool
        with ProcessPoolExecutor(n_workers) as executor:
            futures = list()
            # split the load operations into chunks
            for i in range(0, niterator, chunksize):
                # select a chunk of filenames
                proc_iterator = iterator[i:(i + chunksize)]
                # submit the task
                future = executor.submit(
                    cpu_bound_process, thread_func, proc_iterator, args)
                futures.append(future)
            # process all results
            for future in futures:
                # open the file and load the data
                res = future.result()
                results = [*results, *res]
    return results


def cpu_bound_process(thread_func, proc_iterator, args):
    """
    Executes a CPU-bound function over multiple iterations and collects all results into a single list.
    
    Parameters:
    thread_func (callable): A function that accepts an iteration value and additional arguments, returning an iterable of results.
    proc_iterator (iterable): An iterable that provides iteration values to be passed to thread_func.
    args (any): Additional arguments to be passed to thread_func.
    
    Returns:
    list: A combined list of all results produced by thread_func for each iteration.
    """
    results = []
    for iteration in proc_iterator:
        res = thread_func(iteration, args)
        results = [*results, *res]
    return results

############## MULTI PROCESS UNORDERED ##############


def cpu_bound_unordered(thread_func, iterator, args, maxproc=None):
    """
    Executes a CPU-bound function concurrently across multiple processes without preserving the order of results.
    
    This function distributes tasks from the given iterator to a pool of worker processes that run the specified `thread_func`.
    Each worker receives input from an input queue and places results into an output queue. The number of worker processes
    is determined based on the number of CPU cores, the length of the iterator, and an optional maximum process limit.
    
    Parameters:
        thread_func (callable): The function to be executed by each worker process. It should accept the input item,
                                the input queue, the output queue, and additional arguments.
        iterator (iterable): An iterable containing the input data to be processed.
        args (tuple): Additional arguments to pass to the `thread_func`.
        maxproc (int, optional): Maximum number of worker processes to spawn. Defaults to None, which lets the function
                                 decide based on CPU count and iterator length.
    
    Returns:
        list: A list containing all results collected from the worker processes, order not guaranteed.
    
    Notes:
        - Uses multiprocessing queues to distribute tasks and collect results.
        - Uses tqdm to display a progress bar for task completion.
        - Worker processes are signaled to terminate by sending `None` through the input queue.
    """
    results = []
    input_queue = multiprocessing.Queue()
    output_queue = multiprocessing.Queue()
    niterator = len(iterator)
    nworkers = multiprocessing.cpu_count() - 2
    nworkers = min(nworkers, niterator)
    if not maxproc is None:
        nworkers = min(nworkers, maxproc)

    workers = [multiprocessing.Process(target=single_thread_worker_process,
                                       args=(thread_func, input_queue, output_queue, args))
               for _ in range(nworkers)]

    for w in workers:
        w.start()

    for i in range(niterator):
        input_queue.put(iterator[i])

    for i in tqdm(range(niterator), desc='cpu_bound_unordered:'):
        results.extend(output_queue.get())

    # Signal processes to terminate
    for _ in range(niterator):
        input_queue.put(None)

    for w in workers:
        w.join()

    return results


def single_thread_worker_process(thread_func, input_queue, output_queue, args):
    """
    Continuously processes tasks from an input queue using a specified function and places the results into an output queue until a termination signal is received.
    
    Args:
        thread_func (callable): A function that processes each task. It should accept two arguments: the task (iteration) and additional parameters (args).
        input_queue (queue.Queue): Queue from which tasks are retrieved. Receiving None indicates no more tasks and stops processing.
        output_queue (queue.Queue): Queue where processed results are placed.
        args (any): Additional arguments passed to thread_func for processing each task.
    
    The function runs in a loop, fetching tasks from input_queue, processing them with thread_func, and putting the results into output_queue. It terminates when a None value is encountered in input_queue.
    """
    while True:
        iteration = input_queue.get()
        if iteration is None:
            break
        result = thread_func(iteration, args)
        output_queue.put(result)
