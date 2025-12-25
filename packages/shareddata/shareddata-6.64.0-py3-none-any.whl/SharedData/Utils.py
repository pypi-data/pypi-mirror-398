import hashlib
import bson
import pandas as pd
import os
from multiprocessing import resource_tracker

# TODO: CHANGE FIX REGISTER/UNREGISTER TO INCLUDE SEMAPHORES
def remove_shm_from_resource_tracker():
    """
    Monkey-patch the multiprocessing.resource_tracker to prevent it from tracking SharedMemory objects.
    
    This function modifies the internal register and unregister methods of the resource_tracker to ignore
    resources of type "shared_memory". It also removes the cleanup function associated with shared_memory
    from the resource_tracker's cleanup functions. This is useful to avoid issues related to the automatic
    tracking and cleanup of shared memory segments in multiprocessing, as described in:
    https://bugs.python.org/issue38119
    """

    def fix_register(name, rtype):
        """
        Registers a resource with the resource tracker unless the resource type is 'shared_memory'.
        
        Parameters:
            name (str): The name of the resource to register.
            rtype (str): The type of the resource.
        
        Returns:
            The result of the resource_tracker's register method if rtype is not 'shared_memory'; otherwise, None.
        """
        if rtype == "shared_memory":
            return
        return resource_tracker._resource_tracker.register(self, name, rtype)
    resource_tracker.register = fix_register

    def fix_unregister(name, rtype):
        """
        Unregister a resource by name and type, skipping unregistration for shared memory resources.
        
        Parameters:
            name (str): The name of the resource to unregister.
            rtype (str): The type of the resource to unregister.
        
        Returns:
            The result of the resource_tracker's unregister method, or None if the resource type is 'shared_memory'.
        """
        if rtype == "shared_memory":
            return
        return resource_tracker._resource_tracker.unregister(self, name, rtype)
    resource_tracker.unregister = fix_unregister

    if "shared_memory" in resource_tracker._CLEANUP_FUNCS:
        del resource_tracker._CLEANUP_FUNCS["shared_memory"]

if os.name == 'posix':
    from cffi import FFI
    # atomic semaphore operation
    ffi = FFI()
    ffi.cdef("""    
    unsigned char long_compare_and_swap(long mem_addr, long seek, long oldvalue, long newvalue);
    """)
    cpp = ffi.verify("""    
    unsigned char long_compare_and_swap(long mem_addr, long seek, long oldvalue, long newvalue) {
        long * mem_ptr = (long *) mem_addr;
        mem_ptr += seek;
        return __sync_bool_compare_and_swap(mem_ptr, oldvalue, newvalue);
    };    
    """)

elif os.name == "nt": 
    import sys
    sys.path.append(os.path.dirname(__file__))   
    import sharedmutexwin as cpp
    
# check if partition is a date
def datetype(x):
    """
    Determine the granularity of a date string based on its format.
    
    Parameters:
        x (str): A date string which can be empty or in one of the following formats:
                 - 'YYYYMMDD' for day-level precision
                 - 'YYYYMM' for month-level precision
                 - 'YYYY' for year-level precision
    
    Returns:
        str: A string indicating the date granularity:
             - 'day' if the input matches the 'YYYYMMDD' format
             - 'month' if the input matches the 'YYYYMM' format
             - 'year' if the input matches the 'YYYY' format
             - '' (empty string) if the input is empty or does not match any recognized format
    """
    if x == '':
        return ''
    
    if len(x) == 8:
        try:
            pd.to_datetime(x,format='%Y%m%d')
            return 'day'
        except:
            pass

    if len(x) == 6:
        try:                
            pd.to_datetime(x,format='%Y%m')
            return 'month'
        except:
            pass

    if len(x) == 4:
        try:                
            pd.to_datetime(x,format='%Y')
            return 'year'
        except:
            pass

    return ''

