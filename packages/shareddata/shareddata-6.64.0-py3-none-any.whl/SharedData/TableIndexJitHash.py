import numpy as np
from numba import njit

CACHE_JITTED = True

# ============================================================================
# HASH UTILITIES
# ============================================================================

@njit(cache=CACHE_JITTED)
def djb2_hash(str_arr):
    """
    Compute DJB2 hash of a byte array (for string fields).
    
    This is a fast, simple hash function suitable for hash table indexing.
    Stops at null byte (0) terminator.
    """
    hash_val = np.uint64(5381)
    for i in range(len(str_arr)):
        c = np.uint8(str_arr[i])
        if c == 0:
            break
        hash_val = ((hash_val << np.uint64(5)) + hash_val) + c
    return hash_val


@njit(cache=CACHE_JITTED)
def hash_int64(value):
    """Hash an int64 value for composite keys."""
    v = np.uint64(value)
    v = ((v >> np.uint64(16)) ^ v) * np.uint64(0x45d9f3b)
    v = ((v >> np.uint64(16)) ^ v) * np.uint64(0x45d9f3b)
    v = (v >> np.uint64(16)) ^ v
    return v


@njit(cache=CACHE_JITTED)
def hash_float64(value):
    """Hash a float64 value for composite keys."""
    bits = np.array([value], dtype=np.float64).view(np.uint64)[0]
    return hash_int64(np.int64(bits))