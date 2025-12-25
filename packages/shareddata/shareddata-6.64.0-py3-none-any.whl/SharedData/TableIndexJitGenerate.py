"""
Code generator for TableIndexJitFunctions.py

This script generates the three core JIT-compiled functions for each database type:
1. create_pkey_<pkey>_jit - Creates the primary key hash table and auxiliary indices
2. get_loc_<pkey>_jit - Retrieves record locations by key lookup
3. upsert_<pkey>_jit - Inserts or updates records with index maintenance

The generator handles special cases like the Relationships database where symbol != symbol1
uses a different hash calculation.
"""

from typing import List, Dict, Tuple
from SharedData.Database import DATABASE_PKEYS, STRING_FIELDS, NUMERIC_FIELDS


def get_hash_calculation(fields: List[str], record_prefix: str = "records", index: str = "i", 
                         special_relationships: bool = False) -> Tuple[List[str], str]:
    """
    Generate hash calculation code for given fields.
    
    Args:
        fields: List of field names to hash
        record_prefix: Prefix for accessing records (e.g., 'records', 'new_records', 'keys')
        index: Index variable name
        special_relationships: If True, handle special Relationships logic for symbol/symbol1
        
    Returns:
        Tuple of (hash_variable_lines, final_hash_expression)
    """
    hash_vars = []
    hash_components = []
    
    for field_idx, field in enumerate(fields):
        var_name = f"h{field_idx}"
        
        if field == 'date':
            hash_vars.append(f"        {var_name} = np.uint64({record_prefix}['{field}'][{index}])")
            hash_components.append(var_name)
        elif field in STRING_FIELDS or field in ['symbol1', 'callput']:  # String-like fields
            hash_vars.append(f"        {var_name} = djb2_hash({record_prefix}['{field}'][{index}])")
            hash_components.append(var_name)
        elif field in NUMERIC_FIELDS or field in ['expiry', 'strike']:  # Numeric fields
            hash_vars.append(f"        {var_name} = hash_int64({record_prefix}['{field}'][{index}])")
            hash_components.append(var_name)
        else:
            raise ValueError(f"Unknown field type: {field}")
    
    # Special case for Relationships: symbol != symbol1 uses different hash
    if special_relationships and 'symbol' in fields and 'symbol1' in fields:
        # Find indices of symbol fields
        symbol_idx = fields.index('symbol')
        symbol1_idx = fields.index('symbol1')
        
        # Create conditional hash calculation
        hash_expr_with_symbol1 = " ^ ".join(hash_components)
        # Remove symbol1 component for when symbol == symbol1
        hash_components_no_symbol1 = [c for i, c in enumerate(hash_components) if i != symbol1_idx]
        hash_expr_without_symbol1 = " ^ ".join(hash_components_no_symbol1)
        
        return (hash_vars, None, hash_expr_with_symbol1, hash_expr_without_symbol1)
    else:
        if len(hash_components) == 1:
            final_expr = hash_components[0]
        else:
            final_expr = " ^ ".join(hash_components)
        
        return (hash_vars, final_expr, None, None)


def get_comparison_condition(fields: List[str], left_prefix: str, left_index: str,
                             right_prefix: str, right_index: str, indent: int = 20) -> str:
    """Generate comparison condition for checking if records match."""
    conditions = []
    for field in fields:
        # Handle proper indexing
        left_access = f"{left_prefix}[{left_index}]" if left_index else left_prefix
        right_access = f"{right_prefix}[{right_index}]" if right_index else right_prefix
        conditions.append(f"({left_access}['{field}'] != {right_access}['{field}'])")
    
    if len(conditions) == 1:
        return conditions[0]
    else:
        separator = f" |\n{' ' * indent}"
        return separator.join(conditions)


def get_equality_condition(fields: List[str], left_prefix: str, left_index: str,
                           right_prefix: str, right_index: str) -> str:
    """Generate equality condition for checking if records match (using 'and')."""
    conditions = []
    for field in fields:
        # Handle proper indexing
        left_access = f"{left_prefix}[{left_index}]" if left_index else left_prefix
        right_access = f"{right_prefix}[{right_index}]" if right_index else right_prefix
        conditions.append(f"{left_access}['{field}'] == {right_access}['{field}']")
    
    return " and\n                   ".join(conditions)


