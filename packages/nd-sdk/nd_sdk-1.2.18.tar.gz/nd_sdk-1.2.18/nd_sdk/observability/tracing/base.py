"""
Base Trace Processor - Abstract interface for all trace providers
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from enum import Enum


class SpanKind(Enum):
    """Standard span kinds for distributed tracing"""
    INTERNAL = "INTERNAL"
    SERVER = "SERVER"
    CLIENT = "CLIENT"
    PRODUCER = "PRODUCER"
    CONSUMER = "CONSUMER"


class SpanStatus(Enum):
    """Standard span status codes"""
    UNSET = "UNSET"
    OK = "OK"
    ERROR = "ERROR"


class BaseTraceProcessor(ABC):
    """
    Abstract base class for trace processors.
    All trace providers must implement these methods.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the trace processor and any required resources.
        This method should be called before any tracing operations.
        """
        pass

    @abstractmethod
    def create_span(
            self,
            name: str,
            kind: str = "INTERNAL",
            attributes: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Create and start a new span.

        Args:
            name: Name of the span
            kind: Span kind as string (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
            attributes: Optional attributes to attach to the span

        Returns:
            Provider-specific span object
        """
        pass

    @abstractmethod
    def finish_span(
            self,
            span: Any,
            status: str = "OK",
            exception: Optional[Exception] = None
    ) -> None:
        """
        End a span and export it.

        Args:
            span: The span object to end
            status: Span status as string (OK, ERROR, UNSET)
            exception: Optional exception that occurred
        """
        pass

    @abstractmethod
    def add_event(
            self,
            span: Any,
            event_name: str,
            attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add an event to an active span.

        Args:
            span: The span to add the event to
            event_name: Name of the event
            attributes: Optional event attributes
        """
        pass

    @abstractmethod
    def set_attribute(
            self,
            span: Any,
            key: str,
            value: Any
    ) -> None:
        """
        Set an attribute on an active span.

        Args:
            span: The span to set the attribute on
            key: Attribute key
            value: Attribute value
        """
        pass

    @abstractmethod
    def record_error(
            self,
            span: Any,
            exception: Exception
    ) -> None:
        """
        Record an exception on a span without ending it.

        Args:
            span: The span to record the error on
            exception: The exception to record
        """
        pass

    @abstractmethod
    def get_current_span(self) -> Optional[Any]:
        """
        Get the currently active span.

        Returns:
            Current span object or None
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """
        Shutdown the trace processor and cleanup resources.
        """
        pass
