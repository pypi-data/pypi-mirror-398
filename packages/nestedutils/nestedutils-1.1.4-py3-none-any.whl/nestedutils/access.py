from typing import Any, List, Literal, Union
from .exceptions import PathError
from .enums import PathErrorCode, FillStrategy
from .helpers import normalize_path, navigate, create_container, fill_list_gaps, ensure_container_at_index
from .helpers import is_int_key, resolve_write_index


def get_at(data: Any, path: Union[str, List[Any]], default: Any = None) -> Any:
    """Retrieve a value from a nested data structure.
    
    Navigates through nested dictionaries, lists, and tuples using a path specified as either
    a dot-notation string or a list of keys/indices. Returns ``default`` if the path does not
    exist or an index is out of bounds (positive or negative). Supports negative indexing for
    lists and tuples.
    
    Args:
        data: The data structure to navigate (dict, list, tuple, or nested combinations).
        path: Path to the value. Accepts either a dot-separated string (e.g., "a.b.0.name") or
            a list of keys/indices (e.g., ["a", "b", 0, "name"]). Indices may be integers or
            strings representing integers (including negative indices).
        default: Value to return if the path does not exist (default: None).
    
    Returns:
        The value at the specified path, or ``default`` if the path does not exist.
    
    Raises:
        PathError: If the path is malformed, empty, or contains empty keys.
    
    Examples:
        >>> data = {"a": {"b": {"c": 5}}}
        >>> get_at(data, "a.b.c")
        5
        
        >>> get_at(data, "a.b.d", default=99)
        99
        
        >>> data = {"items": [{"name": "apple"}, {"name": "banana"}]}
        >>> get_at(data, "items.1.name")
        'banana'
        
        >>> get_at(data, "items.-1.name")
        'banana'
        
        >>> get_at(data, "items.-5.name", default="not found")
        'not found'
        
        >>> data = (10, 20, 30)
        >>> get_at(data, "-1")
        30
    """
    keys = normalize_path(path)
    current = data
    MISSING = object()
    
    for key in keys:
        current = navigate(current, key, MISSING)
        if current is MISSING:
            return default
    
    return current


def exists_at(data: Any, path: Union[str, List[Any]]) -> bool:
    """Check if a path exists in a nested data structure.
    
    Navigates through nested dictionaries, lists, and tuples. Returns True if the full path
    exists, False otherwise (including for any out-of-bounds index, positive or negative).
    Supports negative indexing for lists and tuples.
    
    Args:
        data: The data structure to navigate (dict, list, tuple, or nested combinations).
        path: Path to check. Accepts either a dot-separated string (e.g., "a.b.0.name") or a
            list of keys/indices (e.g., ["a", "b", 0, "name"]).
    
    Returns:
        True if the path exists, False otherwise.
    
    Raises:
        PathError: If the path is malformed, empty, or contains empty keys.
    
    Examples:
        >>> data = {"a": {"b": {"c": 5}}}
        >>> exists_at(data, "a.b.c")
        True
        
        >>> exists_at(data, "a.b.d")
        False
        
        >>> data = {"items": [{"name": "apple"}, {"name": "banana"}]}
        >>> exists_at(data, "items.1.name")
        True
        
        >>> exists_at(data, "items.-1.name")
        True
        
        >>> exists_at(data, "items.-5.name")
        False
        
        >>> exists_at(data, "items.10.name")
        False
        
        >>> data = (10, 20, 30)
        >>> exists_at(data, "2")
        True
        
        >>> exists_at(data, "5")
        False
    """
    keys = normalize_path(path)
    current = data
    MISSING = object()
    
    for key in keys:
        current = navigate(current, key, MISSING)
        if current is MISSING:
            return False
    
    return True