def get_auxiliary_indices(fields: List[str]) -> Dict[str, bool]:
    """Determine which auxiliary indices are needed based on primary key fields."""
    return {
        'date': 'date' in fields,
        'symbol': 'symbol' in fields and len(fields) > 1,
        'portfolio': 'portfolio' in fields,
        'tag': 'tag' in fields,
    }


def generate_create_pkey_function(database: str, pkey_fields: List[str]) -> str:
    """Generate create_pkey_<pkey>_jit function."""
    pkey_str = "_".join(pkey_fields)
    func_name = f"create_pkey_{pkey_str}_jit"
    
    # Check if this is the Relationships database with special logic
    is_relationships = (database == 'Relationships' and 'symbol' in pkey_fields and 'symbol1' in pkey_fields)
    
    aux_indices = get_auxiliary_indices(pkey_fields)
    
    # Build function signature
    params = ["records", "count", "pkey"]
    if aux_indices['date']:
        params.extend(["datelastidx", "dateprevidx", "mindate", "periodns"])
    # Always use portlastidx/portprevidx for tag fields to match hardcoded upsert signature
    if aux_indices['tag'] or aux_indices['portfolio']:
        params.extend(["portlastidx", "portprevidx"])
    if aux_indices['symbol']:
        params.extend(["symbollastidx", "symbolprevidx"])
    params.append("start")
    
    param_str = ", ".join(params)
    
    # Generate hash calculation
    if is_relationships:
        hash_vars, _, hash_with_s1, hash_without_s1 = get_hash_calculation(pkey_fields, special_relationships=True)
        # For the conditional block, we need hash variables indented properly
        hash_calc = f"""        if records['symbol'][i] != records['symbol1'][i]:
            h0 = np.uint64(records['date'][i])
            h1 = djb2_hash(records['symbol'][i])
            h2 = djb2_hash(records['symbol1'][i])
            h = np.uint32(({hash_with_s1}) % n)
        else:
            h0 = np.uint64(records['date'][i])
            h1 = djb2_hash(records['symbol'][i])
            h = np.uint32(({hash_without_s1}) % n)"""
    else:
        hash_vars, hash_expr, _, _ = get_hash_calculation(pkey_fields)
        hash_block = "\n".join(hash_vars)
        hash_calc = f"""{hash_block}
        h = np.uint32(({hash_expr}) % n)"""
    
    # Generate comparison condition
    comparison = get_comparison_condition(pkey_fields, "records", "pkey[h]", "records", "i")
    
    # Generate auxiliary index updates
    aux_updates = []
    
    if aux_indices['date']:
        aux_updates.append("""
        # update date index
        intdt = np.uint32( (np.uint64(records['date'][i]) - np.uint64(mindate)) // np.uint64(periodns) )
        if datelastidx[intdt] == -1:  # date not found
            datelastidx[intdt] = i
            dateprevidx[i] = -1
        else: # found            
            dateprevidx[i] = datelastidx[intdt]
            datelastidx[intdt] = i""")
    
    if aux_indices['portfolio']:
        port_field = 'portfolio'
        port_hash_idx = pkey_fields.index(port_field)
        aux_updates.append(f"""
        # update portfolio index
        hs = np.uint32(h{port_hash_idx} % n)
        if portlastidx[hs] == -1:  # portfolio not found
            portlastidx[hs] = i
            portprevidx[i] = -1
        else:
            # check for collision
            found = True
            j = 1
            while (records[i]['{port_field}'] != records[portlastidx[hs]]['{port_field}']):
                hs = np.uint32((hs + j**2) % n)
                if portlastidx[hs] == -1:
                    portlastidx[hs] = i
                    portprevidx[i] = -1
                    found = False
                    break
                j += 1

            if found:
                portprevidx[i] = portlastidx[hs]
                portlastidx[hs] = i""")

    if aux_indices['tag']:
        tag_field = 'tag'
        tag_hash_idx = pkey_fields.index(tag_field)
        aux_updates.append(f"""
        # update tag index
        hs = np.uint32(h{tag_hash_idx} % n)
        if portlastidx[hs] == -1:  # tag not found
            portlastidx[hs] = i
            portprevidx[i] = -1
        else:
            # check for collision
            found = True
            j = 1
            while (records[i]['{tag_field}'] != records[portlastidx[hs]]['{tag_field}']):
                hs = np.uint32((hs + j**2) % n)
                if portlastidx[hs] == -1:
                    portlastidx[hs] = i
                    portprevidx[i] = -1
                    found = False
                    break
                j += 1

            if found:
                portprevidx[i] = portlastidx[hs]
                portlastidx[hs] = i""")
    
    if aux_indices['symbol']:
        # Use hash component corresponding to 'symbol' field specifically
        symbol_hash_idx = pkey_fields.index('symbol')
        aux_updates.append(f"""
        # update symbol index
        hs = np.uint32(h{symbol_hash_idx} % n)
        if symbollastidx[hs] == -1:  # symbol not found
            symbollastidx[hs] = i
            symbolprevidx[i] = -1
        else:
            # check for collision
            found = True
            j = 1
            while (records[i]['{pkey_fields[symbol_hash_idx]}'] != records[symbollastidx[hs]]['{pkey_fields[symbol_hash_idx]}']):
                hs = np.uint32((hs + j**2) % n)
                if symbollastidx[hs] == -1:
                    symbollastidx[hs] = i
                    symbolprevidx[i] = -1
                    found = False
                    break
                j += 1

            if found:
                symbolprevidx[i] = symbollastidx[hs]
                symbollastidx[hs] = i""")
    
    aux_updates_str = "".join(aux_updates)
    
    # Build function
    code = f"""###################### {pkey_str.upper()} ########################
@njit(cache=CACHE_JITTED)
def {func_name}({param_str}):
    \"\"\"
    Creates and updates primary key and indexing arrays for records based on {', '.join(pkey_fields)} fields.
    
    Uses quadratic probing to resolve hash collisions when inserting records into a primary key hash table.
    Also maintains linked lists for efficient indexing by various fields.
    
    Parameters:
    - records (structured array): Array of records containing {', '.join(f"'{f}'" for f in pkey_fields)} fields.
    - count (int): Total number of records to process starting from the 'start' index.
    - pkey (ndarray): Hash table array for primary keys, initialized with -1 indicating empty slots.
    - start (int): Starting index in records from which to begin processing.
    
    Returns:
    - bool: True if all records were successfully inserted without unresolvable collisions; False otherwise.
    \"\"\"
    n = np.uint32(pkey.size-1)
    for i in range(start, count):        
{hash_calc}
        if pkey[h] == -1:
            pkey[h] = i
        else:
            duplicatedkey = True
            j = 1
            while (
                    {comparison}
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    pkey[h] = i
                    duplicatedkey = False
                    break
                j += 1
            if duplicatedkey:
                return False
{aux_updates_str}

    return True
"""
    return code


