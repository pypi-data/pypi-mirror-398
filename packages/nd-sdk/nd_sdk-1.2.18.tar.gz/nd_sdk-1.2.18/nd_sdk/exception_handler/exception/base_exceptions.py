import json
from typing import Dict, Any, Optional


# ============================================================================
# Base Exception Classes
# ============================================================================

class BaseException(Exception):
    """Base exception class for all exceptions"""

    def __init__(self, code: str, message: str, context: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.context = context or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/API responses"""
        return {
            "error_code": self.code,
            "error_message": self.message,
            "error_type": self.__class__.__name__,
            "context": self.context
        }

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class StorageException(BaseException):
    """Storage-related exceptions"""
    pass


class FileSystemException(BaseException):
    """File system exceptions"""
    pass


class PermissionException(BaseException):
    """Permission-related exceptions"""
    pass


class NetworkException(BaseException):
    """Network-related exceptions"""
    pass


class TimeoutException(BaseException):
    """Timeout exceptions"""
    pass


class DataParsingException(BaseException):
    """Data parsing exceptions"""
    pass


class ProcessingException(BaseException):
    """Processing exceptions"""
    pass


class MathOperationException(BaseException):
    """Mathematical operation exceptions"""
    pass


class InitializationException(BaseException):
    """Initialization exceptions"""
    pass


class ConcurrencyException(BaseException):
    """Concurrency-related exceptions"""
    pass


class DataValidationException(BaseException):
    """Data validation exceptions"""
    pass


class ResourceException(BaseException):
    """Resource-related exceptions"""
    pass


class HandledExceptionWarning(BaseException):
    """Warning for handled exceptions"""
    pass

