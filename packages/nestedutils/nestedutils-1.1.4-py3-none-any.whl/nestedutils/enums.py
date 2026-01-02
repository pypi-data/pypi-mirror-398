from enum import Enum

class PathErrorCode(Enum):
    """Error codes for path-related exceptions."""
    INVALID_INDEX = "INVALID_INDEX"
    MISSING_KEY = "MISSING_KEY"
    EMPTY_PATH = "EMPTY_PATH"
    IMMUTABLE_CONTAINER = "IMMUTABLE_CONTAINER"
    INVALID_PATH = "INVALID_PATH"
    INVALID_FILL_STRATEGY = "INVALID_FILL_STRATEGY"


class FillStrategy(Enum):
    """Strategy for filling missing containers when setting nested paths."""
    AUTO = "auto"
    NONE = "none"
    DICT = "dict"
    LIST = "list"