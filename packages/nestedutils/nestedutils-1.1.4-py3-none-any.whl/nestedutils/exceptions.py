from typing import Optional
from .enums import PathErrorCode

class PathError(Exception):
    """Raised when a nested path cannot be navigated or modified."""
    
    def __init__(self, message: str, code: Optional[PathErrorCode] = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