def generate_get_loc_function(database: str, pkey_fields: List[str]) -> str:
    """Generate get_loc_<pkey>_jit function."""
    pkey_str = "_".join(pkey_fields)
    func_name = f"get_loc_{pkey_str}_jit"
    
    # Check if this is the Relationships database
    is_relationships = (database == 'Relationships' and 'symbol' in pkey_fields and 'symbol1' in pkey_fields)
    
    # Generate hash calculation
    if is_relationships:
        hash_vars, _, hash_with_s1, hash_without_s1 = get_hash_calculation(pkey_fields, record_prefix="keys", special_relationships=True)
        # For the conditional block, we need hash variables indented properly
        hash_calc = f"""        if keys['symbol'][i] != keys['symbol1'][i]:
            h0 = np.uint64(keys['date'][i])
            h1 = djb2_hash(keys['symbol'][i])
            h2 = djb2_hash(keys['symbol1'][i])
            h = np.uint32(({hash_with_s1}) % n)
        else:
            h0 = np.uint64(keys['date'][i])
            h1 = djb2_hash(keys['symbol'][i])
            h = np.uint32(({hash_without_s1}) % n)"""
    else:
        hash_vars, hash_expr, _, _ = get_hash_calculation(pkey_fields, record_prefix="keys")
        hash_block = "\n".join(hash_vars)
        hash_calc = f"""{hash_block}
        h = np.uint32(({hash_expr}) % n)"""
    
    # Generate comparison condition
    comparison = get_comparison_condition(pkey_fields, "records", "pkey[h]", "keys", "i")
    
    code = f"""@njit(cache=CACHE_JITTED)
def {func_name}(records, pkey, keys):
    \"\"\"
    Finds the indices of records matching given {', '.join(pkey_fields)} keys using a hash table with quadratic probing.
    
    Parameters:
        records (np.ndarray): Structured array containing records with {', '.join(f"'{f}'" for f in pkey_fields)} fields.
        pkey (np.ndarray): Hash table array mapping hashed keys to indices in records, with -1 indicating empty slots.
        keys (np.ndarray): Structured array of keys with {', '.join(f"'{f}'" for f in pkey_fields)} fields to look up in records.
    
    Returns:
        np.ndarray: Array of indices in records corresponding to each key in keys; -1 if no match is found.
    \"\"\"
    n = np.uint32(pkey.size-1)
    loc = np.empty((keys.size, ){', dtype=np.int64' if pkey_fields == ['date','symbol'] else ''})
    for i in range(keys.size):
{hash_calc}
        if pkey[h] == -1:
            loc[i] = pkey[h]
        else:
            j = 1
            while (
                    {comparison}
            ):
                h = np.uint32((h + j ** 2) % n)
                if pkey[h] == -1:
                    break
                j += 1
            loc[i] = pkey[h]
    
    return loc
"""
    return code


