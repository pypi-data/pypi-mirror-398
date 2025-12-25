import contextvars
import uuid
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from opentelemetry import trace
from opentelemetry.trace import NonRecordingSpan
from opentelemetry.propagate import inject, extract
from opentelemetry.context import attach, detach


_trace_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('trace_id', default=None)
_span_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('span_id', default=None)
_correlation_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('correlation_id', default=None)



class ObservabilityContext:
    """
    Context manager for observability data (trace_id, span_id, correlation_id).
    Provides both OpenTelemetry integration and manual context management.
    Auto-generates IDs if not present.
    """

    def __init__(self, trace_id: Optional[str] = None,
                 span_id: Optional[str] = None,
                 correlation_id: Optional[str] = None):
        """Initialize context with optional manual values."""
        self._trace_id = trace_id
        self._span_id = span_id
        self._correlation_id = correlation_id
        self._tokens = []

    @staticmethod
    def _generate_trace_id() -> str:
        """Generate a new trace ID in OpenTelemetry format (32 hex chars)."""
        return uuid.uuid4().hex + uuid.uuid4().hex[:16]

    @staticmethod
    def _generate_span_id() -> str:
        """Generate a new span ID in OpenTelemetry format (16 hex chars)."""
        return uuid.uuid4().hex[:16]

    @staticmethod
    def _generate_correlation_id() -> str:
        """Generate a new correlation ID."""
        return str(uuid.uuid4())

    @staticmethod
    def get_trace_id() -> Optional[str]:
        """Get trace_id from context variables or OpenTelemetry span."""
        # First check manual context
        manual_trace_id = _trace_id_var.get()
        if manual_trace_id:
            return manual_trace_id

        # Fall back to OpenTelemetry
        try:
            span = trace.get_current_span()
            if not span or isinstance(span, NonRecordingSpan):
                return None

            span_context = span.get_span_context()
            if not span_context or not span_context.is_valid:
                return None

            trace_id = span_context.trace_id
            if trace_id == 0:
                return None

            return format(trace_id, '032x')
        except Exception as e:
            print(f"[CONTEXT] Could not get trace_id: {e}")
            return None

    @staticmethod
    def get_span_id() -> Optional[str]:
        """Get span_id from context variables or OpenTelemetry span."""
        # First check manual context
        manual_span_id = _span_id_var.get()
        if manual_span_id:
            return manual_span_id

        # Fall back to OpenTelemetry
        try:
            span = trace.get_current_span()
            if not span or isinstance(span, NonRecordingSpan):
                return None

            span_context = span.get_span_context()
            if not span_context or not span_context.is_valid:
                return None

            span_id = span_context.span_id
            if span_id == 0:
                return None

            return format(span_id, '016x')
        except Exception as e:
            print(f"[CONTEXT] Could not get span_id: {e}")
            return None

    @staticmethod
    def get_correlation_id() -> Optional[str]:
        """Get correlation_id from context variables or use trace_id as fallback."""
        manual_correlation_id = _correlation_id_var.get()
        if manual_correlation_id:
            return manual_correlation_id

        # Use trace_id as correlation_id fallback
        return ObservabilityContext.get_trace_id()

    @staticmethod
    def get_or_create_trace_id() -> str:
        """
        Get trace_id from context or auto-generate if not present.
        Sets the generated ID in context for subsequent calls.
        """
        trace_id = ObservabilityContext.get_trace_id()
        if trace_id:
            return trace_id

        # Auto-generate and set in context
        new_trace_id = ObservabilityContext._generate_trace_id()
        _trace_id_var.set(new_trace_id)
        return new_trace_id

    @staticmethod
    def get_or_create_span_id() -> str:
        """
        Get span_id from context or auto-generate if not present.
        Sets the generated ID in context for subsequent calls.
        """
        span_id = ObservabilityContext.get_span_id()
        if span_id:
            return span_id

        # Auto-generate and set in context
        new_span_id = ObservabilityContext._generate_span_id()
        _span_id_var.set(new_span_id)
        return new_span_id

    @staticmethod
    def get_or_create_correlation_id() -> str:
        """
        Get correlation_id from context or auto-generate if not present.
        Sets the generated ID in context for subsequent calls.
        """
        correlation_id = ObservabilityContext.get_correlation_id()
        if correlation_id:
            return correlation_id

        # Auto-generate and set in context
        new_correlation_id = ObservabilityContext._generate_correlation_id()
        _correlation_id_var.set(new_correlation_id)
        return new_correlation_id

    @staticmethod
    def ensure_context() -> Dict[str, str]:
        """
        Ensure all context IDs exist, auto-generating if necessary.
        Returns dict with all IDs.
        """
        return {
            'trace_id': ObservabilityContext.get_or_create_trace_id(),
            'span_id': ObservabilityContext.get_or_create_span_id(),
            'correlation_id': ObservabilityContext.get_or_create_correlation_id()
        }

    @staticmethod
    def set_trace_id(trace_id: Optional[str]) -> None:
        """Set trace_id in context variables."""
        _trace_id_var.set(trace_id)

    @staticmethod
    def set_span_id(span_id: Optional[str]) -> None:
        """Set span_id in context variables."""
        _span_id_var.set(span_id)

    @staticmethod
    def set_correlation_id(correlation_id: Optional[str]) -> None:
        """Set correlation_id in context variables."""
        _correlation_id_var.set(correlation_id)

    @staticmethod
    def get_current_span():
        """Get the current OpenTelemetry span."""
        try:
            span = trace.get_current_span()
            if span and not isinstance(span, NonRecordingSpan):
                return span
            return None
        except Exception:
            return None

    @staticmethod
    def set_attribute(key: str, value: Any, span=None) -> None:
        """Set an attribute on the current or specified span."""
        target_span = span or ObservabilityContext.get_current_span()
        if target_span:
            try:
                target_span.set_attribute(key, value)
            except Exception as e:
                print(f"[CONTEXT] Error setting attribute: {e}")

    @staticmethod
    def add_event(event_name: str, attributes: Optional[Dict[str, Any]] = None, span=None) -> None:
        """Add an event to the current or specified span."""
        target_span = span or ObservabilityContext.get_current_span()
        if target_span:
            try:
                target_span.add_event(event_name, attributes or {})
            except Exception as e:
                print(f"[CONTEXT] Error adding event: {e}")

    @staticmethod
    def record_exception(exception: Exception, span=None) -> None:
        """Record an exception on the current or specified span."""
        target_span = span or ObservabilityContext.get_current_span()
        if target_span:
            try:
                target_span.record_exception(exception)
            except Exception as e:
                print(f"[CONTEXT] Error recording exception: {e}")

    @staticmethod
    def inject_context(carrier: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Inject OpenTelemetry context into carrier for propagation."""
        if carrier is None:
            carrier = {}

        if not isinstance(carrier, dict):
            print(f"[CONTEXT] Carrier must be dict, got {type(carrier)}. Creating new dict.")
            carrier = {}

        try:
            inject(carrier)

            # Also inject manual context if present
            manual_trace_id = _trace_id_var.get()
            manual_span_id = _span_id_var.get()
            manual_correlation_id = _correlation_id_var.get()

            if manual_trace_id:
                carrier['x-trace-id'] = manual_trace_id
            if manual_span_id:
                carrier['x-span-id'] = manual_span_id
            if manual_correlation_id:
                carrier['x-correlation-id'] = manual_correlation_id

        except Exception as e:
            print(f"[CONTEXT] Error injecting context: {e}")

        return carrier

    @staticmethod
    def extract_context(carrier: Dict[str, str]):
        """Extract context from carrier and return context manager."""
        return _CarrierContextManager(carrier)

    @staticmethod
    def to_dict() -> Dict[str, Any]:
        """
        Get current context, auto-generating IDs if missing.
        Ensures all ID formats satisfy OTEL standards.
        """
        trace_id = ObservabilityContext.get_or_create_trace_id()
        span_id = ObservabilityContext.get_or_create_span_id()
        correlation_id = ObservabilityContext.get_or_create_correlation_id()

        return {
            'trace_id': trace_id,
            'span_id': span_id,
            'correlation_id': correlation_id
        }

    @classmethod
    def get_current(cls):
        """Get current context as an object with attributes."""

        class ContextData:
            def __init__(self, trace_id, span_id, correlation_id):
                self.trace_id = trace_id
                self.span_id = span_id
                self.correlation_id = correlation_id

        return ContextData(
            trace_id=cls.get_trace_id(),
            span_id=cls.get_span_id(),
            correlation_id=cls.get_correlation_id()
        )

    def __enter__(self):
        """Enter context manager, setting manual context values."""
        if self._trace_id:
            _trace_id_var.set(self._trace_id)
        if self._span_id:
            _span_id_var.set(self._span_id)
        if self._correlation_id:
            _correlation_id_var.set(self._correlation_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager, clearing manual context values."""
        # Reset to None when exiting context
        if self._trace_id:
            _trace_id_var.set(None)
        if self._span_id:
            _span_id_var.set(None)
        if self._correlation_id:
            _correlation_id_var.set(None)
        return False


class _CarrierContextManager:
    """Context manager for extracting and attaching OpenTelemetry context from carriers."""

    def __init__(self, carrier: Dict[str, str]):
        self.carrier = carrier
        self.token = None
        self._manual_trace_id = None
        self._manual_span_id = None
        self._manual_correlation_id = None

    def __enter__(self):
        try:
            # Extract OpenTelemetry context
            otel_context = extract(self.carrier)
            self.token = attach(otel_context)

            # Extract manual context
            self._manual_trace_id = self.carrier.get('x-trace-id')
            self._manual_span_id = self.carrier.get('x-span-id')
            self._manual_correlation_id = self.carrier.get('x-correlation-id')

            if self._manual_trace_id:
                _trace_id_var.set(self._manual_trace_id)
            if self._manual_span_id:
                _span_id_var.set(self._manual_span_id)
            if self._manual_correlation_id:
                _correlation_id_var.set(self._manual_correlation_id)

        except Exception as e:
            print(f"[CONTEXT] Error in context extraction: {e}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.token is not None:
                detach(self.token)

            # Clear manual context
            if self._manual_trace_id:
                _trace_id_var.set(None)
            if self._manual_span_id:
                _span_id_var.set(None)
            if self._manual_correlation_id:
                _correlation_id_var.set(None)

        except Exception as e:
            print(f"[CONTEXT] Error in context detachment: {e}")
        return False


class BaseFrameworkAdapter(ABC):
    """
    Abstract base class for framework-specific adapters.
    Each web framework needs to implement how it:
    1. Extracts headers from incoming requests
    2. Applies middleware to the application

    To add a new framework:
    1. Inherit from this class
    2. Implement apply_middleware() method
    3. Register using SetContextManager.register_framework()
    """

    def __init__(self):
        """Initialize adapter with header mappings for ID extraction."""
        self.header_mappings = {
            'trace_id': ['traceparent', 'x-trace-id', 'x-b3-traceid'],
            'span_id': ['x-span-id', 'x-b3-spanid'],
            'correlation_id': ['x-correlation-id', 'x-request-id']
        }

    @abstractmethod
    def apply_middleware(self, app: Any) -> None:
        """
        Apply middleware to the framework application.

        Args:
            app: Framework-specific application instance
        """
        pass

    def extract_trace_id(self, headers: Dict[str, str]) -> Optional[str]:
        """
        Extract trace ID from headers with fallback logic.
        Supports W3C Trace Context (traceparent) and B3 formats.

        Args:
            headers: Request headers (case-insensitive dict)

        Returns:
            Extracted trace ID or None
        """
        # Normalize headers to lowercase for case-insensitive lookup
        headers_lower = {k.lower(): v for k, v in headers.items()}

        # Try each header in priority order
        for header_name in self.header_mappings['trace_id']:
            value = headers_lower.get(header_name.lower())
            if value:
                # Handle W3C Trace Context format: "00-<trace-id>-<span-id>-<flags>"
                if header_name == 'traceparent':
                    parts = value.split('-')
                    if len(parts) >= 2:
                        return parts[1]  # Extract trace-id portion
                else:
                    # Direct trace ID value
                    return value

        return None

    def extract_span_id(self, headers: Dict[str, str]) -> Optional[str]:
        """
        Extract span ID from headers.

        Args:
            headers: Request headers

        Returns:
            Extracted span ID or None
        """
        headers_lower = {k.lower(): v for k, v in headers.items()}

        for header_name in self.header_mappings['span_id']:
            value = headers_lower.get(header_name.lower())
            if value:
                return value

        # Try extracting from traceparent
        traceparent = headers_lower.get('traceparent')
        if traceparent:
            parts = traceparent.split('-')
            if len(parts) >= 3:
                return parts[2]  # Extract span-id portion

        return None

    def extract_correlation_id(self, headers: Dict[str, str]) -> Optional[str]:
        """
        Extract correlation ID from headers.

        Args:
            headers: Request headers

        Returns:
            Extracted correlation ID or None
        """
        headers_lower = {k.lower(): v for k, v in headers.items()}

        for header_name in self.header_mappings['correlation_id']:
            value = headers_lower.get(header_name.lower())
            if value:
                return value

        return None

    def set_context_from_headers(self, headers: Dict[str, str]) -> None:
        """
        Extract IDs from headers and set in ObservabilityContext.
        This is the core logic shared by all framework adapters.

        Args:
            headers: Request headers dictionary
        """
        trace_id = self.extract_trace_id(headers)
        span_id = self.extract_span_id(headers)
        correlation_id = self.extract_correlation_id(headers)

        # Set in context - ObservabilityContext will handle None values
        # by falling back to OTEL or auto-generation
        if trace_id:
            ObservabilityContext.set_trace_id(trace_id)

        if span_id:
            ObservabilityContext.set_span_id(span_id)

        if correlation_id:
            ObservabilityContext.set_correlation_id(correlation_id)

        # Ensure context exists (will auto-generate if needed)
        ObservabilityContext.ensure_context()


class FastAPIAdapter(BaseFrameworkAdapter):
    """
    FastAPI-specific adapter using Starlette middleware.

    Integrates with FastAPI's middleware system to extract context
    from incoming requests and set it for the entire request lifecycle.
    """

    def apply_middleware(self, app: Any) -> None:
        """
        Apply middleware to FastAPI application.

        Args:
            app: FastAPI application instance
        """
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.requests import Request

        class ObservabilityMiddleware(BaseHTTPMiddleware):
            """Middleware that extracts observability context from request headers."""

            def __init__(self, app, adapter: FastAPIAdapter):
                super().__init__(app)
                self.adapter = adapter

            async def dispatch(self, request: Request, call_next):
                """
                Extract context before request processing.
                Context automatically cleared after request by contextvars.
                """
                # Extract headers and set context
                headers = dict(request.headers)
                self.adapter.set_context_from_headers(headers)

                try:
                    # Process request with context set
                    response = await call_next(request)
                    return response
                finally:
                    # Context automatically cleared by contextvars when request ends
                    pass

        # Add middleware to FastAPI app
        app.add_middleware(ObservabilityMiddleware, adapter=self)
        print("[CONTEXT MANAGER] FastAPI middleware registered")


class FlaskAdapter(BaseFrameworkAdapter):
    """
    Flask-specific adapter using before_request and teardown_request hooks.

    Integrates with Flask's request lifecycle hooks to extract and manage context.
    """

    def apply_middleware(self, app: Any) -> None:
        """
        Apply middleware to Flask application.

        Args:
            app: Flask application instance
        """
        from flask import request, g

        @app.before_request
        def set_observability_context():
            """Set context before each request."""
            headers = dict(request.headers)
            self.set_context_from_headers(headers)

            # Store in Flask's g object for easy access in views if needed
            g.trace_id = ObservabilityContext.get_trace_id()
            g.span_id = ObservabilityContext.get_span_id()
            g.correlation_id = ObservabilityContext.get_correlation_id()

        @app.teardown_request
        def clear_observability_context(exception=None):
            """
            Clear context after request completes.
            Note: contextvars automatically handles cleanup, but this is explicit.
            """
            # Context is automatically cleared by contextvars
            pass

        print("[CONTEXT MANAGER] Flask middleware registered")


class SetContextManager:
    """
    Main context manager class that provides framework-agnostic initialization.
    Uses factory pattern to create appropriate framework adapters.

    Features:
    - Automatic framework detection and adapter selection
    - Extensible: easily add new framework support
    - Manages middleware lifecycle

    Example:
        manager = SetContextManager('fastapi')
        manager.setup(app)
    """

    # Registry of supported frameworks and their adapters
    _adapters = {
        'fastapi': FastAPIAdapter,
        'flask': FlaskAdapter,
    }

    def __init__(self, framework: str):
        framework_lower = framework.lower()

        if framework_lower not in self._adapters:
            raise ValueError(
                f"Framework '{framework}' not supported. "
                f"Available: {list(self._adapters.keys())}"
            )

        self.framework = framework_lower
        self.adapter = self._adapters[framework_lower]()
        print(f"[CONTEXT MANAGER] Initialized for framework: {framework}")

    def setup(self, app: Any) -> None:
        self.adapter.apply_middleware(app)


    @classmethod
    def supported_frameworks(cls) -> list:
        return list(cls._adapters.keys())


class ServiceObservability:

    _initialized = False
    _context_manager: Optional[SetContextManager] = None

    @classmethod
    def initialize(
            cls,
            service_name: str,
            service_version: str = "1.0.0",
            environment: str = "development",
            framework: Optional[str] = None,
            app: Optional[Any] = None,
            enable_logging: bool = True,
            enable_tracing: bool = True,
            enable_metrics: bool = True,
    ) -> None:
        if cls._initialized:
            # Import here to avoid circular dependency
            from ..config.data_config import ServiceConfig
            print(f"[SERVICE OBSERVABILITY] Already initialized for: {ServiceConfig.service_name}")
            return

        print("=" * 70)
        print(f"[SERVICE OBSERVABILITY] Initializing for service: {service_name}")
        print("=" * 70)

        # Step 1: Configure service metadata (global config)
        try:
            from obs_framework.config.config import ServiceConfig
            ServiceConfig.configure(
                service_name=service_name,
                service_version=service_version,
                environment=environment
            )
            print(f"✓ Service config: {service_name} v{service_version} ({environment})")
        except ImportError as e:
            print(f"✗ Failed to configure service: {e}")
            raise

        # Step 2: Setup framework middleware (extracts IDs from headers)
        if framework and app:
            try:
                cls._context_manager = SetContextManager(framework)
                cls._context_manager.setup(app)
                print(f"✓ Context middleware registered for {framework}")
            except Exception as e:
                print(f"✗ Failed to setup framework middleware: {e}")
                print("  Continuing without middleware - IDs will be auto-generated")
        elif framework or app:
            print("⚠ Warning: Both 'framework' and 'app' must be provided for middleware")
            print("  Continuing without middleware - IDs will be auto-generated")

        cls._initialized = True
        print("=" * 70)
        print(f"[SERVICE OBSERVABILITY] ✓ Initialization complete for {service_name}")
        print("=" * 70)

    @classmethod
    def is_initialized(cls) -> bool:
        """
        Check if observability has been initialized.

        Returns:
            True if initialized, False otherwise
        """
        return cls._initialized

    @classmethod
    def get_context_manager(cls) -> Optional[SetContextManager]:
        """
        Get the context manager instance.

        Returns:
            SetContextManager instance or None if not initialized
        """
        return cls._context_manager


