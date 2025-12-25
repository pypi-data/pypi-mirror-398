import json
from ...observability.factory import get_logger
from ...caching.factory import get_cache
from functools import wraps
import traceback
from .base_exceptions import *

# ============================================================================
# Exception Handler Class
# ============================================================================


class IDPExceptionHandler(BaseException):
    """
    Centralized exception handler for IDP framework.
    Manages error catalog, exception mapping, and logging.
    """

    # Map category names to exception classes
    CATEGORY_MAP = {
        "StorageException": StorageException,
        "FileSystemException": FileSystemException,
        "PermissionException": PermissionException,
        "NetworkException": NetworkException,
        "TimeoutException": TimeoutException,
        "DataParsingException": DataParsingException,
        "ProcessingException": ProcessingException,
        "MathOperationException": MathOperationException,
        "InitializationException": InitializationException,
        "ConcurrencyException": ConcurrencyException,
        "DataValidationException": DataValidationException,
        "ResourceException": ResourceException,
        "HandledExceptionWarning": HandledExceptionWarning
    }

    # Map Python built-in exceptions to IDP error types
    BUILTIN_EXCEPTION_MAP = {
        FileNotFoundError: ("FileSystemException", "File_Not_Found"),
        PermissionError: ("PermissionException", "Operation_Not_Permitted"),
        TimeoutError: ("TimeoutException", "Operation_Timeout"),
        json.JSONDecodeError: ("DataParsingException", "JSON_Decode_Error"),
        UnicodeDecodeError: ("DataParsingException", "Unicode_Decode_Error"),
        UnicodeEncodeError: ("DataParsingException", "Unicode_Encode_Error"),
        ValueError: ("ProcessingException", "Invalid_Value"),
        TypeError: ("ProcessingException", "Type_Mismatch"),
        KeyError: ("ProcessingException", "Key_Not_Found"),
        IndexError: ("ProcessingException", "Index_Out_Of_Range"),
        AttributeError: ("ProcessingException", "Attribute_Access_Failed"),
        MemoryError: ("ProcessingException", "Memory_Error"),
        OverflowError: ("MathOperationException", "Numerical_Overflow"),
        RuntimeError: ("ProcessingException", "Runtime_Error"),
        RecursionError: ("ProcessingException", "Recursion_Error"),
        StopIteration: ("ProcessingException", "Iterator_Exhausted"),
        AssertionError: ("ProcessingException", "Assertion_Failed"),
        ImportError: ("ProcessingException", "Import_Failed"),
        ModuleNotFoundError: ("ProcessingException", "Module_Not_Found"),
        NotImplementedError: ("ProcessingException", "Feature_Not_Implemented"),
        SystemError: ("ProcessingException", "System_Error"),
        BufferError: ("ProcessingException", "Buffer_Error"),
        EOFError: ("ProcessingException", "End_Of_File"),
        LookupError: ("ProcessingException", "Lookup_Error"),
        KeyboardInterrupt: ("ProcessingException", "User_Interrupted"),
        SystemExit: ("ProcessingException", "System_Exit"),
        GeneratorExit: ("ProcessingException", "Generator_Exit"),
        ReferenceError: ("ProcessingException", "Reference_Error"),
        ZeroDivisionError: ("MathOperationException", "Division_By_Zero"),
        FloatingPointError: ("MathOperationException", "Floating_Point_Error"),
        ArithmeticError: ("MathOperationException", "Arithmetic_Error"),
        OSError: ("ResourceException", "OS_Error"),
        IOError: ("ResourceException", "IO_Error"),
    }

    def __init__(self):
        """
        Initialize the exception handler.

        Args:
            error_catalog: Dictionary containing error definitions
        """
        cache = get_cache.get()
        self.logger = get_logger.get()
        error_catalog = cache.get("NDSDK:cassandra:configuration:exception-catalog")
        if error_catalog:
            self.logger.info(f"IDPExceptionHandler initialized with error catalog.")
        self.error_catalog = error_catalog.get("ErrorCatalog", error_catalog)


    def get_error_info(self, category: str, error_type: str) -> Dict[str, str]:
        """
        Get error information from catalog.

        Args:
            category: Error category (e.g., "StorageException")
            error_type: Error type (e.g., "S3_Upload_Failed")

        Returns:
            Dictionary with Code and Message
        """
        try:
            return self.error_catalog[category][error_type]
        except KeyError:
            return {
                "Code": "IDP-E999",
                "Message": f"Unknown error: {category}.{error_type}"
            }

    def raise_error(self, category: str, error_type: str, context: Optional[Dict[str, Any]] = None):
        """
        Raise an IDP exception with info logging.

        Args:
            category: Error category
            error_type: Specific error type
            context: Optional context information
        """
        self.logger.error(traceback.format_exc())
        error_info = self.get_error_info(category, error_type)

        exception_class = self.CATEGORY_MAP.get(category, BaseException)

        # Format message with context if available
        message = error_info["Message"]
        if context:
            try:
                message = message.format(**context)
            except KeyError:
                pass  # Use original message if formatting fails

        exc = exception_class(
            code=error_info["Code"],
            message=message,
            context=context.update({"traceback": traceback.format_exc()}) if context else {"traceback": traceback.format_exc()},
        )

        # Log as info before raising
        error_message = {
            "error_code": exc.code,
            "message": exc.message,
            "context": exc.context
        }
        self.logger.error(error_message)

        raise exc

    def warn_error(self, category: str, error_type: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Log an IDP error as warning without raising exception.

        Args:
            category: Error category
            error_type: Specific error type
            context: Optional context information

        Returns:
            Dictionary containing error information
        """
        self.logger.error(traceback.format_exc())
        error_info = self.get_error_info(category, error_type)

        # Format message with context if available
        message = error_info["Message"]
        if context:
            try:
                message = message.format(**context)
            except KeyError:
                pass  # Use original message if formatting fails

        # Log as warning
        error_message = {
            "error_code": error_info["Code"],
            "message": message or "",
            "context": context or {}
        }
        self.logger.warning(error_message)


    def wrap_exception(self, original_exception: Exception,
                       context: Optional[Dict[str, Any]] = None) -> BaseException:
        """
        Wrap a Python built-in exception into an IDP exception.

        Args:
            original_exception: Original Python exception
            context: Optional context information

        Returns:
            BaseException instance
        """
        exc_type = type(original_exception)

        # Check if we have a mapping for this exception type
        if exc_type in self.BUILTIN_EXCEPTION_MAP:
            category, error_type = self.BUILTIN_EXCEPTION_MAP[exc_type]
            error_info = self.get_error_info(category, error_type)
            exception_class = self.CATEGORY_MAP.get(category, BaseException)
        else:
            # Default to ProcessingException for unmapped exceptions
            error_info = {
                "Code": "IDP-E023",
                "Message": f"An unexpected error occurred in the processing service: {str(original_exception)}"
            }
            exception_class = ProcessingException

        # Add original exception details to context
        if context is None:
            context = {}
        context.update({
            "original_exception": str(original_exception),
            "exception_type": exc_type.__name__,
            "traceback": traceback.format_exc()
        })

        return exception_class(
            code=error_info["Code"],
            message=error_info["Message"],
            context=context
        )

    def _log_exception(self, exception: BaseException):
        """Log exception details"""
        extra = {
            "error_code": exception.code,
            "context": exception.context
        }

        if exception.code.startswith("IDP-W"):
            self.logger.warning(exception.message)
        else:
            self.logger.error(exception.message)

    def handle_exception(self, func):
        """
        Decorator to automatically handle exceptions in functions.

        Usage:
            @handler.handle_exception
            def my_function():
                # your code
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseException:
                # Re-raise IDP exceptions as-is
                raise
            except Exception as e:
                # Wrap other exceptions
                wrapped_exc = self.wrap_exception(e)
                self._log_exception(wrapped_exc)
                raise wrapped_exc

        return wrapper

    def exception_context(self, category: str, error_type: str):
        """
        Context manager for exception handling.

        Usage:
            with handler.exception_context("StorageException", "S3_Upload_Failed"):
                # your code
        """
        return ExceptionContext(self, category, error_type)


# ============================================================================
# Context Manager for Exception Handling
# ============================================================================

class ExceptionContext:
    """Context manager for scoped exception handling"""

    def __init__(self, handler: IDPExceptionHandler, category: str, error_type: str):
        self.handler = handler
        self.category = category
        self.error_type = error_type

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return True

        if isinstance(exc_val, BaseException):
            # Already an IDP exception, just log and re-raise
            self.handler._log_exception(exc_val)
            return False

        # Wrap the exception
        wrapped_exc = self.handler.wrap_exception(exc_val)
        self.handler._log_exception(wrapped_exc)
        raise wrapped_exc from exc_val