def set_at(
    data: Any,
    path: Union[str, List[Any]],
    value: Any,
    fill_strategy: Literal["auto", "none", "dict", "list"] = "auto"
) -> None:
    """Set a value in a nested data structure, creating intermediate containers as needed.
    
    Navigates to the specified path and sets the value, automatically creating missing
    intermediate dictionaries or lists according to ``fill_strategy``.
    
    List indexing rules:
        - Non-negative indices can extend the list, filling gaps as needed.
        - Negative indices can only modify existing elements (no extension allowed).
        - Out-of-bounds negative indices raise PathError.
    
    Args:
        data: The mutable data structure to modify (dict or list). Intermediate containers are
            created automatically, but the root must be mutable.
        path: Path where to set the value. Accepts either a dot-separated string (e.g., "a.b.0.name")
            or a list of keys/indices (e.g., ["a", "b", 0, "name"]).
        value: The value to set at the specified path.
        fill_strategy: Controls how missing intermediate containers are created. Must be one of:
            - 'auto' (default): creates {} for dict keys, [] for list indices, and None for sparse
              list gaps.
            - 'none': fills sparse list gaps with None.
            - 'dict': always creates dictionaries {} for missing containers.
            - 'list': always creates lists [] for missing containers.
    
    Returns:
        None. The function modifies ``data`` in place.
    
    Raises:
        PathError: If the path is malformed, empty, attempts to modify a tuple, uses an invalid
            fill_strategy, or uses an out-of-bounds negative index.
    
    Note:
        When extending lists with gaps (e.g., setting index 5 on a list of length 2),
        intermediate positions are filled based on ``fill_strategy`` ('auto' and 'none' use None;
        'dict' uses {}; 'list' uses []).
    
    Examples:
        >>> data = {}
        >>> set_at(data, "user.profile.name", "Alice")
        >>> data
        {'user': {'profile': {'name': 'Alice'}}}
        
        >>> data = {}
        >>> set_at(data, "items.0.name", "Item 1")
        >>> data
        {'items': [{'name': 'Item 1'}]}
        
        >>> data = {}
        >>> set_at(data, "items.5", "last", fill_strategy="none")
        >>> data
        {'items': [None, None, None, None, None, 'last']}
        
        >>> data = {}
        >>> set_at(data, "items.2.sub.value", 42)  # 'auto' creates dict at target index, None for gaps
        >>> data
        {'items': [None, None, {'sub': {'value': 42}}]}
        
        >>> data = [1, 2, 3]
        >>> set_at(data, "5", 99)  # extends with None gaps
        >>> data
        [1, 2, 3, None, None, 99]
        
        >>> set_at(data, "-1", 100)  # modifies existing last element
        >>> data
        [1, 2, 3, None, None, 100]
    """
    try:
        strategy = FillStrategy(fill_strategy)
    except ValueError:
        valid = {s.value for s in FillStrategy}
        raise PathError(
            f"Invalid fill_strategy: {fill_strategy}. Valid: {valid}",
            PathErrorCode.INVALID_FILL_STRATEGY
        )
    
    keys = normalize_path(path)
    current = data
    
    # Navigate intermediate keys
    for i, key in enumerate(keys[:-1]):
        next_key = keys[i + 1]
        
        if isinstance(current, dict):
            if key not in current or current[key] is None:
                current[key] = create_container(strategy, next_key)
            current = current[key]
        
        elif isinstance(current, list):
            if not is_int_key(key):
                raise PathError(
                    f"Expected numeric index, got '{key}'",
                    PathErrorCode.INVALID_INDEX
                )
            
            idx = resolve_write_index(current, key, allow_extension=True)
            fill_list_gaps(current, idx, strategy)
            ensure_container_at_index(current, idx, strategy, next_key)
            current = current[idx]
        
        elif isinstance(current, tuple):
            raise PathError(
                "Cannot modify tuple (immutable)",
                PathErrorCode.IMMUTABLE_CONTAINER
            )
        
        else:
            raise PathError(
                f"Cannot navigate into {type(current).__name__}",
                PathErrorCode.INVALID_PATH
            )
    
    # Set final value
    final_key = keys[-1]
    
    if isinstance(current, dict):
        current[final_key] = value
    
    elif isinstance(current, list):
        if not is_int_key(final_key):
            raise PathError(
                f"Expected numeric index, got '{final_key}'",
                PathErrorCode.INVALID_INDEX
            )
        
        idx = resolve_write_index(current, final_key, allow_extension=True)
        
        while len(current) <= idx:
            current.append(None)
        
        current[idx] = value
    
    elif isinstance(current, tuple):
        raise PathError(
            "Cannot modify tuple (immutable)",
            PathErrorCode.IMMUTABLE_CONTAINER
        )
    
    else:
        raise PathError(
            f"Cannot set value in {type(current).__name__}",
            PathErrorCode.INVALID_PATH
        )


