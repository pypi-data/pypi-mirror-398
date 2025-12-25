# merge.py
from typing import Any, Dict, Tuple, Iterable, Set, Optional

# ---------- your existing deep_merge (unchanged) ----------
def deep_merge(base: dict, updates: dict, delete_nulls: bool = True) -> dict:
    """
    Recursively merge two dictionaries.
    Args:
        base: original dict (must be a dict; caller should pass {} if None)
        updates: updates to apply
        delete_nulls: if True, keys with value None in updates are removed from result
    Returns:
        new dict with updates applied (shallow-copy semantics)
    """
    result = base.copy()
    for k, v in updates.items():
        if delete_nulls and v is None:
            result.pop(k, None)
        elif isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = deep_merge(result[k], v, delete_nulls)
        else:
            result[k] = v
    return result


# ---------- internal helpers (renamed with leading underscore) ----------
def _deep_get(obj: Optional[Dict[str, Any]], path: str) -> Tuple[Any, bool]:
    """
    Get a value by dot-path from a dict.
    Returns (value, found_flag). found_flag is True even when the found value is None.
    If path == "" returns (obj, True).
    """
    if obj is None:
        return None, False
    current = obj
    if path == "":
        return current, True
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None, False
        current = current[part]
    return current, True


def _compute_new_value_from_delta_or_data(
    data: Optional[Dict[str, Any]],
    delta: Optional[Dict[str, Any]],
    path: str,
    delete_nulls: bool = True,
) -> Tuple[Any, bool]:
    """
    Compute new value at `path` after applying delta onto data.

    - Ancestor-none or ancestor scalar behavior unchanged: if an ancestor is present in delta
      and is non-dict, nested paths are considered removed.
    - If exact path present in delta:
        - If value is None and delete_nulls True -> treated as removed (new_found=False)
        - If value is dict and data has a dict at same path -> deep-merge and return merged dict
        - Otherwise return delta's value
    - Else fall back to data
    """
    delta = delta or {}
    data = data or {}

    # Ancestor checks (unchanged): if any ancestor in delta is non-dict -> nested paths removed.
    if path:
        parts = path.split(".")
        for i in range(1, len(parts)):
            ancestor = ".".join(parts[:i])
            anc_val, anc_found = _deep_get(delta, ancestor)
            if anc_found:
                if anc_val is None and delete_nulls:
                    return None, False
                if not isinstance(anc_val, dict):
                    return None, False
                # if ancestor is a dict in delta, nested keys may still exist; continue

    # Exact path present in delta?
    val, found_in_delta = _deep_get(delta, path)
    if found_in_delta:
        # deletion by None
        if val is None and delete_nulls:
            return None, False

        # If both data and delta at this path are dicts -> do a deep merge
        data_val, found_in_data = _deep_get(data, path)
        if isinstance(val, dict) and found_in_data and isinstance(data_val, dict):
            merged = deep_merge(data_val, val, delete_nulls)
            return merged, True

        # otherwise delta replaces
        return val, True

    # fallback to data
    val, found_in_data = _deep_get(data, path)
    if found_in_data:
        return val, True

    return None, False


def _collect_paths(obj: Optional[Dict[str, Any]], prefix: str = "") -> Set[str]:
    """
    Collect dot-paths for every key in obj.
    - Includes intermediate dict keys and nested/leaf keys.
    - Treats non-dict values (including lists, None) as leaves.
    """
    paths: Set[str] = set()
    if not isinstance(obj, dict) or obj is None:
        return paths

    for k, v in obj.items():
        path = f"{prefix}.{k}" if prefix else k
        paths.add(path)
        if isinstance(v, dict) and v is not None:
            paths.update(_collect_paths(v, path))
    return paths


def detect_field_changes(
    data: Optional[Dict[str, Any]],
    delta: Optional[Dict[str, Any]],
    fields: Optional[Iterable[str]] = None,
    delete_nulls: bool = True,
) -> Dict[str, Dict[str, Any]]:
    """
    For each dot-path in `fields` (or for all discovered paths when fields is None) returns:
      {
        "old": <old_value_or_None>,
        "old_found": True/False,
        "new": <new_value_or_None>,
        "new_found": True/False,
        "changed": True/False,
        "reason": "deleted"|"updated"|"added"|"unchanged"
      }

    Note: when new_found is False it means the field will be absent after merge (deleted).
    """
    data = data or {}
    delta = delta or {}

    if fields is None:
        paths_from_data = _collect_paths(data)
        paths_from_delta = _collect_paths(delta)
        fields_list = sorted(paths_from_data.union(paths_from_delta))
    else:
        fields_list = list(fields)

    out: Dict[str, Dict[str, Any]] = {}

    for path in fields_list:
        old_val, old_found = _deep_get(data, path)
        new_val, new_found = _compute_new_value_from_delta_or_data(data, delta, path, delete_nulls=delete_nulls)

        # Determine changed/ reason
        if not old_found and not new_found:
            changed = False
            reason = "unchanged"
        elif not old_found and new_found:
            changed = True
            reason = "added"
        elif old_found and not new_found:
            changed = True
            reason = "deleted"
        else:
            changed = old_val != new_val
            reason = "updated" if changed else "unchanged"

        out[path] = {
            "old": old_val,
            "old_found": old_found,
            "new": None if not new_found else new_val,
            "new_found": new_found,
            "changed": changed,
            "reason": reason,
        }

    return out


def safe_any_changed(changes: Dict[str, Dict[str, Any]]) -> bool:
    """
    Compute any_changed robustly by only checking dict entries that look like field entries.
    """
    return any(
        isinstance(info, dict) and info.get("changed", False)
        for info in changes.values()
    )


def prune_conflicting_set_unset(set_map: Dict[str, Any], unset_map: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Remove keys from set_map and unset_map that conflict with parent keys.
    Parents win: if 'record.test' exists, drop 'record.test.*' entries from both maps.
    Also remove keys that appear in both maps (prefer $set).
    """
    # normalize keys lists
    set_keys = sorted(set_map.keys(), key=lambda k: (k.count("."), k))
    unset_keys = sorted(unset_map.keys(), key=lambda k: (k.count("."), k))

    # Build a set of parent keys present (both set and unset)
    parent_keys = set()
    for k in set_keys + unset_keys:
        # check if any ancestor of k is present in set_map or unset_map
        parts = k.split(".")
        for i in range(1, len(parts)):
            ancestor = ".".join(parts[:i])
            if ancestor in set_map or ancestor in unset_map:
                parent_keys.add(ancestor)

    # If some parent keys exist, drop any deeper keys under them
    def drop_children(map_obj: Dict[str, Any]) -> Dict[str, Any]:
        kept = {}
        for k, v in map_obj.items():
            # if any ancestor is present in original maps, drop this key
            parts = k.split(".")
            ancestor_found = False
            for i in range(1, len(parts)):
                ancestor = ".".join(parts[:i])
                if ancestor in set_map or ancestor in unset_map:
                    ancestor_found = True
                    break
            if not ancestor_found:
                kept[k] = v
        return kept

    pruned_set = drop_children(set_map)
    pruned_unset = drop_children(unset_map)

    # Remove keys present in both - prefer $set (so drop from unset)
    for k in list(pruned_unset.keys()):
        if k in pruned_set:
            pruned_unset.pop(k, None)

    return pruned_set, pruned_unset