from pandas.core.internals import BlockManager, make_block
class BlockManagerUnconsolidated(BlockManager):
    """
    A subclass of BlockManager representing an unconsolidated block manager.
    
    This class overrides consolidation behavior to indicate that blocks are never consolidated.
    It maintains internal flags to reflect this unconsolidated state and provides no-op or
    pass-through implementations for consolidation methods.
    
    Attributes:
        _is_consolidated (bool): Always False, indicating blocks are not consolidated.
        _known_consolidated (bool): Always False, indicating consolidation status is unknown.
    
    Methods:
        _consolidate_inplace(): Does nothing; placeholder for in-place consolidation.
        _consolidate(): Returns the current blocks without performing consolidation.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the object by invoking the BlockManager constructor with the provided arguments.
        
        This method sets the internal state flags `_is_consolidated` and `_known_consolidated` to False,
        indicating that the block manager has not been consolidated or verified as consolidated yet.
        
        Parameters:
            *args: Variable length argument list forwarded to the BlockManager initializer.
            **kwargs: Arbitrary keyword arguments forwarded to the BlockManager initializer.
        """
        BlockManager.__init__(self, *args, **kwargs)
        self._is_consolidated = False
        self._known_consolidated = False

    def _consolidate_inplace(self): pass
    def _consolidate(self): return self.blocks

import numpy as np
def mmaparray2df(arr, indexcols):
    """
    Consolidate the internal data structure in place.
    
    This method updates the current object's state by merging or reorganizing its internal components
    to ensure consistency and optimal structure. It modifies the object directly without creating a new instance.
    
    Note:
    - This is an internal method and should not be called directly from outside the class.
    - The exact consolidation behavior depends on the specific implementation in subclasses or the containing class.
    """
    blocks = []    
    p = 0
    _len = None
    for n in arr.dtype.names[indexcols:]:
        a = arr[n]
        blk = make_block(values=a.reshape((1,len(a))), placement=(p,))
        blocks.append(blk)
        p += 1

    blocks = tuple(blocks)
    columns = pd.Index(arr.dtype.names[indexcols:])
    idxnames = arr.dtype.names[:indexcols]
    idxdtype = [arr.dtype[n] for n in idxnames]
    index = pd.DatetimeIndex(arr['date'])
    if indexcols > 1:
        idxarr = []
        i=0
        for n in idxnames:
            if ('|S' in str(idxdtype[i])):
                decoded = arr[n].astype(str)
                idxarr.append(decoded)
            elif (idxdtype[i] == np.dtype('<M8[ns]')):
                idxarr.append(pd.to_datetime(arr[n]))
            else:
                idxarr.append(arr[n])
            i+=1            
        index = pd.MultiIndex.from_arrays(idxarr,names=idxnames)    
        
    mgr = BlockManagerUnconsolidated(blocks=blocks, axes=[columns, index])
    return pd.DataFrame(mgr, copy=False)

def sort_dict(obj: object) -> object:
    """
    Recursively sort dictionaries by their keys and apply the sorting to nested dictionaries and lists.
    
    For a dictionary input, returns a new dictionary with keys sorted in ascending order, recursively sorting all nested dictionaries and lists.
    For a list input, recursively sorts each element.
    For other data types, returns the object unchanged.
    
    This function is useful for ensuring consistent ordering of dictionary keys, which can aid in hashing or comparing nested data structures.
    
    Args:
        obj (object): The input object to sort, which may be a dictionary, list, or any other data type.
    
    Returns:
        object: A new object with dictionaries sorted by keys recursively, or the original object if it is not a dictionary or list.
    """
    if isinstance(obj, dict):
        return {k: sort_dict(obj[k]) for k in sorted(obj)}
    elif isinstance(obj, list):
        return [sort_dict(item) for item in obj]
    else:
        return obj

def get_hash(obj: dict) -> str:
    """
    Generate a SHA-256 hash for a given dictionary.
    
    This method sorts the dictionary to ensure consistent key order, encodes it into BSON format,
    and computes the SHA-256 hash of the encoded bytes.
    
    Args:
        obj (dict): The dictionary to hash.
    
    Returns:
        str: The hexadecimal SHA-256 hash string of the BSON-encoded sorted dictionary.
    """
    obj = sort_dict(obj)
    return hashlib.sha256(bson.BSON.encode(obj)).hexdigest()
