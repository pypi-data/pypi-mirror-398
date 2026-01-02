from typing import Any, List, Union, Optional
from .exceptions import PathError
from .enums import PathErrorCode, FillStrategy
from .constants import MAX_DEPTH, MAX_LIST_SIZE


def normalize_path(path: Union[str, List[Any]]) -> List[str]:
    """Normalize path to list of strings and validate.
    
    Converts path to a list of string keys, validating that:
    - Path is not empty
    - No keys in the path are empty strings
    - Path depth does not exceed MAX_DEPTH
    
    Args:
        path: Either a dot-notation string (e.g., "a.b.c") or a list of keys.
    
    Returns:
        List of string keys representing the path.
    
    Raises:
        PathError: If path format is invalid, path is empty, contains empty keys,
            or exceeds maximum depth.
    """
    if isinstance(path, list):
        keys = [str(x) for x in path]
    elif isinstance(path, str):
        keys = path.split(".")
    else:
        raise PathError(
            f"Path must be string or list, got {type(path).__name__}", 
            PathErrorCode.INVALID_PATH
        )
    
    if not keys:
        raise PathError("Path cannot be empty", PathErrorCode.EMPTY_PATH)
    
    if len(keys) > MAX_DEPTH:
        raise PathError(
            f"Path depth exceeds maximum of {MAX_DEPTH}",
            PathErrorCode.INVALID_PATH
        )
    
    if any(key == "" for key in keys):
        raise PathError("Path cannot contain empty keys", PathErrorCode.EMPTY_PATH)
    
    return keys


def is_int_key(key: str) -> bool:
    """Check if a key represents a valid integer index.
    
    Args:
        key: String to check.
    
    Returns:
        True if key can be parsed as an integer, False otherwise.
    
    Examples:
        >>> is_int_key("0")
        True
        >>> is_int_key("-1")
        True
        >>> is_int_key("abc")
        False
        >>> is_int_key("-")
        False
    """
    try:
        int(key)
        return True
    except ValueError:
        return False


def parse_int_key(key: str) -> int:
    """Parse a string key into an integer index.
    
    Args:
        key: String representation of an index.
    
    Returns:
        Parsed integer index.
    
    Raises:
        PathError: If key cannot be parsed as an integer.
    """
    try:
        return int(key)
    except ValueError:
        raise PathError(f"Invalid list index: '{key}'", PathErrorCode.INVALID_INDEX)


def resolve_read_index(container: Union[list, tuple], key: str) -> Optional[int]:
    """Resolve index for read operations (get_at, exists_at).
    
    Read operations are graceful - out-of-bounds indices return None
    to signal "not found" rather than raising errors.
    
    Args:
        container: The list or tuple to index into.
        key: String representation of the index.
    
    Returns:
        Resolved positive index, or None if out of bounds.
    
    Raises:
        PathError: If the key is not a valid integer.
    """
    idx = parse_int_key(key)
    
    if idx < 0:
        idx = len(container) + idx
    
    if 0 <= idx < len(container):
        return idx
    
    return None


def resolve_write_index(container: list, key: str, allow_extension: bool = True) -> int:
    """Resolve index for write operations (set_at).
    
    Write operations have stricter semantics:
    - Negative indices must reference existing elements (no extension)
    - Positive indices can extend the list if allow_extension=True
    - Positive indices cannot exceed MAX_LIST_SIZE to prevent memory exhaustion
    
    Args:
        container: The list to index into.
        key: String representation of the index.
        allow_extension: If True, positive indices can exceed current list length.
                        If False, all indices must reference existing elements.
    
    Returns:
        Resolved positive index.
    
    Raises:
        PathError: If index is out of bounds, exceeds MAX_LIST_SIZE, or key cannot be parsed as integer.
    """
    idx = parse_int_key(key)
    length = len(container)
    
    if idx < 0:
        resolved = length + idx
        if resolved < 0 or resolved >= length:
            raise PathError(
                f"Index {key} out of bounds for list of length {length}",
                PathErrorCode.INVALID_INDEX
            )
        return resolved
    
    # Check maximum list size when extension is allowed
    if allow_extension and idx > MAX_LIST_SIZE:
        raise PathError(
            f"List index {idx} exceeds maximum size {MAX_LIST_SIZE}",
            PathErrorCode.INVALID_INDEX
        )
    
    if not allow_extension and idx >= length:
        raise PathError(
            f"Index {key} out of bounds for list of length {length}",
            PathErrorCode.INVALID_INDEX
        )
    
    return idx


def navigate(container: Any, key: str, default: Any) -> Any:
    """Navigate one level into a container.
    
    Used by read operations (get_at, exists_at). Returns default
    for any navigation failures rather than raising exceptions.
    
    Args:
        container: Container to navigate into (dict, list, or tuple).
        key: Key or index to access.
        default: Sentinel value to return on failure.
    
    Returns:
        The value at the key, or default if navigation fails.
    """
    if isinstance(container, dict):
        return container.get(key, default)
    
    if isinstance(container, (list, tuple)):
        if not is_int_key(key):
            return default
        
        idx = resolve_read_index(container, key)
        if idx is None:
            return default
        
        return container[idx]
    
    return default


def create_container(strategy: FillStrategy, next_key: str) -> Union[dict, list]:
    """Create a new container based on fill strategy and next key.
    
    Args:
        strategy: The fill strategy to use.
        next_key: The next key in the path (used for "auto" strategy).
    
    Returns:
        A new dict or list.
    """
    if strategy == FillStrategy.DICT:
        return {}
    elif strategy == FillStrategy.LIST:
        return []
    else:  # auto or none
        return [] if is_int_key(next_key) else {}


def fill_list_gaps(target: list, up_to_index: int, strategy: FillStrategy) -> None:
    """Fill gaps in a list up to (but not including) target index.
    
    Args:
        target: The list to extend.
        up_to_index: The target index to reach.
        strategy: How to fill the gaps (None for auto/none, dict/list for others).
    """
    while len(target) < up_to_index:
        if strategy == FillStrategy.DICT:
            target.append({})
        elif strategy == FillStrategy.LIST:
            target.append([])
        else:  # auto or none
            target.append(None)


def ensure_container_at_index(
    target: list, 
    index: int, 
    strategy: FillStrategy, 
    next_key: str
) -> None:
    """Ensure there's a navigable container at the given index.
    
    Creates a new container if index doesn't exist or contains None.
    
    Args:
        target: The list to modify.
        index: The index to ensure a container at.
        strategy: How to create containers.
        next_key: The next key in the path (for "auto" strategy).
    """
    if len(target) == index:
        target.append(create_container(strategy, next_key))
    elif target[index] is None:
        target[index] = create_container(strategy, next_key)