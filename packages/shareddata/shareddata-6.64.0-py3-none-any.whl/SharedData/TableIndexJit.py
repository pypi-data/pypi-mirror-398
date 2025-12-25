from numba.typed import List
import numpy as np
from numba import njit

CACHE_JITTED = True

@njit(cache=CACHE_JITTED)
def djb2_hash(str_arr):
    """
    Computes the DJB2 hash of a given array of bytes.
    
    Parameters:
        str_arr (numpy.ndarray): An array of uint8 representing the input string to hash. The hashing stops if a null byte (0) is encountered.
    
    Returns:
        numpy.uint64: The computed DJB2 hash value as a 64-bit unsigned integer.
    
    Notes:
        This function uses the DJB2 algorithm, which initializes the hash to 5381 and iteratively updates it by multiplying the current hash by 33 and adding the current byte.
        The function is JIT-compiled with Numba for performance optimization.
    """
    hash_val = np.uint64(5381)
    for i in range(len(str_arr)):
        c = np.uint8(str_arr[i])
        if c == 0:
            break
        # Perform the hashing: hash * 33 + c
        hash_val = ((hash_val << np.uint64(5)) + hash_val) + c
    return hash_val

###################### SYMBOL ########################
@njit(cache=CACHE_JITTED)
def create_pkey_symbol_jit(records, count, pkey, start):
    """
    Populate the primary key array `pkey` with indices of unique symbols from `records` using quadratic probing for collision resolution.
    
    Parameters:
    - records (structured array): Array of records containing a 'symbol' field.
    - count (int): The number of records to process.
    - pkey (numpy.ndarray): Array used as a hash table to store indices of unique symbols; initialized with -1.
    - start (int): The starting index in `records` from which to begin processing.
    
    Returns:
    - bool: True if all symbols were inserted without unresolvable collisions; False if a duplicate key collision occurs.
    
    Notes:
    - Uses the djb2 hash function to hash symbols.
    - Employs quadratic probing to resolve hash collisions.
    - Assumes `pkey` size is one greater than the maximum hash value to avoid modulo zero.
    - Decorated with `@njit` for Just-In-Time compilation with caching enabled.
    """
    n = np.uint32(pkey.size-1)
    for i in range(start, count):        
        h1 = djb2_hash(records['symbol'][i])
        h = np.uint32((h1) % n)
        if pkey[h] == -1:
            pkey[h] = i
        else:
            duplicatedkey = True
            j = 1
            while (                    
                    (records[pkey[h]]['symbol'] != records[i]['symbol'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    pkey[h] = i
                    duplicatedkey = False
                    break
                j += 1
            if duplicatedkey:
                return False        

    return True

@njit(cache=CACHE_JITTED)
def get_loc_symbol_jit(records, pkey, keys):
    """
    Finds the indices of specified symbols within a records array using a hash table with quadratic probing.
    
    Parameters
    ----------
    records : numpy structured array
        Array of records containing a 'symbol' field to be matched.
    pkey : numpy.ndarray
        Hash table array with indices into the records array; uses -1 to indicate empty slots.
    keys : numpy structured array
        Array of keys with a 'symbol' field whose locations in records are to be found.
    
    Returns
    -------
    numpy.ndarray
        Array of indices corresponding to the locations of each key's symbol in records, or -1 if not found.
    
    Notes
    -----
    - Uses the djb2_hash function to hash symbols.
    - Employs quadratic probing to resolve hash collisions.
    - Assumes pkey size is one greater than the maximum hash index.
    - Decorated with @njit for Just-In-Time compilation and caching.
    """
    n = np.uint32(pkey.size-1)
    loc = np.empty((keys.size, ))
    for i in range(keys.size):        
        h1 = djb2_hash(keys['symbol'][i])
        h = np.uint32((h1) % n)
        if pkey[h] == -1:
            loc[i] = pkey[h]
        else:
            j = 1
            while (                    
                    (records[pkey[h]]['symbol'] != keys[i]['symbol'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1
            loc[i] = pkey[h]
    return loc

@njit(cache=CACHE_JITTED)
def upsert_symbol_jit(records, count, new_records, pkey, 
                    datelastidx, dateprevidx, mindate, periodns,
                    portlastidx, portprevidx, symbollastidx, symbolprevidx):
    """
    Insert or update records in a hash table using quadratic probing for collision resolution.
    
    Parameters:
    - records (np.ndarray): Array of existing records to be updated or appended.
    - count (int): Current number of records in the records array.
    - new_records (np.ndarray): Array of new records to be inserted or used to update existing records.
    - pkey (np.ndarray): Hash table array mapping hash indices to record indices in `records`.
    - datelastidx, dateprevidx, mindate, periodns, portlastidx, portprevidx, symbollastidx, symbolprevidx:
      Additional indices and parameters related to record fields (not used directly in this function).
    
    Returns:
    - count (int): Updated count of records after insertion/updating.
    - minchgid (int): The smallest index of the record that was changed or inserted.
    - True (bool): A constant boolean indicating successful completion.
    
    Notes:
    - Uses djb2 hash function on the 'symbol' field of new_records for hashing.
    - Employs quadratic probing to resolve hash collisions.
    - Stops inserting new records if the maximum size of the records array is reached.
    """
    minchgid = count
    maxsize = records.size
    nrec = new_records.size
    n = np.uint32(pkey.size-1)

    for i in range(nrec):        
        h1 = djb2_hash(new_records['symbol'][i])
        h = np.uint32((h1) % n)
        found = False

        if pkey[h] != -1:  # hash already exists
            j = 1
            while True:  # check for collision & find a free bucket
                if (records[pkey[h]]['symbol'] == new_records[i]['symbol']):
                    # record exists update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    found = True
                    break
                # collision confirmed jump hash
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1

        if not found:
            # Check space and append new record
            if count >= maxsize:
                break  # max size reached
            else:
                # append new record
                records[count] = new_records[i]                                
                pkey[h] = count                
                minchgid = min(minchgid, count)
                count += 1

    return count, minchgid, True


###################### DATE_SYMBOL ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_symbol_jit(records, count, pkey,
                                datelastidx, dateprevidx, mindate, periodns,
                                symbollastidx, symbolprevidx, start):
    """
    '''
    Creates and updates primary key and indexing arrays for a set of records based on their 'date' and 'symbol' fields.
    
    This function uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    It also maintains linked lists for efficient indexing by date and symbol.
    
    Parameters:
    - records (structured array): Array of records containing at least 'date' and 'symbol' fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - datelastidx (ndarray): Array tracking the last inserted record index for each date bucket, initialized with -1.
    - dateprevidx (ndarray): Array storing the previous record index in the date chain for each record.
    - mindate (int or uint64): Minimum date value used to normalize dates for bucketing.
    - periodns (int or uint64): Period length in nanoseconds used to group dates into buckets.
    - symbollastidx (ndarray): Array tracking the last inserted record index for each symbol bucket, initialized with -1.
    - symbolprevidx (ndarray): Array storing the previous record index in the symbol
    """
    n = np.uint32(pkey.size-1)
    for i in range(start, count):                
        h0 = np.uint64(records['date'][i])
        h1 = djb2_hash(records['symbol'][i])
        h = np.uint32((h0 ^ h1) % n)
        
        if pkey[h] == -1:
            pkey[h] = i
        else:
            duplicatedkey = True
            j = 1
            while (
                    (records[pkey[h]]['date'] != records[i]['date']) |
                    (records[pkey[h]]['symbol'] != records[i]['symbol'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    pkey[h] = i
                    duplicatedkey = False
                    break
                j += 1
            if duplicatedkey:
                return False

        # update date index
        intdt = np.uint32( (np.uint64(records['date'][i]) - np.uint64(mindate)) // np.uint64(periodns) )
        if datelastidx[intdt] == -1:  # date not found
            datelastidx[intdt] = i
            dateprevidx[i] = -1
        else: # found            
            dateprevidx[i] = datelastidx[intdt]
            datelastidx[intdt] = i

        # update symbol index
        hs = np.uint32(h1 % n)
        if symbollastidx[hs] == -1:  # symbol not found
            symbollastidx[hs] = i
            symbolprevidx[i] = -1
        else:
            # check for collision
            found = True
            j = 1
            while (records[i]['symbol'] != records[symbollastidx[hs]]['symbol']):
                hs = np.uint32((hs + j**2) % n)
                if symbollastidx[hs] == -1:
                    symbollastidx[hs] = i
                    symbolprevidx[i] = -1
                    found = False
                    break
                j += 1

            if found:
                symbolprevidx[i] = symbollastidx[hs]
                symbollastidx[hs] = i

    return True

@njit(cache=CACHE_JITTED)
def get_loc_date_symbol_jit(records, pkey, keys):    
    """
    Finds the indices of records matching given date and symbol keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'date' and 'symbol' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with 'date' and 'symbol' fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
    
    Notes:
        - Uses a combination of the date and symbol fields to compute the hash.
        - Employs quadratic probing to resolve hash collisions.
        - Decorated with @njit for JIT compilation to improve performance.
    """
    n = np.uint32(pkey.size-1)
    loc = np.empty((keys.size, ),dtype=np.int64)
    for i in range(keys.size):
        h0 = np.uint64(keys['date'][i])
        h1 = djb2_hash(keys['symbol'][i])
        h = np.uint32((h0 ^ h1) % n)
        if pkey[h] == -1:
            loc[i] = pkey[h]
        else:
            j = 1
            while (
                    (records[pkey[h]]['date'] != keys[i]['date']) |
                    (records[pkey[h]]['symbol'] != keys[i]['symbol'])
            ):
                h = np.uint32((h + j**2) % n)
                if pkey[h] == -1:
                    break
                j += 1
            loc[i] = pkey[h]
    
    return loc

@njit(cache=CACHE_JITTED)
def upsert_date_symbol_jit(records, count, new_records, pkey, 
                           datelastidx, dateprevidx, mindate, periodns,
                           portlastidx, portprevidx, symbollastidx, symbolprevidx):
    """
    '''
    Upserts new records into a hash-indexed structured array with date and symbol linked indices.
    
    This function inserts or updates records in a pre-allocated structured NumPy array `records` using a hash table `pkey` keyed by a combination of date and symbol. It resolves hash collisions via quadratic probing. The function maintains linked lists for efficient indexing by date and symbol, updating `datelastidx`, `dateprevidx`, `symbollastidx`, and `symbolprevidx` arrays accordingly. It also tracks whether the date index remains sorted after insertions.
    
    Parameters:
    - records (np.ndarray): Structured array of existing records with fields including 'date' and 'symbol'.
    - count (int): Current number of valid records in `records`.
    - new_records (np.ndarray): Structured array of new records to be upserted.
    - pkey (np.ndarray): Hash table array mapping hashed keys to record indices; -1 indicates empty slot.
    - datelastidx (np.ndarray): Array storing the last record index for each date bucket.
    - dateprevidx (np.ndarray): Array linking previous records within the same date bucket.
    - mindate (int): Minimum date value used for date bucket calculation.
    - periodns (int): Time
    """
    minchgid = count
    maxsize = records.size
    nrec = new_records.size
    n = np.uint32(pkey.size-1)
    # track last date to check if idx is sorted
    isidxsorted = True
    if count>0:
        lastdate = np.int64(records[count-1]['date'])
    else:
        lastdate = 0    
    for i in range(nrec):
        h0 = np.uint64(new_records['date'][i])
        h1 = djb2_hash(new_records['symbol'][i])
        h = np.uint32((h0 ^ h1) % n)
        found = False

        if pkey[h] != -1:  # hash already exists
            j = 1
            while True:  # check for collision & find a free bucket
                if (records[pkey[h]]['date'] == new_records[i]['date'] and
                   records[pkey[h]]['symbol'] == new_records[i]['symbol']):
                    # record exists update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    found = True
                    break
                # collision confirmed jump hash
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1

        if not found:
            # Check space and append new record
            if count >= maxsize:
                break  # max size reached
            else:
                # append new record
                records[count] = new_records[i]                
                pkey[h] = count

                # update date index
                _lastdate = np.int64(new_records['date'][i])
                if _lastdate<lastdate:
                    isidxsorted = False
                else:
                    lastdate = _lastdate
                intdt = np.uint32( (np.uint64(new_records['date'][i]) - np.uint64(mindate)) // np.uint64(periodns) )
                if datelastidx[intdt] == -1:  # date not found
                    datelastidx[intdt] = count
                    dateprevidx[count] = -1
                else: # found            
                    dateprevidx[count] = datelastidx[intdt]
                    datelastidx[intdt] = count

                # update symbol index
                hs = np.uint32(h1 % n)
                if symbollastidx[hs] == -1:  # symbol not found
                    symbollastidx[hs] = count
                    symbolprevidx[count] = -1
                else:
                    # check for collision and find the appropriate bucket
                    found_symbol = True
                    j = 1
                    while records[symbollastidx[hs]]['symbol'] != new_records[i]['symbol']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if symbollastidx[hs] == -1:
                            symbollastidx[hs] = count
                            symbolprevidx[count] = -1
                            found_symbol = False
                            break
                        j += 1

                    if found_symbol:
                        symbolprevidx[count] = symbollastidx[hs]
                        symbollastidx[hs] = count

                minchgid = min(minchgid, count)
                count += 1

    return count, minchgid, isidxsorted


###################### DATE_TAG_SYMBOL ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_tag_symbol_jit(records, count, pkey, 
                                    datelastidx, dateprevidx, mindate, periodns, 
                                    taglastidx, tagprevidx, symbollastidx, symbolprevidx, start):
    """
    '''
    Creates and updates primary key hash table and linked indices for 'date', 'tag', and 'symbol' fields in a structured record array.
    
    Uses quadratic probing to resolve hash collisions when inserting records into the primary key hash table. Also maintains linked lists for each unique date, tag, and symbol to enable efficient lookups and updates.
    
    Parameters:
    - records (np.ndarray): Structured array with fields 'date', 'tag', and 'symbol'.
    - count (int): Number of records to process.
    - pkey (np.ndarray): Primary key hash table array, initialized with -1 indicating empty slots.
    - datelastidx (np.ndarray): Array tracking the last inserted record index for each date bucket, initialized with -1.
    - dateprevidx (np.ndarray): Array storing the previous record index in the linked list for each record's date.
    - mindate (int or np.uint64): Minimum date value used to normalize dates for bucketing.
    - periodns (int or np.uint64): Period length in nanoseconds used to bucket dates.
    - taglastidx (np.ndarray): Array tracking the last inserted record index for each tag bucket, initialized with -1.
    - tagprevidx (np.ndarray): Array storing the previous record index in the linked
    """
    n = np.uint32(pkey.size-1)
    for i in range(start, count):        
        h0 = np.uint64(records['date'][i])
        h1 = djb2_hash(records['tag'][i])
        h2 = djb2_hash(records['symbol'][i])
        h = np.uint32((h0 ^ h1 ^ h2) % n)
        
        if pkey[h] == -1:
            pkey[h] = i
        else:
            duplicatedkey = True
            j = 1
            while (
                    (records[pkey[h]]['date'] != records[i]['date']) |
                    (records[pkey[h]]['tag'] != records[i]['tag']) |
                    (records[pkey[h]]['symbol'] != records[i]['symbol'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    pkey[h] = i
                    duplicatedkey = False
                    break
                j += 1
            if duplicatedkey:
                return False

        # update date index
        intdt = np.uint32( (np.uint64(records['date'][i]) - np.uint64(mindate)) // np.uint64(periodns) )
        if datelastidx[intdt] == -1:  # date not found
            datelastidx[intdt] = i
            dateprevidx[i] = -1
        else: # found            
            dateprevidx[i] = datelastidx[intdt]
            datelastidx[intdt] = i
            
        # update tag index
        hs = np.uint32(h1 % n)
        if taglastidx[hs] == -1:  # tag not found
            taglastidx[hs] = i
            tagprevidx[i] = -1
        else:
            # check for collision
            found = True
            j = 1
            while (records[i]['tag'] != records[taglastidx[hs]]['tag']):
                hs = np.uint32((hs + j**2) % n)
                if taglastidx[hs] == -1:
                    taglastidx[hs] = i
                    tagprevidx[i] = -1
                    found = False
                    break
                j += 1

            if found:
                tagprevidx[i] = taglastidx[hs]
                taglastidx[hs] = i

        # update symbol index
        hs = np.uint32(h2 % n)
        if symbollastidx[hs] == -1:  # symbol not found
            symbollastidx[hs] = i
            symbolprevidx[i] = -1
        else:
            # check for collision
            found = True
            j = 1
            while (records[i]['symbol'] != records[symbollastidx[hs]]['symbol']):
                hs = np.uint32((hs + j**2) % n)
                if symbollastidx[hs] == -1:
                    symbollastidx[hs] = i
                    symbolprevidx[i] = -1
                    found = False
                    break
                j += 1

            if found:
                symbolprevidx[i] = symbollastidx[hs]
                symbollastidx[hs] = i

    return True

@njit(cache=CACHE_JITTED)
def get_loc_date_tag_symbol_jit(records, pkey, keys):
    """
    Locate indices of specified keys in a hash table using quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array of records with fields 'date', 'tag', and 'symbol'.
        pkey (np.ndarray): Hash table array where each element is an index into `records` or -1 if empty.
        keys (np.ndarray): Structured array of keys with fields 'date', 'tag', and 'symbol' to find in the hash table.
    
    Returns:
        np.ndarray: Array of indices in `pkey` corresponding to each key in `keys`. Returns -1 if a key is not found.
    
    Details:
        - Combines 'date', 'tag', and 'symbol' fields into a hash using XOR of djb2 hashes.
        - Resolves collisions via quadratic probing.
        - Assumes `pkey` size is one greater than the maximum hash index.
    """
    n = np.uint32(pkey.size-1)
    loc = np.empty((keys.size, ))
    for i in range(keys.size):
        h0 = np.uint64(keys['date'][i])
        h1 = djb2_hash(keys['tag'][i])
        h2 = djb2_hash(keys['symbol'][i])
        h = np.uint32((h0 ^ h1 ^ h2) % n)
        if pkey[h] == -1:
            loc[i] = pkey[h]
        else:
            j = 1
            while (
                    (records[pkey[h]]['date'] != keys[i]['date']) |
                    (records[pkey[h]]['tag'] != keys[i]['tag']) |
                    (records[pkey[h]]['symbol'] != keys[i]['symbol'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1
            loc[i] = pkey[h]
    return loc

@njit(cache=CACHE_JITTED)
def upsert_date_tag_symbol_jit(records, count, new_records, pkey, 
                            datelastidx, dateprevidx, mindate, periodns,
                            taglastidx, tagprevidx, symbollastidx, symbolprevidx):

    """
    '''
    Insert or update records in a structured array indexed by a composite key of date, tag, and symbol, maintaining multiple linked hash indices for efficient lookups.
    
    Parameters:
    - records (np.ndarray): Structured array containing existing records with fields including 'date', 'tag', and 'symbol'.
    - count (int): Current number of valid records in `records`.
    - new_records (np.ndarray): Structured array of new records to be inserted or updated.
    - pkey (np.ndarray): Primary key hash table mapping hashed composite keys to record indices.
    - datelastidx (np.ndarray): Array indexing the last record for each date bucket.
    - dateprevidx (np.ndarray): Array linking previous records in the same date bucket.
    - mindate (int): Minimum date value used for date bucket calculation.
    - periodns (int): Period length in nanoseconds used for date bucketing.
    - taglastidx (np.ndarray): Hash table indexing the last record for each tag bucket.
    - tagprevidx (np.ndarray): Array linking previous records in the same tag bucket.
    - symbollastidx (np.ndarray): Hash table indexing the last record for each symbol bucket.
    - symbolprevidx (np.ndarray): Array linking previous records in the same symbol bucket.
    """
    minchgid = count
    maxsize = records.size
    nrec = new_records.size
    n = np.uint32(pkey.size-1)
    # track last date to check if idx is sorted
    isidxsorted = True
    if count>0:
        lastdate = np.int64(records[count-1]['date'])
    else:
        lastdate = 0    
    for i in range(nrec):
        h0 = np.uint64(new_records['date'][i])
        h1 = djb2_hash(new_records['tag'][i])
        h2 = djb2_hash(new_records['symbol'][i])
        h = np.uint32((h0 ^ h1 ^ h2) % n)
        found = False

        if pkey[h] != -1:  # hash already exists
            j = 1
            while True:  # check for collision & find a free bucket
                if (records[pkey[h]]['date'] == new_records[i]['date'] and
                   records[pkey[h]]['tag'] == new_records[i]['tag'] and
                   records[pkey[h]]['symbol'] == new_records[i]['symbol']):
                    # record exists, update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    found = True
                    break
                # collision confirmed, jump hash
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1

        if not found:
            # Check space and append new record
            if count >= maxsize:
                break  # max size reached
            else:
                # append new record
                records[count] = new_records[i]                
                pkey[h] = count

                 # update date index
                _lastdate = np.int64(new_records['date'][i])
                if _lastdate<lastdate:
                    isidxsorted = False
                else:
                    lastdate = _lastdate
                intdt = np.uint32( (np.uint64(new_records['date'][i]) - np.uint64(mindate)) // np.uint64(periodns) )                
                if datelastidx[intdt] == -1:  # date not found
                    datelastidx[intdt] = count
                    dateprevidx[count] = -1
                else: # found            
                    dateprevidx[count] = datelastidx[intdt]
                    datelastidx[intdt] = count
                
                # update tag index
                hs = np.uint32(h1 % n)
                if taglastidx[hs] == -1:  # tag not found
                    taglastidx[hs] = count
                    tagprevidx[count] = -1
                else:
                    # check for collision and find the appropriate bucket
                    found_tag = True
                    j = 1
                    while records[taglastidx[hs]]['tag'] != new_records[i]['tag']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if taglastidx[hs] == -1:
                            taglastidx[hs] = count
                            tagprevidx[count] = -1
                            found_tag = False
                            break
                        j += 1

                    if found_tag:
                        tagprevidx[count] = taglastidx[hs]
                        taglastidx[hs] = count

                # update symbol index
                hs = np.uint32(h2 % n)
                if symbollastidx[hs] == -1:  # symbol not found
                    symbollastidx[hs] = count
                    symbolprevidx[count] = -1
                else:
                    # check for collision and find the appropriate bucket
                    found_symbol = True
                    j = 1
                    while records[symbollastidx[hs]]['symbol'] != new_records[i]['symbol']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if symbollastidx[hs] == -1:
                            symbollastidx[hs] = count
                            symbolprevidx[count] = -1
                            found_symbol = False
                            break
                        j += 1

                    if found_symbol:
                        symbolprevidx[count] = symbollastidx[hs]
                        symbollastidx[hs] = count

                minchgid = min(minchgid, count)
                count += 1

    return count, minchgid, isidxsorted


###################### DATE_SYMBOL_SYMBOL1 ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_symbol_symbol1_jit(records, count, pkey, 
                                        datelastidx, dateprevidx, mindate, periodns, 
                                        symbollastidx, symbolprevidx, start):
    """
    '''
    Creates and updates primary key and index mappings for records based on date and symbol fields using a custom hashing and quadratic probing method.
    
    Parameters:
        records (structured array): Array of records with fields 'date', 'symbol', and 'symbol1'.
        count (int): Number of records to process.
        pkey (np.ndarray): Array used as a hash table for primary keys, initialized with -1.
        datelastidx (np.ndarray): Array tracking the last index for each date bucket, initialized with -1.
        dateprevidx (np.ndarray): Array storing previous indices for records sharing the same date.
        mindate (int or np.uint64): Minimum date value used for date normalization.
        periodns (int or np.uint64): Period length in nanoseconds for date bucketing.
        symbollastidx (np.ndarray): Array tracking the last index for each symbol hash bucket, initialized with -1.
        symbolprevidx (np.ndarray): Array storing previous indices for records sharing the same symbol.
        start (int): Starting index in records from which to begin processing.
    
    Returns:
        bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
    
    Notes:
        - Uses a combined hash of date
    """
    n = np.uint32(pkey.size-1)
    for i in range(start, count):        
        if records['symbol'][i] != records['symbol1'][i]:
            h0 = np.uint64(records['date'][i])
            h1 = djb2_hash(records['symbol'][i])
            h2 = djb2_hash(records['symbol1'][i])
            h = np.uint32((h0 ^ h1 ^ h2) % n)
        else:
            h0 = np.uint64(records['date'][i])
            h1 = djb2_hash(records['symbol'][i])
            h = np.uint32((h0 ^ h1) % n)
        if pkey[h] == -1:
            pkey[h] = i
        else:
            duplicatedkey = True
            j = 1
            while (
                    (records[pkey[h]]['date'] != records[i]['date']) |
                    (records[pkey[h]]['symbol'] != records[i]['symbol']) |
                    (records[pkey[h]]['symbol1'] != records[i]['symbol1'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    pkey[h] = i
                    duplicatedkey = False
                    break
                j += 1
            if duplicatedkey:
                return False

        # update date index
        intdt = np.uint32( (np.uint64(records['date'][i]) - np.uint64(mindate)) // np.uint64(periodns) )
        if datelastidx[intdt] == -1:  # date not found
            datelastidx[intdt] = i
            dateprevidx[i] = -1
        else: # found            
            dateprevidx[i] = datelastidx[intdt]
            datelastidx[intdt] = i

        # update symbol index
        hs = np.uint32(h1 % n)
        if symbollastidx[hs] == -1:  # symbol not found
            symbollastidx[hs] = i
            symbolprevidx[i] = -1
        else:
            # check for collision
            found = True
            j = 1
            while (records[i]['symbol'] != records[symbollastidx[hs]]['symbol']):
                hs = np.uint32((hs + j**2) % n)
                if symbollastidx[hs] == -1:
                    symbollastidx[hs] = i
                    symbolprevidx[i] = -1
                    found = False
                    break
                j += 1

            if found:
                symbolprevidx[i] = symbollastidx[hs]
                symbollastidx[hs] = i

    return True

@njit(cache=CACHE_JITTED)
def get_loc_date_symbol_symbol1_jit(records, pkey, keys):
    """
    Compute the location indices in the primary key array for given keys using a custom hashing and quadratic probing.
    
    Parameters
    ----------
    records : numpy structured array
        Array of records containing fields 'date', 'symbol', and 'symbol1'.
    pkey : numpy array of int32
        Primary key array used for indexing, where -1 indicates an empty slot.
    keys : numpy structured array
        Array of keys with fields 'date', 'symbol', and 'symbol1' to locate in records.
    
    Returns
    -------
    loc : numpy array of float64
        Array of location indices corresponding to each key in `keys`. If a key is not found, the location is -1.
    
    Notes
    -----
    - Uses a custom hash function combining date and symbol fields.
    - Applies quadratic probing to resolve hash collisions.
    - Assumes `djb2_hash` is a predefined hash function for strings.
    - Decorated with `@njit` for JIT compilation with caching enabled.
    """
    n = np.uint32(pkey.size-1)
    loc = np.empty((keys.size, ))
    for i in range(keys.size):
        if keys['symbol'][i] != keys['symbol1'][i]:
            h0 = np.uint64(keys['date'][i])
            h1 = djb2_hash(keys['symbol'][i])
            h2 = djb2_hash(keys['symbol1'][i])
            h = np.uint32((h0 ^ h1 ^ h2) % n)
        else:
            h0 = np.uint64(keys['date'][i])
            h1 = djb2_hash(keys['symbol'][i])
            h = np.uint32((h0 ^ h1) % n)
        if pkey[h] == -1:
            loc[i] = pkey[h]
        else:
            j = 1
            while (
                    (records[pkey[h]]['date'] != keys[i]['date']) |
                    (records[pkey[h]]['symbol'] != keys[i]['symbol']) |
                    (records[pkey[h]]['symbol1'] != keys[i]['symbol1'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1
            loc[i] = pkey[h]
    return loc

@njit(cache=CACHE_JITTED)
def upsert_date_symbol_symbol1_jit(records, count, new_records, pkey, 
                                   datelastidx, dateprevidx, mindate, periodns,
                                   portlastidx, portprevidx, symbollastidx, symbolprevidx):
    """
    '''
    Insert or update records in a hash-indexed structured array using composite keys of date, symbol, and symbol1.
    
    This function performs an "upsert" operation on the `records` array: it updates existing records if a matching composite key is found, or inserts new records if not. It uses quadratic probing to resolve hash collisions in the primary hash table (`pkey`). Additionally, it maintains auxiliary linked-list style indices for efficient lookups by date and symbol.
    
    Parameters:
    - records (np.ndarray): Structured array of existing records with fields including 'date', 'symbol', and 'symbol1'.
    - count (int): Current number of valid records in `records`.
    - new_records (np.ndarray): Structured array of new records to be upserted.
    - pkey (np.ndarray): Hash table array mapping hashed keys to indices in `records`.
    - datelastidx (np.ndarray): Array indexing the last record for each date bucket.
    - dateprevidx (np.ndarray): Array linking records with the same date in a linked-list manner.
    - mindate (int): Minimum date value used for date indexing.
    - periodns (int): Period length in nanoseconds used to bucket dates.
    - portlastidx (np.ndarray): Unused in this function
    """
    minchgid = count
    maxsize = records.size
    nrec = new_records.size
    n = np.uint32(pkey.size-1)
    # track last date to check if idx is sorted
    isidxsorted = True
    if count>0:
        lastdate = np.int64(records[count-1]['date'])
    else:
        lastdate = 0    
    for i in range(nrec):
        if new_records['symbol'][i] != new_records['symbol1'][i]:
            h0 = np.uint64(new_records['date'][i])
            h1 = djb2_hash(new_records['symbol'][i])
            h2 = djb2_hash(new_records['symbol1'][i])
            h = np.uint32((h0 ^ h1 ^ h2) % n)
        else:
            h0 = np.uint64(new_records['date'][i])
            h1 = djb2_hash(new_records['symbol'][i])
            h = np.uint32((h0 ^ h1) % n)
        found = False

        if pkey[h] != -1:  # hash already exists
            j = 1
            while True:  # check for collision & find a free bucket
                if (records[pkey[h]]['date'] == new_records[i]['date'] and
                   records[pkey[h]]['symbol'] == new_records[i]['symbol'] and
                        records[pkey[h]]['symbol1'] == new_records[i]['symbol1']):
                    # record exists update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    found = True
                    break
                # collision confirmed jump hash
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1

        if not found:
            # Check space and append new record
            if count >= maxsize:
                break  # max size reached
            else:
                # append new record
                records[count] = new_records[i]                
                pkey[h] = count

                 # update date index
                _lastdate = np.int64(new_records['date'][i])
                if _lastdate<lastdate:
                    isidxsorted = False
                else:
                    lastdate = _lastdate
                intdt = np.uint32( (np.uint64(new_records['date'][i]) - np.uint64(mindate)) // np.uint64(periodns) )                
                if datelastidx[intdt] == -1:  # date not found
                    datelastidx[intdt] = count
                    dateprevidx[count] = -1
                else: # found            
                    dateprevidx[count] = datelastidx[intdt]
                    datelastidx[intdt] = count

                # update symbol index
                hs = np.uint32(h1 % n)
                if symbollastidx[hs] == -1:  # symbol not found
                    symbollastidx[hs] = count
                    symbolprevidx[count] = -1
                else:
                    # check for collision and find the appropriate bucket
                    found_symbol = True
                    j = 1
                    while records[symbollastidx[hs]]['symbol'] != new_records[i]['symbol']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if symbollastidx[hs] == -1:
                            symbollastidx[hs] = count
                            symbolprevidx[count] = -1
                            found_symbol = False
                            break
                        j += 1

                    if found_symbol:
                        symbolprevidx[count] = symbollastidx[hs]
                        symbollastidx[hs] = count

                minchgid = min(minchgid, count)
                count += 1

    return count, minchgid, isidxsorted


###################### DATE_PORTFOLIO ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_portfolio_jit(records, count, pkey, 
                                   datelastidx, dateprevidx, mindate, periodns, 
                                   portlastidx, portprevidx, start):
    """
    '''
    Creates and updates hash-based indices for a portfolio dataset to enable fast lookups by primary key, date, and portfolio.
    
    Parameters:
    - records (structured array): Array of records with fields 'date' and 'portfolio'.
    - count (int): Number of records to process starting from 'start'.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1.
    - datelastidx (ndarray): Array tracking the last index for each date bucket, initialized with -1.
    - dateprevidx (ndarray): Array storing the previous index for each record in the date chain.
    - mindate (int or uint64): The minimum date value used to normalize dates.
    - periodns (int or uint64): The period length in nanoseconds used to bucket dates.
    - portlastidx (ndarray): Array tracking the last index for each portfolio hash bucket, initialized with -1.
    - portprevidx (ndarray): Array storing the previous index for each record in the portfolio chain.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were inserted without primary key collisions; False if a duplicate primary key was detected.
    
    Behavior:
    - Uses double hashing with
    """
    n = np.uint32(pkey.size-1)
    for i in range(start, count):        
        h0 = np.uint64(records['date'][i])
        h1 = djb2_hash(records['portfolio'][i])
        h = np.uint32((h0 ^ h1) % n)
        if pkey[h] == -1:
            pkey[h] = i
        else:
            duplicatedkey = True
            j = 1
            while (
                    (records[pkey[h]]['date'] != records[i]['date']) |
                    (records[pkey[h]]['portfolio'] != records[i]['portfolio'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    pkey[h] = i
                    duplicatedkey = False
                    break
                j += 1
            if duplicatedkey:
                return False
        
        # update date index
        intdt = np.uint32( (np.uint64(records['date'][i]) - np.uint64(mindate)) // np.uint64(periodns) )
        if datelastidx[intdt] == -1:  # date not found
            datelastidx[intdt] = i
            dateprevidx[i] = -1
        else: # found            
            dateprevidx[i] = datelastidx[intdt]
            datelastidx[intdt] = i

        # update port index
        hs = np.uint32(h1 % n)
        if portlastidx[hs] == -1:  # port not found
            portlastidx[hs] = i
            portprevidx[i] = -1
        else:
            # check for collision
            found = True
            j = 1
            while (records[i]['portfolio'] != records[portlastidx[hs]]['portfolio']):
                hs = np.uint32((hs + j**2) % n)
                if portlastidx[hs] == -1:
                    portlastidx[hs] = i
                    portprevidx[i] = -1
                    found = False
                    break
                j += 1

            if found:
                portprevidx[i] = portlastidx[hs]
                portlastidx[hs] = i

    return True

@njit(cache=CACHE_JITTED)
def get_loc_date_portfolio_jit(records, pkey, keys):
    """
    Finds the indices in `records` corresponding to each entry in `keys` using a quadratic probing hash lookup.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'date' and 'portfolio' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in `records`. Contains -1 for empty slots.
        keys (np.ndarray): Structured array of keys with 'date' and 'portfolio' fields to look up in `records`.
    
    Returns:
        np.ndarray: Array of indices in `records` corresponding to each key in `keys`. If a key is not found, the corresponding index is -1.
    
    Notes:
        - Uses a combination of XOR and djb2 hash for hashing 'date' and 'portfolio' fields.
        - Resolves collisions using quadratic probing.
        - Assumes `pkey` size is one more than the maximum index in `records`.
        - Decorated with `@njit` for Just-In-Time compilation with caching enabled.
    """
    n = np.uint32(pkey.size-1)
    loc = np.empty((keys.size, ))
    for i in range(keys.size):
        h0 = np.uint64(keys['date'][i])
        h1 = djb2_hash(keys['portfolio'][i])
        h = np.uint32((h0 ^ h1) % n)
        if pkey[h] == -1:
            loc[i] = pkey[h]
        else:
            j = 1
            while (
                    (records[pkey[h]]['date'] != keys[i]['date']) |
                    (records[pkey[h]]['portfolio'] != keys[i]['portfolio'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1
            loc[i] = pkey[h]
    return loc

@njit(cache=CACHE_JITTED)
def upsert_date_portfolio_jit(records, count, new_records, pkey, 
                              datelastidx, dateprevidx, mindate, periodns,
                              portlastidx, portprevidx, symbollastidx, symbolprevidx):
    """
    '''
    Insert or update records in a portfolio dataset using a hash-based approach with quadratic probing for collision resolution.
    
    Parameters:
    - records (np.ndarray): Structured array of existing records with fields including 'date' and 'portfolio'.
    - count (int): Current number of valid records in `records`.
    - new_records (np.ndarray): Structured array of new records to be upserted.
    - pkey (np.ndarray): Hash table array mapping hashed keys to indices in `records`.
    - datelastidx (np.ndarray): Array tracking the last record index for each date bucket.
    - dateprevidx (np.ndarray): Array linking records with the previous record index for the same date.
    - mindate (int): Minimum date value used for date indexing.
    - periodns (int): Period length in nanoseconds used to bucket dates.
    - portlastidx (np.ndarray): Array tracking the last record index for each portfolio bucket.
    - portprevidx (np.ndarray): Array linking records with the previous record index for the same portfolio.
    - symbollastidx (np.ndarray): (Unused in this function but presumably for symbol indexing.)
    - symbolprevidx (np.ndarray): (Unused in this function but presumably for symbol indexing.)
    
    Returns:
    - count (int): Updated
    """
    minchgid = count
    maxsize = records.size
    nrec = new_records.size
    n = np.uint32(pkey.size-1)
    # track last date to check if idx is sorted
    isidxsorted = True
    if count>0:
        lastdate = np.int64(records[count-1]['date'])
    else:
        lastdate = 0    
    for i in range(nrec):
        h0 = np.uint64(new_records['date'][i])
        h1 = djb2_hash(new_records['portfolio'][i])
        h = np.uint32((h0 ^ h1) % n)
        found = False

        if pkey[h] != -1:  # hash already exists
            j = 1
            while True:  # check for collision & find a free bucket
                if (records[pkey[h]]['date'] == new_records[i]['date'] and
                   records[pkey[h]]['portfolio'] == new_records[i]['portfolio']):
                    # record exists update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    found = True
                    break
                # collision confirmed jump hash
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1

        if not found:
            # Check space and append new record
            if count >= maxsize:
                break  # max size reached
            else:
                # append new record
                records[count] = new_records[i]                
                pkey[h] = count
                
                # update date index
                _lastdate = np.int64(new_records['date'][i])
                if _lastdate<lastdate:
                    isidxsorted = False
                else:
                    lastdate = _lastdate
                intdt = np.uint32( (np.uint64(new_records['date'][i]) - np.uint64(mindate)) // np.uint64(periodns) )                
                if datelastidx[intdt] == -1:  # date not found
                    datelastidx[intdt] = count
                    dateprevidx[count] = -1
                else: # found            
                    dateprevidx[count] = datelastidx[intdt]
                    datelastidx[intdt] = count

                # update portfolio index
                hs = np.uint32(h1 % n)
                if portlastidx[hs] == -1:  # portfolio not found
                    portlastidx[hs] = count
                    portprevidx[count] = -1
                else:
                    # check for collision and find the appropriate bucket
                    found_portfolio = True
                    j = 1
                    while records[portlastidx[hs]]['portfolio'] != new_records[i]['portfolio']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if portlastidx[hs] == -1:
                            portlastidx[hs] = count
                            portprevidx[count] = -1
                            found_portfolio = False
                            break
                        j += 1

                    if found_portfolio:
                        portprevidx[count] = portlastidx[hs]
                        portlastidx[hs] = count

                minchgid = min(minchgid, count)
                count += 1

    return count, minchgid, isidxsorted


###################### DATE_PORTFOLIO_SYMBOL ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_portfolio_symbol_jit(records, count, pkey, 
                                          datelastidx, dateprevidx, mindate, periodns,
                                          portlastidx, portprevidx, symbollastidx, symbolprevidx, start):
    """
    '''
    Creates and updates hash-based indices for a subset of records keyed by a composite of date, portfolio, and symbol fields.
    
    This function processes records from the `start` index up to `count`, inserting each record into a primary key hash table (`pkey`) using a combined hash of its date, portfolio, and symbol values. Collisions in the primary key table are resolved using quadratic probing. Additionally, it maintains and updates linked lists for efficient lookups by date, portfolio, and symbol:
    
    - `datelastidx` and `dateprevidx` track the most recent and previous record indices per date.
    - `portlastidx` and `portprevidx` track the most recent and previous record indices per portfolio, resolving collisions with quadratic probing.
    - `symbollastidx` and `symbolprevidx` track the most recent and previous record indices per symbol, also resolving collisions with quadratic probing.
    
    Parameters:
    - records (structured array): Array of records with fields 'date', 'portfolio', and 'symbol'.
    - count (int): Total number of records to process.
    - pkey (np.ndarray): Primary key hash table initialized with -1 for empty slots.
    - datelastidx (np.ndarray): Array tracking the last record index
    """
    n = np.uint32(pkey.size-1)
    for i in range(start, count):
        h0 = np.uint64(records['date'][i])
        h1 = djb2_hash(records['portfolio'][i])
        h2 = djb2_hash(records['symbol'][i])
        h = np.uint32((h0 ^ h1 ^ h2) % n)
        if pkey[h] == -1:
            pkey[h] = i
        else:
            duplicatedkey = True
            j = 1
            while (
                    (records[pkey[h]]['date'] != records[i]['date']) |
                    (records[pkey[h]]['portfolio'] != records[i]['portfolio']) |
                    (records[pkey[h]]['symbol'] != records[i]['symbol'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    pkey[h] = i
                    duplicatedkey = False
                    break
                j += 1
            if duplicatedkey:
                return False

        # update date index
        intdt = np.uint32( (np.uint64(records['date'][i]) - np.uint64(mindate)) // np.uint64(periodns) )
        if datelastidx[intdt] == -1:  # date not found
            datelastidx[intdt] = i
            dateprevidx[i] = -1
        else: # found            
            dateprevidx[i] = datelastidx[intdt]
            datelastidx[intdt] = i

        # update port index
        hs = np.uint32(h1 % n)
        if portlastidx[hs] == -1:  # port not found
            portlastidx[hs] = i
            portprevidx[i] = -1
        else:
            # check for collision
            found = True
            j = 1
            while (records[i]['portfolio'] != records[portlastidx[hs]]['portfolio']):
                hs = np.uint32((hs + j**2) % n)
                if portlastidx[hs] == -1:
                    portlastidx[hs] = i
                    portprevidx[i] = -1
                    found = False
                    break
                j += 1

            if found:
                portprevidx[i] = portlastidx[hs]
                portlastidx[hs] = i

        # update symbol index
        hs = np.uint32(h2 % n)
        if symbollastidx[hs] == -1:  # symbol not found
            symbollastidx[hs] = i
            symbolprevidx[i] = -1
        else:
            # check for collision
            found = True
            j = 1
            while (records[i]['symbol'] != records[symbollastidx[hs]]['symbol']):
                hs = np.uint32((hs + j**2) % n)
                if symbollastidx[hs] == -1:
                    symbollastidx[hs] = i
                    symbolprevidx[i] = -1
                    found = False
                    break
                j += 1

            if found:
                symbolprevidx[i] = symbollastidx[hs]
                symbollastidx[hs] = i

    return True

@njit(cache=CACHE_JITTED)
def get_loc_date_portfolio_symbol_jit(records, pkey, keys):
    """
    Locate indices of given keys in a records array using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array with fields 'date', 'portfolio', and 'symbol'.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in `records`.
        keys (np.ndarray): Structured array of keys with fields 'date', 'portfolio', and 'symbol' to find in `records`.
    
    Returns:
        np.ndarray: Array of indices in `records` corresponding to each key in `keys`. Returns -1 for keys not found.
    
    Notes:
        - Combines the 'date' field and hashed 'portfolio' and 'symbol' strings to compute the hash.
        - Uses quadratic probing to resolve collisions in the hash table.
        - Decorated with @njit for Just-In-Time compilation to enhance performance.
    """
    n = np.uint32(pkey.size-1)
    loc = np.empty((keys.size, ))
    for i in range(keys.size):
        h0 = np.uint64(keys['date'][i])
        h1 = djb2_hash(keys['portfolio'][i])
        h2 = djb2_hash(keys['symbol'][i])
        h = np.uint32((h0 ^ h1 ^ h2) % n)
        if pkey[h] == -1:
            loc[i] = pkey[h]
        else:
            j = 1
            while (
                    (records[pkey[h]]['date'] != keys[i]['date']) |
                    (records[pkey[h]]['portfolio'] != keys[i]['portfolio']) |
                    (records[pkey[h]]['symbol'] != keys[i]['symbol'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1
            loc[i] = pkey[h]
    return loc

@njit(cache=CACHE_JITTED)
def upsert_date_portfolio_symbol_jit(records, count, new_records, pkey, 
                                     datelastidx, dateprevidx, mindate, periodns,
                                     portlastidx, portprevidx, symbollastidx, symbolprevidx):

    """
    '''
    Insert or update records in a structured array using composite keys (date, portfolio, symbol) with a custom hash table and quadratic probing for collision resolution.
    
    Parameters:
    - records (np.ndarray): Structured array of existing records with fields 'date', 'portfolio', and 'symbol'.
    - count (int): Current number of valid records in `records`.
    - new_records (np.ndarray): Structured array of new records to insert or update.
    - pkey (np.ndarray): Hash table mapping composite keys to indices in `records`.
    - datelastidx (np.ndarray): Array tracking the last inserted record index for each date bucket.
    - dateprevidx (np.ndarray): Array linking records with the same date in a linked-list manner.
    - mindate (int): Minimum date value used for date indexing.
    - periodns (int): Time period in nanoseconds used to bucket dates.
    - portlastidx (np.ndarray): Hash table tracking last inserted record index for each portfolio bucket.
    - portprevidx (np.ndarray): Array linking records with the same portfolio in a linked-list manner.
    - symbollastidx (np.ndarray): Hash table tracking last inserted record index for each symbol bucket.
    - symbolprevidx (np.ndarray): Array linking records with the same
    """
    minchgid = count
    maxsize = records.size
    nrec = new_records.size
    n = np.uint32(pkey.size-1)
    # track last date to check if idx is sorted
    isidxsorted = True
    if count>0:
        lastdate = np.int64(records[count-1]['date'])
    else:
        lastdate = 0
    for i in range(nrec):
        h0 = np.uint64(new_records['date'][i])
        h1 = djb2_hash(new_records['portfolio'][i])
        h2 = djb2_hash(new_records['symbol'][i])
        h = np.uint32((h0 ^ h1 ^ h2) % n)
        found = False

        if pkey[h] != -1:  # hash already exists
            j = 1
            while True:  # check for collision & find a free bucket
                if (records[pkey[h]]['date'] == new_records[i]['date'] and
                   records[pkey[h]]['portfolio'] == new_records[i]['portfolio'] and
                   records[pkey[h]]['symbol'] == new_records[i]['symbol']):
                    # record exists, update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    found = True
                    break
                # collision confirmed, jump hash
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1

        if not found:
            # Check space and append new record
            if count >= maxsize:
                break  # max size reached
            else:
                # append new record
                records[count] = new_records[i]                
                pkey[h] = count

                # update date index
                _lastdate = np.int64(new_records['date'][i])
                if _lastdate<lastdate:
                    isidxsorted = False
                else:
                    lastdate = _lastdate
                intdt = np.uint32( (np.uint64(new_records['date'][i]) - np.uint64(mindate)) // np.uint64(periodns) )                
                if datelastidx[intdt] == -1:  # date not found
                    datelastidx[intdt] = count
                    dateprevidx[count] = -1
                else: # found            
                    dateprevidx[count] = datelastidx[intdt]
                    datelastidx[intdt] = count

                # update portfolio index
                hs = np.uint32(h1 % n)
                if portlastidx[hs] == -1:  # portfolio not found
                    portlastidx[hs] = count
                    portprevidx[count] = -1
                else:
                    # check for collision and find the appropriate bucket
                    found_portfolio = True
                    j = 1
                    while records[portlastidx[hs]]['portfolio'] != new_records[i]['portfolio']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if portlastidx[hs] == -1:
                            portlastidx[hs] = count
                            portprevidx[count] = -1
                            found_portfolio = False
                            break
                        j += 1

                    if found_portfolio:
                        portprevidx[count] = portlastidx[hs]
                        portlastidx[hs] = count

                # update symbol index
                hs = np.uint32(h2 % n)
                if symbollastidx[hs] == -1:  # symbol not found
                    symbollastidx[hs] = count
                    symbolprevidx[count] = -1
                else:
                    # check for collision and find the appropriate bucket
                    found_symbol = True
                    j = 1
                    while records[symbollastidx[hs]]['symbol'] != new_records[i]['symbol']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if symbollastidx[hs] == -1:
                            symbollastidx[hs] = count
                            symbolprevidx[count] = -1
                            found_symbol = False
                            break
                        j += 1

                    if found_symbol:
                        symbolprevidx[count] = symbollastidx[hs]
                        symbollastidx[hs] = count

                minchgid = min(minchgid, count)
                count += 1

    return count, minchgid, isidxsorted


###################### DATE_PORTFOLIO_SYMBOL_TRADEID ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_portfolio_symbol_tradeid_jit(records, count, pkey, 
                                                  datelastidx, dateprevidx, mindate, periodns, 
                                                  portlastidx, portprevidx, symbollastidx, symbolprevidx, start):
    """
    '''
    Creates and updates hash-based indices for a batch of records keyed by a composite of date, portfolio, symbol, and trade ID.
    
    Processes records starting from the given start index up to count, inserting each record into a primary key hash table (`pkey`) using a combined hash of its date, portfolio, symbol, and trade ID fields. Collisions in the primary key hash table are resolved using quadratic probing. If a duplicate composite key is detected, the function returns False immediately.
    
    Additionally, the function maintains linked-list style indices for efficient lookup by date, portfolio, and symbol:
    - `datelastidx` and `dateprevidx` track the latest and previous record indices for each date bucket.
    - `portlastidx` and `portprevidx` track the latest and previous record indices for each portfolio bucket.
    - `symbollastidx` and `symbolprevidx` track the latest and previous record indices for each symbol bucket.
    
    Parameters:
    - records (structured array): Array of records with fields 'date', 'portfolio', 'symbol', and 'tradeid'.
    - count (int): Total number of records to process.
    - pkey (np.ndarray): Primary key hash table initialized with -1 for empty slots.
    - datelast
    """
    n = np.uint32(pkey.size-1)
    for i in range(start, count):        
        h0 = np.uint64(records['date'][i])
        h1 = djb2_hash(records['portfolio'][i])
        h2 = djb2_hash(records['symbol'][i])
        h3 = djb2_hash(records['tradeid'][i])
        h = np.uint32((h0 ^ h1 ^ h2 ^ h3) % n)
        if pkey[h] == -1:
            pkey[h] = i
        else:
            duplicatedkey = True
            j = 1
            while (
                    (records[pkey[h]]['date'] != records[i]['date']) |
                    (records[pkey[h]]['portfolio'] != records[i]['portfolio']) |
                    (records[pkey[h]]['symbol'] != records[i]['symbol']) |
                    (records[pkey[h]]['tradeid'] != records[i]['tradeid'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    pkey[h] = i
                    duplicatedkey = False
                    break
                j += 1
            if duplicatedkey:
                return False

        # update date index
        intdt = np.uint32( (np.uint64(records['date'][i]) - np.uint64(mindate)) // np.uint64(periodns) )
        if datelastidx[intdt] == -1:  # date not found
            datelastidx[intdt] = i
            dateprevidx[i] = -1
        else: # found            
            dateprevidx[i] = datelastidx[intdt]
            datelastidx[intdt] = i
            
        # update port index
        hs = np.uint32(h1 % n)
        if portlastidx[hs] == -1:  # port not found
            portlastidx[hs] = i
            portprevidx[i] = -1
        else:
            # check for collision
            found = True
            j = 1
            while (records[i]['portfolio'] != records[portlastidx[hs]]['portfolio']):
                hs = np.uint32((hs + j**2) % n)
                if portlastidx[hs] == -1:
                    portlastidx[hs] = i
                    portprevidx[i] = -1
                    found = False
                    break
                j += 1

            if found:
                portprevidx[i] = portlastidx[hs]
                portlastidx[hs] = i

        # update symbol index
        hs = np.uint32(h2 % n)
        if symbollastidx[hs] == -1:  # symbol not found
            symbollastidx[hs] = i
            symbolprevidx[i] = -1
        else:
            # check for collision
            found = True
            j = 1
            while (records[i]['symbol'] != records[symbollastidx[hs]]['symbol']):
                hs = np.uint32((hs + j**2) % n)
                if symbollastidx[hs] == -1:
                    symbollastidx[hs] = i
                    symbolprevidx[i] = -1
                    found = False
                    break
                j += 1

            if found:
                symbolprevidx[i] = symbollastidx[hs]
                symbollastidx[hs] = i

    return True

@njit(cache=CACHE_JITTED)
def get_loc_date_portfolio_symbol_tradeid_jit(records, pkey, keys):
    """
    Compute the indices of specified keys within a records array using a hash table with quadratic probing.
    
    This function searches for each key in the `keys` array within the `records` array by hashing a combination
    of the 'date', 'portfolio', 'symbol', and 'tradeid' fields. It uses a provided hash table `pkey` to map
    hashed keys to record indices. Collisions in the hash table are resolved using quadratic probing.
    
    Parameters
    ----------
    records : numpy structured array
        Array of records containing fields 'date', 'portfolio', 'symbol', and 'tradeid'.
    pkey : numpy.ndarray
        Hash table array mapping hashed keys to indices in `records`. A value of -1 indicates an empty slot.
    keys : numpy structured array
        Array of keys to locate in `records`, each with fields 'date', 'portfolio', 'symbol', and 'tradeid'.
    
    Returns
    -------
    numpy.ndarray
        Array of indices indicating the position of each key in `records`. If a key is not found, the index is -1.
    """
    n = np.uint32(pkey.size-1)
    loc = np.empty((keys.size, ))
    for i in range(keys.size):
        h0 = np.uint64(keys['date'][i])
        h1 = djb2_hash(keys['portfolio'][i])
        h2 = djb2_hash(keys['symbol'][i])
        h3 = djb2_hash(keys['tradeid'][i])
        h = np.uint32((h0 ^ h1 ^ h2 ^ h3) % n)
        if pkey[h] == -1:
            loc[i] = pkey[h]
        else:
            j = 1
            while (
                    (records[pkey[h]]['date'] != keys[i]['date']) |
                    (records[pkey[h]]['portfolio'] != keys[i]['portfolio']) |
                    (records[pkey[h]]['symbol'] != keys[i]['symbol']) |
                    (records[pkey[h]]['tradeid'] != keys[i]['tradeid'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1
            loc[i] = pkey[h]
    return loc

@njit(cache=CACHE_JITTED)
def upsert_date_portfolio_symbol_tradeid_jit(records, count, new_records, pkey, 
                                             datelastidx, dateprevidx, mindate, periodns,
                                             portlastidx, portprevidx, symbollastidx, symbolprevidx):

    """
    '''
    Upserts new trade records into an existing structured array of records using a custom hash-based indexing scheme with quadratic probing for collision resolution.
    
    Parameters:
    - records (np.ndarray): Existing array of trade records to be updated or appended.
    - count (int): Current number of valid records in `records`.
    - new_records (np.ndarray): Array of new trade records to be inserted or used to update existing records.
    - pkey (np.ndarray): Primary key hash table mapping hashed keys to record indices in `records`.
    - datelastidx (np.ndarray): Array indexing the last record for each date bucket.
    - dateprevidx (np.ndarray): Array storing the previous record index for each record in the date index chain.
    - mindate (int): Minimum date value used for date bucket calculation.
    - periodns (int): Period length in nanoseconds used to calculate date buckets.
    - portlastidx (np.ndarray): Array indexing the last record for each portfolio bucket.
    - portprevidx (np.ndarray): Array storing the previous record index for each record in the portfolio index chain.
    - symbollastidx (np.ndarray): Array indexing the last record for each symbol bucket.
    - symbolprevidx (np.ndarray): Array storing the previous record index for each
    """
    minchgid = count
    maxsize = records.size
    nrec = new_records.size
    n = np.uint32(pkey.size-1)
    # track last date to check if idx is sorted
    isidxsorted = True
    if count>0:
        lastdate = np.int64(records[count-1]['date'])
    else:
        lastdate = 0
    for i in range(nrec):
        h0 = np.uint64(new_records['date'][i])
        h1 = djb2_hash(new_records['portfolio'][i])
        h2 = djb2_hash(new_records['symbol'][i])
        h3 = djb2_hash(new_records['tradeid'][i])
        h = np.uint32((h0 ^ h1 ^ h2 ^ h3) % n)
        found = False

        if pkey[h] != -1:  # hash already exists
            j = 1
            while True:  # check for collision & find a free bucket
                if (records[pkey[h]]['date'] == new_records[i]['date'] and
                   records[pkey[h]]['portfolio'] == new_records[i]['portfolio'] and
                   records[pkey[h]]['symbol'] == new_records[i]['symbol'] and
                   records[pkey[h]]['tradeid'] == new_records[i]['tradeid']):
                    # record exists, update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    found = True
                    break
                # collision confirmed, jump hash using quadratic probing
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1

        if not found:
            # Check space and append new record
            if count >= maxsize:
                break  # max size reached
            else:
                # append new record
                records[count] = new_records[i]                
                pkey[h] = count

                # update date index
                _lastdate = np.int64(new_records['date'][i])
                if _lastdate<lastdate:
                    isidxsorted = False
                else:
                    lastdate = _lastdate
                intdt = np.uint32( (np.uint64(new_records['date'][i]) - np.uint64(mindate)) // np.uint64(periodns) )                
                if datelastidx[intdt] == -1:  # date not found
                    datelastidx[intdt] = count
                    dateprevidx[count] = -1
                else: # found            
                    dateprevidx[count] = datelastidx[intdt]
                    datelastidx[intdt] = count

                # update portfolio index
                hs = np.uint32(h1 % n)
                if portlastidx[hs] == -1:  # portfolio not found
                    portlastidx[hs] = count
                    portprevidx[count] = -1
                else:
                    # check for collision and find the appropriate bucket
                    found_portfolio = True
                    j = 1
                    while records[portlastidx[hs]]['portfolio'] != new_records[i]['portfolio']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if portlastidx[hs] == -1:
                            portlastidx[hs] = count
                            portprevidx[count] = -1
                            found_portfolio = False
                            break
                        j += 1

                    if found_portfolio:
                        portprevidx[count] = portlastidx[hs]
                        portlastidx[hs] = count

                # update symbol index
                hs = np.uint32(h2 % n)
                if symbollastidx[hs] == -1:  # symbol not found
                    symbollastidx[hs] = count
                    symbolprevidx[count] = -1
                else:
                    # check for collision and find the appropriate bucket
                    found_symbol = True
                    j = 1
                    while records[symbollastidx[hs]]['symbol'] != new_records[i]['symbol']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if symbollastidx[hs] == -1:
                            symbollastidx[hs] = count
                            symbolprevidx[count] = -1
                            found_symbol = False
                            break
                        j += 1

                    if found_symbol:
                        symbolprevidx[count] = symbollastidx[hs]
                        symbollastidx[hs] = count

                minchgid = min(minchgid, count)
                count += 1

    return count, minchgid, isidxsorted


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
