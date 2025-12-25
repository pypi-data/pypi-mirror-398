from numba.typed import List
import numpy as np
from numba import njit

from SharedData.TableIndexJitHash import djb2_hash, hash_int64, hash_float64, CACHE_JITTED

###################### DATE ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_jit(records, count, pkey, datelastidx, dateprevidx, mindate, periodns, start):
    """
    Creates and updates primary key and indexing arrays for records based on date fields.
    
    Uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    Also maintains linked lists for efficient indexing by various fields.
    
    Parameters:
    - records (structured array): Array of records containing 'date' fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
    """
    n = np.uint32(pkey.size-1)
    for i in range(start, count):        
        h0 = np.uint64(records['date'][i])
        h = np.uint32((h0) % n)
        if pkey[h] == -1:
            pkey[h] = i
        else:
            duplicatedkey = True
            j = 1
            while (
                    (records[pkey[h]]['date'] != records[i]['date'])
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

    return True

@njit(cache=CACHE_JITTED)
def get_loc_date_jit(records, pkey, keys):
    """
    Finds the indices of records matching given date keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'date' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with 'date' fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
    """
    n = np.uint32(pkey.size-1)
    loc = np.empty((keys.size, ))
    for i in range(keys.size):
        h0 = np.uint64(keys['date'][i])
        h = np.uint32((h0) % n)
        if pkey[h] == -1:
            loc[i] = pkey[h]
        else:
            j = 1
            while (
                    (records[pkey[h]]['date'] != keys[i]['date'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1
            loc[i] = pkey[h]
    
    return loc

@njit(cache=CACHE_JITTED)
def upsert_date_jit(records, count, new_records, pkey, 
                                datelastidx, dateprevidx, mindate, periodns,
                                portlastidx, portprevidx, symbollastidx, symbolprevidx):
    """
    Insert or update records in a hash table using quadratic probing for collision resolution.
    
    Maintains auxiliary indices for efficient lookups by date, symbol, and/or portfolio fields.
    
    Parameters:
    - records (np.ndarray): Array of existing records to be updated or appended.
    - count (int): Current number of records in the records array.
    - new_records (np.ndarray): Array of new records to be inserted or used to update existing records.
    - pkey (np.ndarray): Hash table array mapping hash indices to record indices in records.
    
    Returns:
    - count (int): Updated count of records after insertion/updating.
    - minchgid (int): The smallest index of the record that was changed or inserted.
    - isidxsorted (bool): Whether the date index remains sorted (True if no date index).
    - positions (np.ndarray): Array of positions where each new record was inserted/updated.
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
    
    # Create array to track positions of new records
    positions = np.full(nrec, -1, dtype=np.int64)

    for i in range(nrec):        
        h0 = np.uint64(new_records['date'][i])
        h = np.uint32((h0) % n)
        found = False

        if pkey[h] != -1:  # hash already exists
            j = 1
            while True:  # check for collision & find a free bucket
                if (records[pkey[h]]['date'] == new_records[i]['date']):
                    # record exists update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    positions[i] = pkey[h]  # Add position of updated record
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
                positions[i] = count  # Add position of new record

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

                minchgid = min(minchgid, count)
                count += 1

    return count, minchgid, isidxsorted, positions


###################### SYMBOL ########################
@njit(cache=CACHE_JITTED)
def create_pkey_symbol_jit(records, count, pkey, start):
    """
    Creates and updates primary key and indexing arrays for records based on symbol fields.
    
    Uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    Also maintains linked lists for efficient indexing by various fields.
    
    Parameters:
    - records (structured array): Array of records containing 'symbol' fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
    """
    n = np.uint32(pkey.size-1)
    for i in range(start, count):        
        h0 = djb2_hash(records['symbol'][i])
        h = np.uint32((h0) % n)
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
    Finds the indices of records matching given symbol keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'symbol' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with 'symbol' fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
    """
    n = np.uint32(pkey.size-1)
    loc = np.empty((keys.size, ))
    for i in range(keys.size):
        h0 = djb2_hash(keys['symbol'][i])
        h = np.uint32((h0) % n)
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
    
    Maintains auxiliary indices for efficient lookups by date, symbol, and/or portfolio fields.
    
    Parameters:
    - records (np.ndarray): Array of existing records to be updated or appended.
    - count (int): Current number of records in the records array.
    - new_records (np.ndarray): Array of new records to be inserted or used to update existing records.
    - pkey (np.ndarray): Hash table array mapping hash indices to record indices in records.
    
    Returns:
    - count (int): Updated count of records after insertion/updating.
    - minchgid (int): The smallest index of the record that was changed or inserted.
    - isidxsorted (bool): Whether the date index remains sorted (True if no date index).
    - positions (np.ndarray): Array of positions where each new record was inserted/updated.
    """
    minchgid = count
    maxsize = records.size
    nrec = new_records.size
    n = np.uint32(pkey.size-1)

    # Create array to track positions of new records
    positions = np.full(nrec, -1, dtype=np.int64)

    for i in range(nrec):        
        h0 = djb2_hash(new_records['symbol'][i])
        h = np.uint32((h0) % n)
        found = False

        if pkey[h] != -1:  # hash already exists
            j = 1
            while True:  # check for collision & find a free bucket
                if (records[pkey[h]]['symbol'] == new_records[i]['symbol']):
                    # record exists update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    positions[i] = pkey[h]  # Add position of updated record
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
                positions[i] = count  # Add position of new record


                minchgid = min(minchgid, count)
                count += 1

    return count, minchgid, True, positions


###################### HASH ########################
@njit(cache=CACHE_JITTED)
def create_pkey_hash_jit(records, count, pkey, start):
    """
    Creates and updates primary key and indexing arrays for records based on hash fields.
    
    Uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    Also maintains linked lists for efficient indexing by various fields.
    
    Parameters:
    - records (structured array): Array of records containing 'hash' fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
    """
    n = np.uint32(pkey.size-1)
    for i in range(start, count):        
        h0 = djb2_hash(records['hash'][i])
        h = np.uint32((h0) % n)
        if pkey[h] == -1:
            pkey[h] = i
        else:
            duplicatedkey = True
            j = 1
            while (
                    (records[pkey[h]]['hash'] != records[i]['hash'])
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
def get_loc_hash_jit(records, pkey, keys):
    """
    Finds the indices of records matching given hash keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'hash' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with 'hash' fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
    """
    n = np.uint32(pkey.size-1)
    loc = np.empty((keys.size, ))
    for i in range(keys.size):
        h0 = djb2_hash(keys['hash'][i])
        h = np.uint32((h0) % n)
        if pkey[h] == -1:
            loc[i] = pkey[h]
        else:
            j = 1
            while (
                    (records[pkey[h]]['hash'] != keys[i]['hash'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1
            loc[i] = pkey[h]
    
    return loc

@njit(cache=CACHE_JITTED)
def upsert_hash_jit(records, count, new_records, pkey, 
                                datelastidx, dateprevidx, mindate, periodns,
                                portlastidx, portprevidx, symbollastidx, symbolprevidx):
    """
    Insert or update records in a hash table using quadratic probing for collision resolution.
    
    Maintains auxiliary indices for efficient lookups by date, symbol, and/or portfolio fields.
    
    Parameters:
    - records (np.ndarray): Array of existing records to be updated or appended.
    - count (int): Current number of records in the records array.
    - new_records (np.ndarray): Array of new records to be inserted or used to update existing records.
    - pkey (np.ndarray): Hash table array mapping hash indices to record indices in records.
    
    Returns:
    - count (int): Updated count of records after insertion/updating.
    - minchgid (int): The smallest index of the record that was changed or inserted.
    - isidxsorted (bool): Whether the date index remains sorted (True if no date index).
    - positions (np.ndarray): Array of positions where each new record was inserted/updated.
    """
    minchgid = count
    maxsize = records.size
    nrec = new_records.size
    n = np.uint32(pkey.size-1)

    # Create array to track positions of new records
    positions = np.full(nrec, -1, dtype=np.int64)

    for i in range(nrec):        
        h0 = djb2_hash(new_records['hash'][i])
        h = np.uint32((h0) % n)
        found = False

        if pkey[h] != -1:  # hash already exists
            j = 1
            while True:  # check for collision & find a free bucket
                if (records[pkey[h]]['hash'] == new_records[i]['hash']):
                    # record exists update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    positions[i] = pkey[h]  # Add position of updated record
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
                positions[i] = count  # Add position of new record


                minchgid = min(minchgid, count)
                count += 1

    return count, minchgid, True, positions


###################### PORTFOLIO ########################
@njit(cache=CACHE_JITTED)
def create_pkey_portfolio_jit(records, count, pkey, portlastidx, portprevidx, start):
    """
    Creates and updates primary key and indexing arrays for records based on portfolio fields.
    
    Uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    Also maintains linked lists for efficient indexing by various fields.
    
    Parameters:
    - records (structured array): Array of records containing 'portfolio' fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
    """
    n = np.uint32(pkey.size-1)
    for i in range(start, count):        
        h0 = djb2_hash(records['portfolio'][i])
        h = np.uint32((h0) % n)
        if pkey[h] == -1:
            pkey[h] = i
        else:
            duplicatedkey = True
            j = 1
            while (
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

        # update portfolio index
        hs = np.uint32(h0 % n)
        if portlastidx[hs] == -1:  # portfolio not found
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
def get_loc_portfolio_jit(records, pkey, keys):
    """
    Finds the indices of records matching given portfolio keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'portfolio' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with 'portfolio' fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
    """
    n = np.uint32(pkey.size-1)
    loc = np.empty((keys.size, ))
    for i in range(keys.size):
        h0 = djb2_hash(keys['portfolio'][i])
        h = np.uint32((h0) % n)
        if pkey[h] == -1:
            loc[i] = pkey[h]
        else:
            j = 1
            while (
                    (records[pkey[h]]['portfolio'] != keys[i]['portfolio'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1
            loc[i] = pkey[h]
    
    return loc

@njit(cache=CACHE_JITTED)
def upsert_portfolio_jit(records, count, new_records, pkey, 
                                datelastidx, dateprevidx, mindate, periodns,
                                portlastidx, portprevidx, symbollastidx, symbolprevidx):
    """
    Insert or update records in a hash table using quadratic probing for collision resolution.
    
    Maintains auxiliary indices for efficient lookups by date, symbol, and/or portfolio fields.
    
    Parameters:
    - records (np.ndarray): Array of existing records to be updated or appended.
    - count (int): Current number of records in the records array.
    - new_records (np.ndarray): Array of new records to be inserted or used to update existing records.
    - pkey (np.ndarray): Hash table array mapping hash indices to record indices in records.
    
    Returns:
    - count (int): Updated count of records after insertion/updating.
    - minchgid (int): The smallest index of the record that was changed or inserted.
    - isidxsorted (bool): Whether the date index remains sorted (True if no date index).
    - positions (np.ndarray): Array of positions where each new record was inserted/updated.
    """
    minchgid = count
    maxsize = records.size
    nrec = new_records.size
    n = np.uint32(pkey.size-1)

    # Create array to track positions of new records
    positions = np.full(nrec, -1, dtype=np.int64)

    for i in range(nrec):        
        h0 = djb2_hash(new_records['portfolio'][i])
        h = np.uint32((h0) % n)
        found = False

        if pkey[h] != -1:  # hash already exists
            j = 1
            while True:  # check for collision & find a free bucket
                if (records[pkey[h]]['portfolio'] == new_records[i]['portfolio']):
                    # record exists update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    positions[i] = pkey[h]  # Add position of updated record
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
                positions[i] = count  # Add position of new record

                # update portfolio index
                hs = np.uint32(h0 % n)
                if portlastidx[hs] == -1:  # portfolio not found
                    portlastidx[hs] = count
                    portprevidx[count] = -1
                else:
                    # check for collision and find the appropriate bucket
                    found_port = True
                    j = 1
                    while records[portlastidx[hs]]['portfolio'] != new_records[i]['portfolio']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if portlastidx[hs] == -1:
                            portlastidx[hs] = count
                            portprevidx[count] = -1
                            found_port = False
                            break
                        j += 1

                    if found_port:
                        portprevidx[count] = portlastidx[hs]
                        portlastidx[hs] = count

                minchgid = min(minchgid, count)
                count += 1

    return count, minchgid, True, positions


###################### DATE_SYMBOL ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_symbol_jit(records, count, pkey, datelastidx, dateprevidx, mindate, periodns, symbollastidx, symbolprevidx, start):
    """
    Creates and updates primary key and indexing arrays for records based on date, symbol fields.
    
    Uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    Also maintains linked lists for efficient indexing by various fields.
    
    Parameters:
    - records (structured array): Array of records containing 'date', 'symbol' fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
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
    Finds the indices of records matching given date, symbol keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'date', 'symbol' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with 'date', 'symbol' fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
    """
    n = np.uint32(pkey.size-1)
    loc = np.empty((keys.size, ), dtype=np.int64)
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
                h = np.uint32((h + j ** 2) % n)
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
    Insert or update records in a hash table using quadratic probing for collision resolution.
    
    Maintains auxiliary indices for efficient lookups by date, symbol, and/or portfolio fields.
    
    Parameters:
    - records (np.ndarray): Array of existing records to be updated or appended.
    - count (int): Current number of records in the records array.
    - new_records (np.ndarray): Array of new records to be inserted or used to update existing records.
    - pkey (np.ndarray): Hash table array mapping hash indices to record indices in records.
    
    Returns:
    - count (int): Updated count of records after insertion/updating.
    - minchgid (int): The smallest index of the record that was changed or inserted.
    - isidxsorted (bool): Whether the date index remains sorted (True if no date index).
    - positions (np.ndarray): Array of positions where each new record was inserted/updated.
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
    
    # Create array to track positions of new records
    positions = np.full(nrec, -1, dtype=np.int64)

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
                    positions[i] = pkey[h]  # Add position of updated record
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
                positions[i] = count  # Add position of new record

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

    return count, minchgid, isidxsorted, positions


###################### DATE_HASH ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_hash_jit(records, count, pkey, datelastidx, dateprevidx, mindate, periodns, start):
    """
    Creates and updates primary key and indexing arrays for records based on date, hash fields.
    
    Uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    Also maintains linked lists for efficient indexing by various fields.
    
    Parameters:
    - records (structured array): Array of records containing 'date', 'hash' fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
    """
    n = np.uint32(pkey.size-1)
    for i in range(start, count):        
        h0 = np.uint64(records['date'][i])
        h1 = djb2_hash(records['hash'][i])
        h = np.uint32((h0 ^ h1) % n)
        if pkey[h] == -1:
            pkey[h] = i
        else:
            duplicatedkey = True
            j = 1
            while (
                    (records[pkey[h]]['date'] != records[i]['date']) |
                    (records[pkey[h]]['hash'] != records[i]['hash'])
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

    return True

@njit(cache=CACHE_JITTED)
def get_loc_date_hash_jit(records, pkey, keys):
    """
    Finds the indices of records matching given date, hash keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'date', 'hash' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with 'date', 'hash' fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
    """
    n = np.uint32(pkey.size-1)
    loc = np.empty((keys.size, ))
    for i in range(keys.size):
        h0 = np.uint64(keys['date'][i])
        h1 = djb2_hash(keys['hash'][i])
        h = np.uint32((h0 ^ h1) % n)
        if pkey[h] == -1:
            loc[i] = pkey[h]
        else:
            j = 1
            while (
                    (records[pkey[h]]['date'] != keys[i]['date']) |
                    (records[pkey[h]]['hash'] != keys[i]['hash'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1
            loc[i] = pkey[h]
    
    return loc

@njit(cache=CACHE_JITTED)
def upsert_date_hash_jit(records, count, new_records, pkey, 
                                datelastidx, dateprevidx, mindate, periodns,
                                portlastidx, portprevidx, symbollastidx, symbolprevidx):
    """
    Insert or update records in a hash table using quadratic probing for collision resolution.
    
    Maintains auxiliary indices for efficient lookups by date, symbol, and/or portfolio fields.
    
    Parameters:
    - records (np.ndarray): Array of existing records to be updated or appended.
    - count (int): Current number of records in the records array.
    - new_records (np.ndarray): Array of new records to be inserted or used to update existing records.
    - pkey (np.ndarray): Hash table array mapping hash indices to record indices in records.
    
    Returns:
    - count (int): Updated count of records after insertion/updating.
    - minchgid (int): The smallest index of the record that was changed or inserted.
    - isidxsorted (bool): Whether the date index remains sorted (True if no date index).
    - positions (np.ndarray): Array of positions where each new record was inserted/updated.
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
    
    # Create array to track positions of new records
    positions = np.full(nrec, -1, dtype=np.int64)

    for i in range(nrec):        
        h0 = np.uint64(new_records['date'][i])
        h1 = djb2_hash(new_records['hash'][i])
        h = np.uint32((h0 ^ h1) % n)
        found = False

        if pkey[h] != -1:  # hash already exists
            j = 1
            while True:  # check for collision & find a free bucket
                if (records[pkey[h]]['date'] == new_records[i]['date'] and
                   records[pkey[h]]['hash'] == new_records[i]['hash']):
                    # record exists update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    positions[i] = pkey[h]  # Add position of updated record
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
                positions[i] = count  # Add position of new record

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

                minchgid = min(minchgid, count)
                count += 1

    return count, minchgid, isidxsorted, positions


###################### DATE_PORTFOLIO ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_portfolio_jit(records, count, pkey, datelastidx, dateprevidx, mindate, periodns, portlastidx, portprevidx, start):
    """
    Creates and updates primary key and indexing arrays for records based on date, portfolio fields.
    
    Uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    Also maintains linked lists for efficient indexing by various fields.
    
    Parameters:
    - records (structured array): Array of records containing 'date', 'portfolio' fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
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
        # update portfolio index
        hs = np.uint32(h1 % n)
        if portlastidx[hs] == -1:  # portfolio not found
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
    Finds the indices of records matching given date, portfolio keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'date', 'portfolio' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with 'date', 'portfolio' fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
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
    Insert or update records in a hash table using quadratic probing for collision resolution.
    
    Maintains auxiliary indices for efficient lookups by date, symbol, and/or portfolio fields.
    
    Parameters:
    - records (np.ndarray): Array of existing records to be updated or appended.
    - count (int): Current number of records in the records array.
    - new_records (np.ndarray): Array of new records to be inserted or used to update existing records.
    - pkey (np.ndarray): Hash table array mapping hash indices to record indices in records.
    
    Returns:
    - count (int): Updated count of records after insertion/updating.
    - minchgid (int): The smallest index of the record that was changed or inserted.
    - isidxsorted (bool): Whether the date index remains sorted (True if no date index).
    - positions (np.ndarray): Array of positions where each new record was inserted/updated.
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
    
    # Create array to track positions of new records
    positions = np.full(nrec, -1, dtype=np.int64)

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
                    positions[i] = pkey[h]  # Add position of updated record
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
                positions[i] = count  # Add position of new record

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
                    found_port = True
                    j = 1
                    while records[portlastidx[hs]]['portfolio'] != new_records[i]['portfolio']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if portlastidx[hs] == -1:
                            portlastidx[hs] = count
                            portprevidx[count] = -1
                            found_port = False
                            break
                        j += 1

                    if found_port:
                        portprevidx[count] = portlastidx[hs]
                        portlastidx[hs] = count

                minchgid = min(minchgid, count)
                count += 1

    return count, minchgid, isidxsorted, positions


###################### DATE_SYMBOL_SYMBOL1 ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_symbol_symbol1_jit(records, count, pkey, datelastidx, dateprevidx, mindate, periodns, symbollastidx, symbolprevidx, start):
    """
    Creates and updates primary key and indexing arrays for records based on date, symbol, symbol1 fields.
    
    Uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    Also maintains linked lists for efficient indexing by various fields.
    
    Parameters:
    - records (structured array): Array of records containing 'date', 'symbol', 'symbol1' fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
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
    Finds the indices of records matching given date, symbol, symbol1 keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'date', 'symbol', 'symbol1' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with 'date', 'symbol', 'symbol1' fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
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
    Insert or update records in a hash table using quadratic probing for collision resolution.
    
    Maintains auxiliary indices for efficient lookups by date, symbol, and/or portfolio fields.
    
    Parameters:
    - records (np.ndarray): Array of existing records to be updated or appended.
    - count (int): Current number of records in the records array.
    - new_records (np.ndarray): Array of new records to be inserted or used to update existing records.
    - pkey (np.ndarray): Hash table array mapping hash indices to record indices in records.
    
    Returns:
    - count (int): Updated count of records after insertion/updating.
    - minchgid (int): The smallest index of the record that was changed or inserted.
    - isidxsorted (bool): Whether the date index remains sorted (True if no date index).
    - positions (np.ndarray): Array of positions where each new record was inserted/updated.
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
    
    # Create array to track positions of new records
    positions = np.full(nrec, -1, dtype=np.int64)

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
                    positions[i] = pkey[h]  # Add position of updated record
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
                positions[i] = count  # Add position of new record

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

    return count, minchgid, isidxsorted, positions


###################### DATE_TAG_SYMBOL ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_tag_symbol_jit(records, count, pkey, datelastidx, dateprevidx, mindate, periodns, portlastidx, portprevidx, symbollastidx, symbolprevidx, start):
    """
    Creates and updates primary key and indexing arrays for records based on date, tag, symbol fields.
    
    Uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    Also maintains linked lists for efficient indexing by various fields.
    
    Parameters:
    - records (structured array): Array of records containing 'date', 'tag', 'symbol' fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
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
        if portlastidx[hs] == -1:  # tag not found
            portlastidx[hs] = i
            portprevidx[i] = -1
        else:
            # check for collision
            found = True
            j = 1
            while (records[i]['tag'] != records[portlastidx[hs]]['tag']):
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
def get_loc_date_tag_symbol_jit(records, pkey, keys):
    """
    Finds the indices of records matching given date, tag, symbol keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'date', 'tag', 'symbol' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with 'date', 'tag', 'symbol' fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
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
                            portlastidx, portprevidx, symbollastidx, symbolprevidx):
    """
    Insert or update records in a hash table using quadratic probing for collision resolution.
    
    Maintains auxiliary indices for efficient lookups by date, symbol, and/or portfolio fields.
    
    Parameters:
    - records (np.ndarray): Array of existing records to be updated or appended.
    - count (int): Current number of records in the records array.
    - new_records (np.ndarray): Array of new records to be inserted or used to update existing records.
    - pkey (np.ndarray): Hash table array mapping hash indices to record indices in records.
    
    Returns:
    - count (int): Updated count of records after insertion/updating.
    - minchgid (int): The smallest index of the record that was changed or inserted.
    - isidxsorted (bool): Whether the date index remains sorted (True if no date index).
    - positions (np.ndarray): Array of positions where each new record was inserted/updated.
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
    
    # Create array to track positions of new records
    positions = np.full(nrec, -1, dtype=np.int64)

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
                    # record exists update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    positions[i] = pkey[h]  # Add position of updated record
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
                positions[i] = count  # Add position of new record

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
                if portlastidx[hs] == -1:  # tag not found
                    portlastidx[hs] = count
                    portprevidx[count] = -1
                else:
                    # check for collision and find the appropriate bucket
                    found_tag = True
                    j = 1
                    while records[portlastidx[hs]]['tag'] != new_records[i]['tag']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if portlastidx[hs] == -1:
                            portlastidx[hs] = count
                            portprevidx[count] = -1
                            found_tag = False
                            break
                        j += 1

                    if found_tag:
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

    return count, minchgid, isidxsorted, positions


###################### DATE_PORTFOLIO_SYMBOL ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_portfolio_symbol_jit(records, count, pkey, datelastidx, dateprevidx, mindate, periodns, portlastidx, portprevidx, symbollastidx, symbolprevidx, start):
    """
    Creates and updates primary key and indexing arrays for records based on date, portfolio, symbol fields.
    
    Uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    Also maintains linked lists for efficient indexing by various fields.
    
    Parameters:
    - records (structured array): Array of records containing 'date', 'portfolio', 'symbol' fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
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
        # update portfolio index
        hs = np.uint32(h1 % n)
        if portlastidx[hs] == -1:  # portfolio not found
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
    Finds the indices of records matching given date, portfolio, symbol keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'date', 'portfolio', 'symbol' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with 'date', 'portfolio', 'symbol' fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
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
    Insert or update records in a hash table using quadratic probing for collision resolution.
    
    Maintains auxiliary indices for efficient lookups by date, symbol, and/or portfolio fields.
    
    Parameters:
    - records (np.ndarray): Array of existing records to be updated or appended.
    - count (int): Current number of records in the records array.
    - new_records (np.ndarray): Array of new records to be inserted or used to update existing records.
    - pkey (np.ndarray): Hash table array mapping hash indices to record indices in records.
    
    Returns:
    - count (int): Updated count of records after insertion/updating.
    - minchgid (int): The smallest index of the record that was changed or inserted.
    - isidxsorted (bool): Whether the date index remains sorted (True if no date index).
    - positions (np.ndarray): Array of positions where each new record was inserted/updated.
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
    
    # Create array to track positions of new records
    positions = np.full(nrec, -1, dtype=np.int64)

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
                    # record exists update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    positions[i] = pkey[h]  # Add position of updated record
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
                positions[i] = count  # Add position of new record

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
                    found_port = True
                    j = 1
                    while records[portlastidx[hs]]['portfolio'] != new_records[i]['portfolio']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if portlastidx[hs] == -1:
                            portlastidx[hs] = count
                            portprevidx[count] = -1
                            found_port = False
                            break
                        j += 1

                    if found_port:
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

    return count, minchgid, isidxsorted, positions


###################### DATE_PORTFOLIO_SYMBOL ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_portfolio_symbol_jit(records, count, pkey, datelastidx, dateprevidx, mindate, periodns, portlastidx, portprevidx, symbollastidx, symbolprevidx, start):
    """
    Creates and updates primary key and indexing arrays for records based on date, portfolio, symbol fields.
    
    Uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    Also maintains linked lists for efficient indexing by various fields.
    
    Parameters:
    - records (structured array): Array of records containing 'date', 'portfolio', 'symbol' fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
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
        # update portfolio index
        hs = np.uint32(h1 % n)
        if portlastidx[hs] == -1:  # portfolio not found
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
    Finds the indices of records matching given date, portfolio, symbol keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'date', 'portfolio', 'symbol' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with 'date', 'portfolio', 'symbol' fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
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
    Insert or update records in a hash table using quadratic probing for collision resolution.
    
    Maintains auxiliary indices for efficient lookups by date, symbol, and/or portfolio fields.
    
    Parameters:
    - records (np.ndarray): Array of existing records to be updated or appended.
    - count (int): Current number of records in the records array.
    - new_records (np.ndarray): Array of new records to be inserted or used to update existing records.
    - pkey (np.ndarray): Hash table array mapping hash indices to record indices in records.
    
    Returns:
    - count (int): Updated count of records after insertion/updating.
    - minchgid (int): The smallest index of the record that was changed or inserted.
    - isidxsorted (bool): Whether the date index remains sorted (True if no date index).
    - positions (np.ndarray): Array of positions where each new record was inserted/updated.
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
    
    # Create array to track positions of new records
    positions = np.full(nrec, -1, dtype=np.int64)

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
                    # record exists update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    positions[i] = pkey[h]  # Add position of updated record
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
                positions[i] = count  # Add position of new record

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
                    found_port = True
                    j = 1
                    while records[portlastidx[hs]]['portfolio'] != new_records[i]['portfolio']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if portlastidx[hs] == -1:
                            portlastidx[hs] = count
                            portprevidx[count] = -1
                            found_port = False
                            break
                        j += 1

                    if found_port:
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

    return count, minchgid, isidxsorted, positions


###################### DATE_PORTFOLIO_SYMBOL ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_portfolio_symbol_jit(records, count, pkey, datelastidx, dateprevidx, mindate, periodns, portlastidx, portprevidx, symbollastidx, symbolprevidx, start):
    """
    Creates and updates primary key and indexing arrays for records based on date, portfolio, symbol fields.
    
    Uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    Also maintains linked lists for efficient indexing by various fields.
    
    Parameters:
    - records (structured array): Array of records containing 'date', 'portfolio', 'symbol' fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
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
        # update portfolio index
        hs = np.uint32(h1 % n)
        if portlastidx[hs] == -1:  # portfolio not found
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
    Finds the indices of records matching given date, portfolio, symbol keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'date', 'portfolio', 'symbol' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with 'date', 'portfolio', 'symbol' fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
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
    Insert or update records in a hash table using quadratic probing for collision resolution.
    
    Maintains auxiliary indices for efficient lookups by date, symbol, and/or portfolio fields.
    
    Parameters:
    - records (np.ndarray): Array of existing records to be updated or appended.
    - count (int): Current number of records in the records array.
    - new_records (np.ndarray): Array of new records to be inserted or used to update existing records.
    - pkey (np.ndarray): Hash table array mapping hash indices to record indices in records.
    
    Returns:
    - count (int): Updated count of records after insertion/updating.
    - minchgid (int): The smallest index of the record that was changed or inserted.
    - isidxsorted (bool): Whether the date index remains sorted (True if no date index).
    - positions (np.ndarray): Array of positions where each new record was inserted/updated.
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
    
    # Create array to track positions of new records
    positions = np.full(nrec, -1, dtype=np.int64)

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
                    # record exists update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    positions[i] = pkey[h]  # Add position of updated record
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
                positions[i] = count  # Add position of new record

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
                    found_port = True
                    j = 1
                    while records[portlastidx[hs]]['portfolio'] != new_records[i]['portfolio']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if portlastidx[hs] == -1:
                            portlastidx[hs] = count
                            portprevidx[count] = -1
                            found_port = False
                            break
                        j += 1

                    if found_port:
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

    return count, minchgid, isidxsorted, positions


###################### DATE_PORTFOLIO_REQUESTID ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_portfolio_requestid_jit(records, count, pkey, datelastidx, dateprevidx, mindate, periodns, portlastidx, portprevidx, start):
    """
    Creates and updates primary key and indexing arrays for records based on date, portfolio, requestid fields.
    
    Uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    Also maintains linked lists for efficient indexing by various fields.
    
    Parameters:
    - records (structured array): Array of records containing 'date', 'portfolio', 'requestid' fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
    """
    n = np.uint32(pkey.size-1)
    for i in range(start, count):        
        h0 = np.uint64(records['date'][i])
        h1 = djb2_hash(records['portfolio'][i])
        h2 = djb2_hash(records['requestid'][i])
        h = np.uint32((h0 ^ h1 ^ h2) % n)
        if pkey[h] == -1:
            pkey[h] = i
        else:
            duplicatedkey = True
            j = 1
            while (
                    (records[pkey[h]]['date'] != records[i]['date']) |
                    (records[pkey[h]]['portfolio'] != records[i]['portfolio']) |
                    (records[pkey[h]]['requestid'] != records[i]['requestid'])
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
        # update portfolio index
        hs = np.uint32(h1 % n)
        if portlastidx[hs] == -1:  # portfolio not found
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
def get_loc_date_portfolio_requestid_jit(records, pkey, keys):
    """
    Finds the indices of records matching given date, portfolio, requestid keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'date', 'portfolio', 'requestid' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with 'date', 'portfolio', 'requestid' fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
    """
    n = np.uint32(pkey.size-1)
    loc = np.empty((keys.size, ))
    for i in range(keys.size):
        h0 = np.uint64(keys['date'][i])
        h1 = djb2_hash(keys['portfolio'][i])
        h2 = djb2_hash(keys['requestid'][i])
        h = np.uint32((h0 ^ h1 ^ h2) % n)
        if pkey[h] == -1:
            loc[i] = pkey[h]
        else:
            j = 1
            while (
                    (records[pkey[h]]['date'] != keys[i]['date']) |
                    (records[pkey[h]]['portfolio'] != keys[i]['portfolio']) |
                    (records[pkey[h]]['requestid'] != keys[i]['requestid'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1
            loc[i] = pkey[h]
    
    return loc

@njit(cache=CACHE_JITTED)
def upsert_date_portfolio_requestid_jit(records, count, new_records, pkey, 
                            datelastidx, dateprevidx, mindate, periodns,
                            portlastidx, portprevidx, symbollastidx, symbolprevidx):
    """
    Insert or update records in a hash table using quadratic probing for collision resolution.
    
    Maintains auxiliary indices for efficient lookups by date, symbol, and/or portfolio fields.
    
    Parameters:
    - records (np.ndarray): Array of existing records to be updated or appended.
    - count (int): Current number of records in the records array.
    - new_records (np.ndarray): Array of new records to be inserted or used to update existing records.
    - pkey (np.ndarray): Hash table array mapping hash indices to record indices in records.
    
    Returns:
    - count (int): Updated count of records after insertion/updating.
    - minchgid (int): The smallest index of the record that was changed or inserted.
    - isidxsorted (bool): Whether the date index remains sorted (True if no date index).
    - positions (np.ndarray): Array of positions where each new record was inserted/updated.
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
    
    # Create array to track positions of new records
    positions = np.full(nrec, -1, dtype=np.int64)

    for i in range(nrec):        
        h0 = np.uint64(new_records['date'][i])
        h1 = djb2_hash(new_records['portfolio'][i])
        h2 = djb2_hash(new_records['requestid'][i])
        h = np.uint32((h0 ^ h1 ^ h2) % n)
        found = False

        if pkey[h] != -1:  # hash already exists
            j = 1
            while True:  # check for collision & find a free bucket
                if (records[pkey[h]]['date'] == new_records[i]['date'] and
                   records[pkey[h]]['portfolio'] == new_records[i]['portfolio'] and
                   records[pkey[h]]['requestid'] == new_records[i]['requestid']):
                    # record exists update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    positions[i] = pkey[h]  # Add position of updated record
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
                positions[i] = count  # Add position of new record

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
                    found_port = True
                    j = 1
                    while records[portlastidx[hs]]['portfolio'] != new_records[i]['portfolio']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if portlastidx[hs] == -1:
                            portlastidx[hs] = count
                            portprevidx[count] = -1
                            found_port = False
                            break
                        j += 1

                    if found_port:
                        portprevidx[count] = portlastidx[hs]
                        portlastidx[hs] = count

                minchgid = min(minchgid, count)
                count += 1

    return count, minchgid, isidxsorted, positions


###################### DATE_PORTFOLIO_CLORDID ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_portfolio_clordid_jit(records, count, pkey, datelastidx, dateprevidx, mindate, periodns, portlastidx, portprevidx, start):
    """
    Creates and updates primary key and indexing arrays for records based on date, portfolio, clordid fields.
    
    Uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    Also maintains linked lists for efficient indexing by various fields.
    
    Parameters:
    - records (structured array): Array of records containing 'date', 'portfolio', 'clordid' fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
    """
    n = np.uint32(pkey.size-1)
    for i in range(start, count):        
        h0 = np.uint64(records['date'][i])
        h1 = djb2_hash(records['portfolio'][i])
        h2 = djb2_hash(records['clordid'][i])
        h = np.uint32((h0 ^ h1 ^ h2) % n)
        if pkey[h] == -1:
            pkey[h] = i
        else:
            duplicatedkey = True
            j = 1
            while (
                    (records[pkey[h]]['date'] != records[i]['date']) |
                    (records[pkey[h]]['portfolio'] != records[i]['portfolio']) |
                    (records[pkey[h]]['clordid'] != records[i]['clordid'])
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
        # update portfolio index
        hs = np.uint32(h1 % n)
        if portlastidx[hs] == -1:  # portfolio not found
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
def get_loc_date_portfolio_clordid_jit(records, pkey, keys):
    """
    Finds the indices of records matching given date, portfolio, clordid keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'date', 'portfolio', 'clordid' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with 'date', 'portfolio', 'clordid' fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
    """
    n = np.uint32(pkey.size-1)
    loc = np.empty((keys.size, ))
    for i in range(keys.size):
        h0 = np.uint64(keys['date'][i])
        h1 = djb2_hash(keys['portfolio'][i])
        h2 = djb2_hash(keys['clordid'][i])
        h = np.uint32((h0 ^ h1 ^ h2) % n)
        if pkey[h] == -1:
            loc[i] = pkey[h]
        else:
            j = 1
            while (
                    (records[pkey[h]]['date'] != keys[i]['date']) |
                    (records[pkey[h]]['portfolio'] != keys[i]['portfolio']) |
                    (records[pkey[h]]['clordid'] != keys[i]['clordid'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1
            loc[i] = pkey[h]
    
    return loc

@njit(cache=CACHE_JITTED)
def upsert_date_portfolio_clordid_jit(records, count, new_records, pkey, 
                            datelastidx, dateprevidx, mindate, periodns,
                            portlastidx, portprevidx, symbollastidx, symbolprevidx):
    """
    Insert or update records in a hash table using quadratic probing for collision resolution.
    
    Maintains auxiliary indices for efficient lookups by date, symbol, and/or portfolio fields.
    
    Parameters:
    - records (np.ndarray): Array of existing records to be updated or appended.
    - count (int): Current number of records in the records array.
    - new_records (np.ndarray): Array of new records to be inserted or used to update existing records.
    - pkey (np.ndarray): Hash table array mapping hash indices to record indices in records.
    
    Returns:
    - count (int): Updated count of records after insertion/updating.
    - minchgid (int): The smallest index of the record that was changed or inserted.
    - isidxsorted (bool): Whether the date index remains sorted (True if no date index).
    - positions (np.ndarray): Array of positions where each new record was inserted/updated.
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
    
    # Create array to track positions of new records
    positions = np.full(nrec, -1, dtype=np.int64)

    for i in range(nrec):        
        h0 = np.uint64(new_records['date'][i])
        h1 = djb2_hash(new_records['portfolio'][i])
        h2 = djb2_hash(new_records['clordid'][i])
        h = np.uint32((h0 ^ h1 ^ h2) % n)
        found = False

        if pkey[h] != -1:  # hash already exists
            j = 1
            while True:  # check for collision & find a free bucket
                if (records[pkey[h]]['date'] == new_records[i]['date'] and
                   records[pkey[h]]['portfolio'] == new_records[i]['portfolio'] and
                   records[pkey[h]]['clordid'] == new_records[i]['clordid']):
                    # record exists update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    positions[i] = pkey[h]  # Add position of updated record
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
                positions[i] = count  # Add position of new record

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
                    found_port = True
                    j = 1
                    while records[portlastidx[hs]]['portfolio'] != new_records[i]['portfolio']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if portlastidx[hs] == -1:
                            portlastidx[hs] = count
                            portprevidx[count] = -1
                            found_port = False
                            break
                        j += 1

                    if found_port:
                        portprevidx[count] = portlastidx[hs]
                        portlastidx[hs] = count

                minchgid = min(minchgid, count)
                count += 1

    return count, minchgid, isidxsorted, positions


###################### DATE_PORTFOLIO_SYMBOL_TRADEID ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_portfolio_symbol_tradeid_jit(records, count, pkey, datelastidx, dateprevidx, mindate, periodns, portlastidx, portprevidx, symbollastidx, symbolprevidx, start):
    """
    Creates and updates primary key and indexing arrays for records based on date, portfolio, symbol, tradeid fields.
    
    Uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    Also maintains linked lists for efficient indexing by various fields.
    
    Parameters:
    - records (structured array): Array of records containing 'date', 'portfolio', 'symbol', 'tradeid' fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
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
        # update portfolio index
        hs = np.uint32(h1 % n)
        if portlastidx[hs] == -1:  # portfolio not found
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
    Finds the indices of records matching given date, portfolio, symbol, tradeid keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'date', 'portfolio', 'symbol', 'tradeid' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with 'date', 'portfolio', 'symbol', 'tradeid' fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
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
    Insert or update records in a hash table using quadratic probing for collision resolution.
    
    Maintains auxiliary indices for efficient lookups by date, symbol, and/or portfolio fields.
    
    Parameters:
    - records (np.ndarray): Array of existing records to be updated or appended.
    - count (int): Current number of records in the records array.
    - new_records (np.ndarray): Array of new records to be inserted or used to update existing records.
    - pkey (np.ndarray): Hash table array mapping hash indices to record indices in records.
    
    Returns:
    - count (int): Updated count of records after insertion/updating.
    - minchgid (int): The smallest index of the record that was changed or inserted.
    - isidxsorted (bool): Whether the date index remains sorted (True if no date index).
    - positions (np.ndarray): Array of positions where each new record was inserted/updated.
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
    
    # Create array to track positions of new records
    positions = np.full(nrec, -1, dtype=np.int64)

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
                    # record exists update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    positions[i] = pkey[h]  # Add position of updated record
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
                positions[i] = count  # Add position of new record

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
                    found_port = True
                    j = 1
                    while records[portlastidx[hs]]['portfolio'] != new_records[i]['portfolio']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if portlastidx[hs] == -1:
                            portlastidx[hs] = count
                            portprevidx[count] = -1
                            found_port = False
                            break
                        j += 1

                    if found_port:
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

    return count, minchgid, isidxsorted, positions


###################### DATE_SYMBOL_EXPIRY_STRIKE_CALLPUT ########################
@njit(cache=CACHE_JITTED)
def create_pkey_date_symbol_expiry_strike_callput_jit(records, count, pkey, datelastidx, dateprevidx, mindate, periodns, symbollastidx, symbolprevidx, start):
    """
    Creates and updates primary key and indexing arrays for records based on date, symbol, expiry, strike, callput fields.
    
    Uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    Also maintains linked lists for efficient indexing by various fields.
    
    Parameters:
    - records (structured array): Array of records containing 'date', 'symbol', 'expiry', 'strike', 'callput' fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
    """
    n = np.uint32(pkey.size-1)
    for i in range(start, count):        
        h0 = np.uint64(records['date'][i])
        h1 = djb2_hash(records['symbol'][i])
        h2 = hash_int64(records['expiry'][i])
        h3 = hash_int64(records['strike'][i])
        h4 = djb2_hash(records['callput'][i])
        h = np.uint32((h0 ^ h1 ^ h2 ^ h3 ^ h4) % n)
        if pkey[h] == -1:
            pkey[h] = i
        else:
            duplicatedkey = True
            j = 1
            while (
                    (records[pkey[h]]['date'] != records[i]['date']) |
                    (records[pkey[h]]['symbol'] != records[i]['symbol']) |
                    (records[pkey[h]]['expiry'] != records[i]['expiry']) |
                    (records[pkey[h]]['strike'] != records[i]['strike']) |
                    (records[pkey[h]]['callput'] != records[i]['callput'])
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
def get_loc_date_symbol_expiry_strike_callput_jit(records, pkey, keys):
    """
    Finds the indices of records matching given date, symbol, expiry, strike, callput keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with 'date', 'symbol', 'expiry', 'strike', 'callput' fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with 'date', 'symbol', 'expiry', 'strike', 'callput' fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
    """
    n = np.uint32(pkey.size-1)
    loc = np.empty((keys.size, ))
    for i in range(keys.size):
        h0 = np.uint64(keys['date'][i])
        h1 = djb2_hash(keys['symbol'][i])
        h2 = hash_int64(keys['expiry'][i])
        h3 = hash_int64(keys['strike'][i])
        h4 = djb2_hash(keys['callput'][i])
        h = np.uint32((h0 ^ h1 ^ h2 ^ h3 ^ h4) % n)
        if pkey[h] == -1:
            loc[i] = pkey[h]
        else:
            j = 1
            while (
                    (records[pkey[h]]['date'] != keys[i]['date']) |
                    (records[pkey[h]]['symbol'] != keys[i]['symbol']) |
                    (records[pkey[h]]['expiry'] != keys[i]['expiry']) |
                    (records[pkey[h]]['strike'] != keys[i]['strike']) |
                    (records[pkey[h]]['callput'] != keys[i]['callput'])
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1
            loc[i] = pkey[h]
    
    return loc

@njit(cache=CACHE_JITTED)
def upsert_date_symbol_expiry_strike_callput_jit(records, count, new_records, pkey, 
                            datelastidx, dateprevidx, mindate, periodns,
                            portlastidx, portprevidx, symbollastidx, symbolprevidx):
    """
    Insert or update records in a hash table using quadratic probing for collision resolution.
    
    Maintains auxiliary indices for efficient lookups by date, symbol, and/or portfolio fields.
    
    Parameters:
    - records (np.ndarray): Array of existing records to be updated or appended.
    - count (int): Current number of records in the records array.
    - new_records (np.ndarray): Array of new records to be inserted or used to update existing records.
    - pkey (np.ndarray): Hash table array mapping hash indices to record indices in records.
    
    Returns:
    - count (int): Updated count of records after insertion/updating.
    - minchgid (int): The smallest index of the record that was changed or inserted.
    - isidxsorted (bool): Whether the date index remains sorted (True if no date index).
    - positions (np.ndarray): Array of positions where each new record was inserted/updated.
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
    
    # Create array to track positions of new records
    positions = np.full(nrec, -1, dtype=np.int64)

    for i in range(nrec):        
        h0 = np.uint64(new_records['date'][i])
        h1 = djb2_hash(new_records['symbol'][i])
        h2 = hash_int64(new_records['expiry'][i])
        h3 = hash_int64(new_records['strike'][i])
        h4 = djb2_hash(new_records['callput'][i])
        h = np.uint32((h0 ^ h1 ^ h2 ^ h3 ^ h4) % n)
        found = False

        if pkey[h] != -1:  # hash already exists
            j = 1
            while True:  # check for collision & find a free bucket
                if (records[pkey[h]]['date'] == new_records[i]['date'] and
                   records[pkey[h]]['symbol'] == new_records[i]['symbol'] and
                   records[pkey[h]]['expiry'] == new_records[i]['expiry'] and
                   records[pkey[h]]['strike'] == new_records[i]['strike'] and
                   records[pkey[h]]['callput'] == new_records[i]['callput']):
                    # record exists update it
                    records[pkey[h]] = new_records[i]
                    minchgid = min(minchgid, pkey[h])
                    positions[i] = pkey[h]  # Add position of updated record
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
                positions[i] = count  # Add position of new record

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

    return count, minchgid, isidxsorted, positions

