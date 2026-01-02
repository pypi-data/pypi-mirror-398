"""Enumerations for nestedutils library.

This module defines error codes and configuration enums used throughout
the nestedutils library for consistent error handling and behavior control.
"""

from enum import Enum


class PathErrorCode(Enum):
    """Error codes for path-related exceptions.
    
    Example:
        ```python
        from nestedutils import get_at, PathError, PathErrorCode
        
        data = {"a": {"b": 1}}
        try:
            get_at(data, "a.c.d")
        except PathError as e:
            if e.code == PathErrorCode.MISSING_KEY:
                print("Key not found")
        ```
    """
    INVALID_INDEX = "INVALID_INDEX"
    MISSING_KEY = "MISSING_KEY"
    EMPTY_PATH = "EMPTY_PATH"
    IMMUTABLE_CONTAINER = "IMMUTABLE_CONTAINER"
    INVALID_PATH = "INVALID_PATH"
    INVALID_FILL_STRATEGY = "INVALID_FILL_STRATEGY"


class FillStrategy(Enum):
    """Strategy for filling missing containers when setting nested paths.
    
    Example:
        ```python
        from nestedutils import set_at, FillStrategy
        
        data = {}
        set_at(data, "items.0.name", "apple", fill_strategy=FillStrategy.AUTO)
        ```
    """
    AUTO = "auto"
    NONE = "none"
    DICT = "dict"
    LIST = "list"