def delete_at(
    data: Any,
    path: Union[str, List[Any]],
    *,
    allow_list_mutation: bool = False
) -> Any:
    """Delete a value from a nested data structure and return it.
    
    Removes the item at the specified path. For dictionaries, the key-value pair is removed.
    For lists, deletion is disabled by default to prevent accidental index shifting that could
    break subsequent code.
    
    Args:
        data: The mutable data structure to modify (dict or list).
        path: Path to the value to delete. Accepts either a dot-separated string (e.g., "a.b.0")
            or a list of keys/indices (e.g., ["a", "b", 0]).
        allow_list_mutation: If True, allows deletion from lists using ``list.pop()``. Defaults
            to False to prevent unintended side effects.
    
    Returns:
        The deleted value.
    
    Raises:
        PathError: If the path does not exist, is malformed, attempts deletion from a tuple,
            attempts list deletion without ``allow_list_mutation=True``, or uses an out-of-bounds
            index.
    
    Examples:
        >>> data = {"a": {"b": 1, "c": 2}}
        >>> delete_at(data, "a.b")
        1
        >>> data
        {'a': {'c': 2}}
        
        >>> data = {"items": [1, 2, 3]}
        >>> delete_at(data, "items.1", allow_list_mutation=True)
        2
        >>> data
        {'items': [1, 3]}
        
        >>> delete_at(data, "items.-1", allow_list_mutation=True)
        3
        >>> data
        {'items': [1]}
        
        >>> delete_at(data, "items.0")  # without allow_list_mutation=True
        Traceback (most recent call last):
        ...
        PathError: List deletion disabled. Set allow_list_mutation=True
    """
    keys = normalize_path(path)
    current = data
    
    # Navigate to parent
    for key in keys[:-1]:
        if isinstance(current, dict):
            if key not in current:
                raise PathError(
                    f"Key not found: '{key}'",
                    PathErrorCode.MISSING_KEY
                )
            current = current[key]
        
        elif isinstance(current, (list, tuple)):
            if not is_int_key(key):
                raise PathError(
                    f"Expected numeric index, got '{key}'",
                    PathErrorCode.INVALID_INDEX
                )
            
            idx = resolve_write_index(current, key, allow_extension=False)
            current = current[idx]
        
        else:
            raise PathError(
                f"Cannot navigate through {type(current).__name__}",
                PathErrorCode.INVALID_PATH
            )
    
    # Delete final key
    final_key = keys[-1]
    
    if isinstance(current, dict):
        if final_key not in current:
            raise PathError(
                f"Key not found: '{final_key}'",
                PathErrorCode.MISSING_KEY
            )
        return current.pop(final_key)
    
    elif isinstance(current, list):
        if not allow_list_mutation:
            raise PathError(
                "List deletion disabled. Set allow_list_mutation=True",
                PathErrorCode.INVALID_PATH
            )
        
        if not is_int_key(final_key):
            raise PathError(
                f"Expected numeric index, got '{final_key}'",
                PathErrorCode.INVALID_INDEX
            )
        
        idx = resolve_write_index(current, final_key, allow_extension=False)
        return current.pop(idx)
    
    elif isinstance(current, tuple):
        raise PathError(
            "Cannot delete from tuple (immutable)",
            PathErrorCode.IMMUTABLE_CONTAINER
        )
    
    else:
        raise PathError(
            f"Cannot delete from {type(current).__name__}",
            PathErrorCode.INVALID_PATH
        )