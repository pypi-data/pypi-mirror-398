from numba.typed import List
import numpy as np
from numba import njit

from SharedData.TableIndexJitHash import djb2_hash, hash_int64, hash_float64, CACHE_JITTED

####################### COMPOSITE INDEX ######################################
@njit(cache=CACHE_JITTED)
def get_date_loc_jit(date, datelastidx, dateprevidx, mindate, periodns, maxids):

    """
    Retrieve a list of indices corresponding to entries for a given date by traversing linked indices backward.
    
    Parameters:
        date (int): The target date as an integer timestamp.
        datelastidx (np.ndarray): Array where each element points to the last index for a date bucket.
        dateprevidx (np.ndarray): Array where each element points to the previous index for the same date bucket.
        mindate (int): The minimum date timestamp used as a reference.
        periodns (int): The period length in nanoseconds used to bucket dates.
        maxids (int): Maximum number of indices to retrieve; if 0, no limit is applied.
    
    Returns:
        list: A list of indices corresponding to entries for the given date, ordered from latest to earliest.
    """
    intdt = np.uint32( (np.uint64(date) - np.uint64(mindate)) // np.uint64(periodns) )
    indexes = list()
            
    if datelastidx[intdt] != -1:
        idx = datelastidx[intdt]
        indexes.append(idx)
        nids = 1
        # Backward traverse through the date indexes using dateprevidx
        while dateprevidx[idx] != -1:
            if (maxids != 0) & (nids >= maxids):
                break
            idx = dateprevidx[idx]
            indexes.append(idx)
            nids += 1

    return indexes

@njit(cache=CACHE_JITTED)
def get_date_loc_gte_jit(startdate, datelastidx, dateprevidx, mindate, periodns, maxids=0):
    """
    Retrieve all indexes corresponding to dates greater than or equal to a specified start date.
    
    Parameters:
    - startdate (int): The starting date threshold.
    - datelastidx (np.ndarray): Array where each element points to the last index for a given date interval.
    - dateprevidx (np.ndarray): Array where each element points to the previous index linked to the same date.
    - mindate (int): The minimum date used as a reference point for date normalization.
    - periodns (int): The length of each date period in nanoseconds.
    - maxids (int, optional): Maximum number of indexes to collect per date. If 0, collect all. Default is 0.
    
    Returns:
    - list: A list of indexes for all dates >= startdate, optionally limited by maxids per date.
    """
    indexes = list()
    N = datelastidx.shape[0]
    startdt = np.uint32((np.uint64(startdate) - np.uint64(mindate)) // np.uint64(periodns))
    for intdt in range(startdt, N):
        if datelastidx[intdt] != -1:
            idx = datelastidx[intdt]
            indexes.append(idx)
            nids = 1
            # Optionally follow backwards
            while dateprevidx[idx] != -1:
                if (maxids != 0) and (nids >= maxids):
                    break
                idx = dateprevidx[idx]
                indexes.append(idx)
                nids += 1
    return indexes

@njit(cache=CACHE_JITTED)
def get_date_loc_lte_jit(enddate, datelastidx, dateprevidx, mindate, periodns, maxids=0):
    """
    Retrieve indexes of data points for all dates less than or equal to a specified end date.
    
    Parameters:
    - enddate (int): Target end date as an integer timestamp.
    - datelastidx (np.ndarray): Array mapping date offsets to the last data index for that date.
    - dateprevidx (np.ndarray): Array mapping each data index to the previous index in the chain.
    - mindate (int): Minimum reference date as an integer timestamp.
    - periodns (int): Length of each period in nanoseconds for offset calculation.
    - maxids (int, optional): Maximum number of indexes to retrieve per date; 0 means no limit. Default is 0.
    
    Returns:
    - list: List of data indexes for all dates <= enddate, limited to maxids per date if specified.
    
    Notes:
    - Dates are converted to offsets relative to mindate and periodns.
    - Uses chain traversal via dateprevidx to collect multiple indexes per date.
    - Optimized with Numba JIT compilation for improved performance.
    """
    indexes = list()
    N = datelastidx.shape[0]
    enddt = np.uint32((np.uint64(enddate) - np.uint64(mindate)) // np.uint64(periodns))
    if enddt > N - 1:
        enddt = N - 1
    for intdt in range(0, enddt + 1):
        if datelastidx[intdt] != -1:
            idx = datelastidx[intdt]
            indexes.append(idx)
            nids = 1
            while dateprevidx[idx] != -1:
                if (maxids != 0) and (nids >= maxids):
                    break
                idx = dateprevidx[idx]
                indexes.append(idx)
                nids += 1
    return indexes

@njit(cache=CACHE_JITTED)
def get_date_loc_gte_lte_jit(startdate, enddate, datelastidx, dateprevidx, mindate, periodns, maxids=0):
    """
    Retrieve all indexes corresponding to dates within the inclusive range [startdate, enddate].
    
    Parameters:
    - startdate (int): The start date as a timestamp or comparable integer.
    - enddate (int): The end date as a timestamp or comparable integer.
    - datelastidx (np.ndarray): Array mapping each date index to the last associated index, with -1 indicating no data.
    - dateprevidx (np.ndarray): Array mapping each index to the previous index in the chain, with -1 indicating the start.
    - mindate (int): The minimum date used as a reference point for indexing.
    - periodns (int): The period length in nanoseconds used to convert dates to indices.
    - maxids (int, optional): Maximum number of indexes to collect per date; if 0, collect all. Default is 0.
    
    Returns:
    - list: A list of indexes for all entries where the date falls between startdate and enddate, inclusive. If maxids > 0, limits the number of indexes per date accordingly.
    """
    indexes = list()
    N = datelastidx.shape[0]
    startdt = np.uint32((np.uint64(startdate) - np.uint64(mindate)) // np.uint64(periodns))
    enddt = np.uint32((np.uint64(enddate) - np.uint64(mindate)) // np.uint64(periodns))
    if startdt > N - 1:
        startdt = N - 1
    if enddt > N - 1:
        enddt = N - 1
    for intdt in range(startdt, enddt + 1):
        if datelastidx[intdt] != -1:
            idx = datelastidx[intdt]
            indexes.append(idx)
            nids = 1
            while dateprevidx[idx] != -1:
                if (maxids != 0) and (nids >= maxids):
                    break
                idx = dateprevidx[idx]
                indexes.append(idx)
                nids += 1
    return indexes

@njit(cache=CACHE_JITTED)
def get_symbol_loc_jit(records, symbollastidx, symbolprevidx, rec, maxids):
    """
    Retrieve the list of record indices corresponding to a given symbol using a hash table with quadratic probing.
    
    Parameters:
    - records (array-like): Array of records, each containing a 'symbol' field.
    - symbollastidx (np.ndarray): Hash table array mapping hashed symbol positions to the last index of that symbol in records.
    - symbolprevidx (np.ndarray): Array mapping each record index to the previous index of the same symbol.
    - rec (array-like): Single-element array containing the record whose symbol is to be located.
    - maxids (int): Maximum number of indices to retrieve; if 0, no limit is applied.
    
    Returns:
    - list: List of indices in records corresponding to the symbol in rec[0], ordered from most recent to older entries.
    """
    n = np.uint32(symbollastidx.size - 1)
    symbol = rec[0]['symbol']
    symbolhash = djb2_hash(symbol)
    h = np.uint32(symbolhash % n)
    indexes = list()
    found = False

    # Find the initial position of the symbol in the hash table
    j = 1
    while symbollastidx[h] != -1:
        idx = symbollastidx[h]
        if records[idx]['symbol'] == symbol:
            indexes.append(idx)
            found = True
            break
        h = np.uint32((h + j ** 2) % n)
        j += 1

    if found:
        nids = 1
        # Backward traverse through the symbol indexes using symbolprevidx
        while symbolprevidx[idx] != -1:
            if (maxids != 0) & (nids >= maxids):
                break
            idx = symbolprevidx[idx]
            indexes.append(idx)
            nids += 1
            

    return indexes

@njit(cache=CACHE_JITTED)
def get_portfolio_loc_jit(records, portlastidx, portprevidx, rec, maxids):
    """
    Retrieve the list of record indices corresponding to a specific portfolio using a hash table with quadratic probing.
    
    Parameters
    ----------
    records : array-like
        An array of records where each record contains a 'portfolio' field.
    portlastidx : numpy.ndarray
        A hash table array storing the last index of each portfolio.
    portprevidx : numpy.ndarray
        An array storing the previous index for each record in the portfolio chain.
    rec : array-like
        A single-element array containing the record whose portfolio is to be searched.
    maxids : int
        The maximum number of indices to retrieve; if 0, retrieves all available indices.
    
    Returns
    -------
    list of int
        A list of indices in `records` corresponding to the portfolio found in `rec`.
    """
    n = np.uint32(portlastidx.size - 1)
    portfolio = rec[0]['portfolio']
    porthash = djb2_hash(portfolio)
    h = np.uint32(porthash % n)
    indexes = list()
    found = False

    # Find the initial position of the symbol in the hash table
    j = 1
    while portlastidx[h] != -1:
        idx = portlastidx[h]
        if records[idx]['portfolio'] == portfolio:
            indexes.append(idx)
            found = True
            break
        h = np.uint32((h + j ** 2) % n)
        j += 1

    if found:
        nids = 1
        # Backward traverse through the symbol indexes using portprevidx
        while portprevidx[idx] != -1:
            if (maxids != 0) & (nids >= maxids):
                break
            idx = portprevidx[idx]
            indexes.append(idx)
            nids += 1
            

    return indexes

@njit(cache=CACHE_JITTED)
def get_tag_loc_jit(records, portlastidx, portprevidx, rec, maxids):    
    """
    Retrieve indices of records matching a given tag using a quadratic probing hash table.
    
    This function searches for all record indices in `records` that have the same tag as the provided `rec` record.
    It uses a quadratic probing approach on the `portlastidx` hash table to find the initial match, then traverses
    backwards through `portprevidx` to collect all matching indices up to `maxids`.
    
    Parameters:
    - records (array-like): Array of records, each with a 'tag' field.
    - portlastidx (np.ndarray): Hash table array storing the last index of each tag; -1 indicates empty slot.
    - portprevidx (np.ndarray): Array storing the previous index for each record to enable backward traversal; -1 indicates no previous.
    - rec (array-like): Single record containing the 'tag' to search for.
    - maxids (int): Maximum number of matching indices to return; 0 means no limit.
    
    Returns:
    - list: List of indices in `records` matching the tag in `rec`, found via hash lookup and backward traversal.
    """
    n = np.uint32(portlastidx.size - 1)
    tag = rec[0]['tag']
    taghash = djb2_hash(tag)
    h = np.uint32(taghash % n)
    indexes = list()
    found = False

    # Find the initial position of the symbol in the hash table
    j = 1
    while portlastidx[h] != -1:
        idx = portlastidx[h]
        if records[idx]['tag'] == tag:
            indexes.append(idx)
            found = True
            break
        h = np.uint32((h + j ** 2) % n)
        j += 1

    if found:
        nids = 1
        # Backward traverse through the symbol indexes using portprevidx
        while portprevidx[idx] != -1:
            if (maxids != 0) & (nids >= maxids):
                break
            idx = portprevidx[idx]
            indexes.append(idx)
            nids += 1
            

    return indexes
