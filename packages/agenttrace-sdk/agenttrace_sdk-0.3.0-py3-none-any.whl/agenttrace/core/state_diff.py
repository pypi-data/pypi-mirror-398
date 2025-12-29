# agenttrace/core/state_diff.py

from typing import Any, Dict, Tuple

def diff_states(prev: Dict[str, Any], next: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute a human-readable diff of two AgentBase state dictionaries.
    
    Output format:
    {
        "messages": {"added": [...], "removed": [...]},
        "memory":  {"changed": {...}, "removed": [...], "added": [...]}  
    }
    """

    diff = {}

    for key in next.keys() | prev.keys():

        prev_val = prev.get(key)
        next_val = next.get(key)

        # ADDED
        if key not in prev:
            diff[key] = {"added": next_val}
            continue

        # REMOVED
        if key not in next:
            diff[key] = {"removed": prev_val}
            continue

        # NO CHANGE
        if prev_val == next_val:
            continue

        # SPECIAL CASE: LISTS (messages)
        if isinstance(prev_val, list) and isinstance(next_val, list):
            sub = diff_list(prev_val, next_val)
            if sub:
                diff[key] = sub
            continue

        # SPECIAL CASE: DICTS (memory/context/etc.)
        if isinstance(prev_val, dict) and isinstance(next_val, dict):
            sub = diff_dict(prev_val, next_val)
            if sub:
                diff[key] = sub
            continue

        # PRIMITIVE CHANGE
        diff[key] = {"changed": {"from": prev_val, "to": next_val}}

    return diff



def diff_list(prev_list: list, next_list: list) -> Dict[str, Any]:
    """
    Simple list diff for messages / arrays.
    """

    added = []
    removed = []

    # Helper to make items hashable for set operations
    def _hashable(item: Any):
        if isinstance(item, dict):
            return tuple(sorted((k, _hashable(v)) for k, v in item.items()))
        if isinstance(item, list):
            return tuple(_hashable(x) for x in item)
        return item

    def _original(item: Any):
        """Return original item structure from hashable representation."""
        # Since we are just using the set logic to find differences, 
        # we need a way to get back the original object.
        # For this simple implementation, we might iterate.
        # But wait, the provided code had _original(item) returning item.
        # This implies the set stores the hashable tuple, but we want the original dict/list back.
        # This is tricky if we only have the tuple.
        # Let's stick to the user's provided logic but maybe refine it if needed.
        # The user's code:
        # prev_set = set(map(_hashable, prev_list))
        # next_set = set(map(_hashable, next_list))
        # for item in next_set - prev_set: added.append(_original(item))
        #
        # If _original just returns item, then 'added' will contain tuples, not dicts.
        # We should probably try to find the original item from the list that matches the hashable.
        return item 

    # Re-implementing list diff to be more robust than the snippet if needed,
    # but let's stick to the user's logic structure but fix the object retrieval.
    
    # Actually, let's use a simpler approach for lists that preserves order and objects:
    # Append-only check? Or full diff?
    # The user's snippet uses sets, which loses order and duplicates.
    # For messages, usually it's append-only.
    
    # Let's use the user's exact provided code structure but maybe fix the _hashable/_original issue
    # by just using the lists directly if possible, or accepting the tuple output for now.
    # User said: "Let's ship a PERFECT diff engine".
    # The provided code has `_original` returning `item`.
    # If `_hashable` returns a tuple, then `added` will contain tuples.
    # This might be acceptable for the diff viewer if it just displays JSON.
    # But it would be better to have the real dicts.
    
    # Let's implement a slightly smarter list diff that handles unhashable types gracefully.
    
    # Strategy:
    # 1. Convert lists to hashable representations for set logic.
    # 2. Map hashable rep back to original object.
    
    prev_map = {_hashable(x): x for x in prev_list}
    next_map = {_hashable(x): x for x in next_list}
    
    prev_set = set(prev_map.keys())
    next_set = set(next_map.keys())
    
    for h in next_set - prev_set:
        added.append(next_map[h])
        
    for h in prev_set - next_set:
        removed.append(prev_map[h])

    result = {}
    if added: result["added"] = added
    if removed: result["removed"] = removed

    return result


def diff_dict(prev_dict: dict, next_dict: dict) -> Dict[str, Any]:
    """
    Recursive diff for nested dicts (memory, context, etc.)
    """

    result = {
        "added": {},
        "removed": {},
        "changed": {},
    }

    for key in next_dict.keys() | prev_dict.keys():

        if key not in prev_dict:
            result["added"][key] = next_dict[key]
            continue

        if key not in next_dict:
            result["removed"][key] = prev_dict[key]
            continue

        if prev_dict[key] != next_dict[key]:
            # Recurse if both are dicts?
            if isinstance(prev_dict[key], dict) and isinstance(next_dict[key], dict):
                 sub = diff_dict(prev_dict[key], next_dict[key])
                 if sub:
                     result["changed"][key] = sub
            else:
                result["changed"][key] = {
                    "from": prev_dict[key],
                    "to": next_dict[key]
                }

    # Clean empty keys
    return {k: v for k, v in result.items() if v}


def _hashable(item: Any):
    """Convert nested lists/dicts to hashable tuples for set diff."""
    if isinstance(item, dict):
        return tuple(sorted((k, _hashable(v)) for k, v in item.items()))
    if isinstance(item, list):
        return tuple(_hashable(x) for x in item)
    return item