def generate_upsert_function(database: str, pkey_fields: List[str]) -> str:
    """Generate upsert_<pkey>_jit function."""
    pkey_str = "_".join(pkey_fields)
    func_name = f"upsert_{pkey_str}_jit"
    
    # Check if this is the Relationships database
    is_relationships = (database == 'Relationships' and 'symbol' in pkey_fields and 'symbol1' in pkey_fields)
    
    aux_indices = get_auxiliary_indices(pkey_fields)
    has_date = aux_indices['date']
    
    # Generate hash calculation
    if is_relationships:
        hash_vars, _, hash_with_s1, hash_without_s1 = get_hash_calculation(pkey_fields, record_prefix="new_records", special_relationships=True)
        # For the conditional block, we need hash variables indented properly
        hash_calc = f"""        if new_records['symbol'][i] != new_records['symbol1'][i]:
            h0 = np.uint64(new_records['date'][i])
            h1 = djb2_hash(new_records['symbol'][i])
            h2 = djb2_hash(new_records['symbol1'][i])
            h = np.uint32(({hash_with_s1}) % n)
        else:
            h0 = np.uint64(new_records['date'][i])
            h1 = djb2_hash(new_records['symbol'][i])
            h = np.uint32(({hash_without_s1}) % n)"""
    else:
        hash_vars, hash_expr, _, _ = get_hash_calculation(pkey_fields, record_prefix="new_records")
        hash_block = "\n".join(hash_vars)
        hash_calc = f"""{hash_block}
        h = np.uint32(({hash_expr}) % n)"""
    
    # Generate equality condition for update check
    equality = get_equality_condition(pkey_fields, "records", "pkey[h]", "new_records", "i")
    
    # Generate auxiliary index updates for new records
    aux_updates = []
    
    if aux_indices['date']:
        aux_updates.append("""
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
                    datelastidx[intdt] = count""")
    
    if aux_indices['portfolio']:
        port_field = 'portfolio'
        port_hash_idx = pkey_fields.index(port_field)
        aux_updates.append(f"""
                # update portfolio index
                hs = np.uint32(h{port_hash_idx} % n)
                if portlastidx[hs] == -1:  # portfolio not found
                    portlastidx[hs] = count
                    portprevidx[count] = -1
                else:
                    # check for collision and find the appropriate bucket
                    found_port = True
                    j = 1
                    while records[portlastidx[hs]]['{port_field}'] != new_records[i]['{port_field}']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if portlastidx[hs] == -1:
                            portlastidx[hs] = count
                            portprevidx[count] = -1
                            found_port = False
                            break
                        j += 1

                    if found_port:
                        portprevidx[count] = portlastidx[hs]
                        portlastidx[hs] = count""")

    if aux_indices['tag']:
        tag_field = 'tag'
        tag_hash_idx = pkey_fields.index(tag_field)
        aux_updates.append(f"""
                # update tag index
                hs = np.uint32(h{tag_hash_idx} % n)
                if portlastidx[hs] == -1:  # tag not found
                    portlastidx[hs] = count
                    portprevidx[count] = -1
                else:
                    # check for collision and find the appropriate bucket
                    found_tag = True
                    j = 1
                    while records[portlastidx[hs]]['{tag_field}'] != new_records[i]['{tag_field}']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if portlastidx[hs] == -1:
                            portlastidx[hs] = count
                            portprevidx[count] = -1
                            found_tag = False
                            break
                        j += 1

                    if found_tag:
                        portprevidx[count] = portlastidx[hs]
                        portlastidx[hs] = count""")
    
    if aux_indices['symbol']:
        symbol_hash_idx = pkey_fields.index('symbol')
        symbol_field = pkey_fields[symbol_hash_idx]
        aux_updates.append(f"""
                # update symbol index
                hs = np.uint32(h{symbol_hash_idx} % n)
                if symbollastidx[hs] == -1:  # symbol not found
                    symbollastidx[hs] = count
                    symbolprevidx[count] = -1
                else:
                    # check for collision and find the appropriate bucket
                    found_symbol = True
                    j = 1
                    while records[symbollastidx[hs]]['{symbol_field}'] != new_records[i]['{symbol_field}']:
                        hs = np.uint32((hs + j ** 2) % n)
                        if symbollastidx[hs] == -1:
                            symbollastidx[hs] = count
                            symbolprevidx[count] = -1
                            found_symbol = False
                            break
                        j += 1

                    if found_symbol:
                        symbolprevidx[count] = symbollastidx[hs]
                        symbollastidx[hs] = count""")
    
    aux_updates_str = "".join(aux_updates)
    
    # Track last date initialization
    lastdate_init = ""
    if has_date:
        lastdate_init = """    # track last date to check if idx is sorted
    isidxsorted = True
    if count>0:
        lastdate = np.int64(records[count-1]['date'])
    else:
        lastdate = 0
    """
    
    code = f"""@njit(cache=CACHE_JITTED)
def {func_name}(records, count, new_records, pkey, 
                {'                ' if len(pkey_fields) <= 2 else '            '}datelastidx, dateprevidx, mindate, periodns,
                {'                ' if len(pkey_fields) <= 2 else '            '}portlastidx, portprevidx, symbollastidx, symbolprevidx):
    \"\"\"
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
    \"\"\"
    minchgid = count
    maxsize = records.size
    nrec = new_records.size
    n = np.uint32(pkey.size-1)
{lastdate_init}
    # Create array to track positions of new records
    positions = np.full(nrec, -1, dtype=np.int64)

    for i in range(nrec):        
{hash_calc}
        found = False

        if pkey[h] != -1:  # hash already exists
            j = 1
            while True:  # check for collision & find a free bucket
                if ({equality}):
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
{aux_updates_str}

                minchgid = min(minchgid, count)
                count += 1

    return count, minchgid, {'isidxsorted' if has_date else 'True'}, positions
"""
    return code


def generate_all_functions() -> str:
    """Generate all JIT functions for all database types."""
    output = []
    
    # Header
    output.append("""from numba.typed import List
import numpy as np
from numba import njit

from SharedData.TableIndexJitHash import djb2_hash, hash_int64, hash_float64, CACHE_JITTED
""")
    
    # Generate functions for each database
    for database, pkey_fields in DATABASE_PKEYS.items():
        output.append(generate_create_pkey_function(database, pkey_fields))
        output.append(generate_get_loc_function(database, pkey_fields))
        output.append(generate_upsert_function(database, pkey_fields))
        output.append("")  # Add blank line between databases
    
    return "\n".join(output)


if __name__ == "__main__":
    # Generate all functions
    generated_code = generate_all_functions()
    
    # Write to file
    output_path = "TableIndexJitFunctions_Generated.py"
    with open(output_path, 'w') as f:
        f.write(generated_code)
    
    print(f"Generated JIT functions written to: {output_path}")
    print(f"Total databases processed: {len(DATABASE_PKEYS)}")
    print(f"Total functions generated: {len(DATABASE_PKEYS) * 3}")
