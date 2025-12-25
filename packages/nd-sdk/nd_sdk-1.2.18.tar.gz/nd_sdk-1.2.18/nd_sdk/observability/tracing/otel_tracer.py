import functools
import inspect
from typing import Optional, Callable, List, Set
import os
import asyncio
import traceback
import threading
import re
from typing import Any, Dict, Optional, Sequence
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult, BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode
from ..context_manager import ObservabilityContext
from ...config.data_config import TraceConfig,ExporterConfig
from ...config.factory import get_config
from ...config.data_config import ServiceConfig

# Traceback filtering for cleaner error messages
EXCLUDED_MODULES = [
    r"asyncio",
    r"opentelemetry",
    r"threading",
    r"concurrent",
    r"contextlib",
    r"logging",
]
exclude_pattern = re.compile("|".join(EXCLUDED_MODULES))


def filter_traceback(tb_list):
    """Filter traceback to remove framework noise."""
    return [line for line in tb_list if not exclude_pattern.search(line)]


# Global registry of traced functions
_TRACED_FUNCTIONS: Set[str] = set()

# Global configuration for selective tracing
_TRACE_CONFIG = {
    'enabled': True,
    'trace_all': True,
    'allowed_functions': set(),
    'allowed_prefixes': set(),
}


def _should_trace_function(func_name: str) -> bool:
    """Determine if a function should be traced based on configuration."""
    if not _TRACE_CONFIG['enabled']:
        return False

    if _TRACE_CONFIG['trace_all']:
        return True

    if func_name in _TRACE_CONFIG['allowed_functions']:
        return True

    for prefix in _TRACE_CONFIG['allowed_prefixes']:
        if func_name.startswith(prefix):
            return True

    return False


def _get_function_identifier(func: Callable) -> str:
    """Get unique identifier for a function."""
    return f"{func.__module__}.{func.__qualname__}"


def _get_function_metadata(func: Callable) -> dict:
    """Extract metadata from a function."""
    metadata = {
        "code.function": func.__name__,
        "code.namespace": func.__module__,
    }

    if "." in func.__qualname__:
        parts = func.__qualname__.rsplit(".", 1)
        if len(parts) == 2:
            metadata["code.class"] = parts[0]

    try:
        metadata["code.filepath"] = inspect.getfile(func)
        metadata["code.lineno"] = inspect.getsourcelines(func)[1]
    except (TypeError, OSError):
        pass

    return metadata


def _detect_endpoint_type(func: Callable) -> Optional[str]:
    """
    Detect if function is a FastAPI or Flask endpoint.

    Returns:
        'fastapi', 'flask', or None
    """
    # Check if function has FastAPI route attributes
    if hasattr(func, '__wrapped__'):
        wrapped = func.__wrapped__
        if hasattr(wrapped, '__self__'):
            obj = wrapped.__self__
            if obj.__class__.__name__ in ('APIRoute', 'Route'):
                return 'fastapi'

    # Check for FastAPI markers on the function itself
    if hasattr(func, 'dependencies') or hasattr(func, '__route__'):
        return 'fastapi'

    # Check for Flask markers
    if hasattr(func, 'methods') or hasattr(func, 'rule'):
        return 'flask'

    # Check module imports to infer framework
    module = inspect.getmodule(func)
    if module:
        module_name = module.__name__
        if 'fastapi' in module_name.lower():
            return 'fastapi'
        elif 'flask' in module_name.lower():
            return 'flask'

    return None


def _extract_http_info_fastapi(args, kwargs) -> dict:
    """Extract HTTP information from FastAPI request."""
    http_info = {}

    try:
        # Look for Request object in args/kwargs
        from fastapi import Request
        from starlette.requests import Request as StarletteRequest

        request = None
        for arg in args:
            if isinstance(arg, (Request, StarletteRequest)):
                request = arg
                break

        if not request and 'request' in kwargs:
            request = kwargs['request']

        if request:
            http_info['http.method'] = request.method
            http_info['http.url'] = str(request.url)
            http_info['http.route'] = request.url.path
            http_info['http.scheme'] = request.url.scheme
            http_info['http.target'] = request.url.path

            # Headers (selective)
            if hasattr(request, 'headers'):
                http_info['http.user_agent'] = request.headers.get('user-agent', 'unknown')

                # Add client info if available
                if hasattr(request, 'client') and request.client:
                    http_info['http.client.ip'] = request.client.host

    except ImportError:
        pass
    except Exception as e:
        print(f"[TRACE DEBUG] Failed to extract FastAPI info: {e}")

    return http_info


def _extract_http_info_flask(args, kwargs) -> dict:
    """Extract HTTP information from Flask request."""
    http_info = {}

    try:
        from flask import request

        if request:
            http_info['http.method'] = request.method
            http_info['http.url'] = request.url
            http_info['http.route'] = request.path
            http_info['http.scheme'] = request.scheme
            http_info['http.target'] = request.path

            # Headers
            http_info['http.user_agent'] = request.headers.get('User-Agent', 'unknown')

            # Client info
            if request.remote_addr:
                http_info['http.client.ip'] = request.remote_addr

    except (ImportError, RuntimeError):
        # RuntimeError occurs when outside request context
        pass
    except Exception as e:
        print(f"[TRACE DEBUG] Failed to extract Flask info: {e}")

    return http_info


def _extract_http_response_info(result, endpoint_type: str) -> dict:
    """
    Extract HTTP response information with enhanced status code detection.
    """
    response_info = {}

    try:
        # Check if result has status_code attribute (works for all Response types)
        if hasattr(result, 'status_code'):
            response_info['http.status_code'] = result.status_code
            print(f"[TRACE DEBUG] Found status_code attribute: {result.status_code}")
            return response_info

        # FastAPI-specific handling
        if endpoint_type == 'fastapi':
            try:
                from starlette.responses import Response, JSONResponse

                if isinstance(result, Response):
                    response_info['http.status_code'] = result.status_code
                elif isinstance(result, dict):
                    # Default success for dict returns
                    response_info['http.status_code'] = 200
                    print(f"[TRACE DEBUG] Dict response, defaulting to 200")
                elif result is None:
                    # None response typically means 204 No Content
                    response_info['http.status_code'] = 204
                else:
                    # Other successful returns
                    response_info['http.status_code'] = 200
                    print(f"[TRACE DEBUG] Unknown response type, defaulting to 200")

            except ImportError:
                # Fallback if starlette not available
                response_info['http.status_code'] = 200

        # Flask-specific handling
        elif endpoint_type == 'flask':
            try:
                from flask import Response as FlaskResponse

                if isinstance(result, FlaskResponse):
                    response_info['http.status_code'] = result.status_code
                elif isinstance(result, tuple):
                    # Flask can return (body, status_code) or (body, status_code, headers)
                    if len(result) >= 2 and isinstance(result[1], int):
                        response_info['http.status_code'] = result[1]
                    else:
                        response_info['http.status_code'] = 200
                else:
                    response_info['http.status_code'] = 200

            except ImportError:
                response_info['http.status_code'] = 200

        # Generic fallback
        else:
            response_info['http.status_code'] = 200
            print(f"[TRACE DEBUG] No endpoint type, defaulting to 200")

    except Exception as e:
        print(f"[TRACE DEBUG] Failed to extract response info: {e}")
        # Even on error, default to 200 for successful function execution
        response_info['http.status_code'] = 200

    return response_info


class CustomSpanExporter(SpanExporter):
    """
    Custom span exporter that converts OTEL spans to dictionary format
    and exports them using the OTELTraceExporter.

    Note: This class attempts to import OTELTraceExporter from your framework.
    If not available, it will fall back to printing spans for testing/development.
    """

    def __init__(self, endpoint: str, protocol: str = "http", format: str = "json"):
        """
        Initialize the custom span exporter.

        Args:
            endpoint: OTLP endpoint URL
            protocol: Protocol to use (http/grpc)
            format: Format to use (json/protobuf)
        """
        self.endpoint = endpoint
        self.protocol = protocol
        self.format = format

        # Try to import and initialize OTELTraceExporter
        # This is optional - if not available, we'll use a fallback
        try:
            from ..otel_exporter import OTELTraceExporter
            self.custom_exporter = OTELTraceExporter()
            print(f"[EXPORTER] Initialized with OTELTraceExporter")
            print(f"[EXPORTER] Endpoint: {endpoint}, Protocol: {protocol}, Format: {format}")
        except ImportError as e:
            print(f"[EXPORTER] Warning: OTELTraceExporter not found ({e})")
            print(f"[EXPORTER] Using fallback mode (will print spans)")
            self.custom_exporter = None

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """
        Convert OTEL spans to custom format and export.

        Args:
            spans: Sequence of OpenTelemetry ReadableSpan objects

        Returns:
            SpanExportResult indicating success/failure
        """
        if not spans:
            return SpanExportResult.SUCCESS

        try:
            # Get or create event loop for async export
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Export each span
            for span in spans:
                # Convert OTEL span to dictionary format
                span_data = self._convert_span_to_dict(span)

                if self.custom_exporter:
                    # Run async export using the custom exporter
                    if loop.is_running():
                        # If loop is already running, create a task
                        asyncio.create_task(self.custom_exporter.export(span_data))
                    else:
                        # Otherwise run it synchronously
                        loop.run_until_complete(self.custom_exporter.export(span_data))
                else:
                    # Fallback: just print the span data
                    print(f"[EXPORTER] Exporting span: {span_data['name']}")

            return SpanExportResult.SUCCESS

        except Exception as e:
            print(f"[EXPORTER] Export failed: {e}")
            import traceback
            traceback.print_exc()
            return SpanExportResult.FAILURE

    def _convert_span_to_dict(self, span: ReadableSpan) -> dict:
        """
        Convert OpenTelemetry ReadableSpan to dictionary format.

        Args:
            span: OpenTelemetry ReadableSpan object

        Returns:
            Dictionary representation of the span
        """
        context = span.get_span_context()

        # Convert IDs to hex strings
        trace_id = format(context.trace_id, '032x')
        span_id = format(context.span_id, '016x')
        parent_id = format(span.parent.span_id, '016x') if span.parent else None

        # Convert timestamps from nanoseconds to seconds
        start_time = span.start_time / 1e9 if span.start_time else 0
        end_time = span.end_time / 1e9 if span.end_time else 0

        # Map span kind
        kind_mapping = {
            1: "INTERNAL",
            2: "SERVER",
            3: "CLIENT",
            4: "PRODUCER",
            5: "CONSUMER",
        }
        kind = kind_mapping.get(span.kind.value, "INTERNAL")

        # Map status
        status_mapping = {
            0: "UNSET",
            1: "OK",
            2: "ERROR",
        }
        status = status_mapping.get(span.status.status_code.value, "UNSET")

        # Get service name
        service_name = "unknown"
        if span.resource and span.resource.attributes:
            service_name = span.resource.attributes.get("service.name", "unknown")

        # Build span dictionary
        span_dict = {
            "trace_id": trace_id,
            "span_id": span_id,
            "name": span.name,
            "kind": kind,
            "start_time": start_time,
            "end_time": end_time,
            "attributes": dict(span.attributes) if span.attributes else {},
            "status": status,
            "service_name": service_name,
        }

        if parent_id:
            span_dict["parent_id"] = parent_id

        if span.events:
            span_dict["events"] = [
                {
                    "name": event.name,
                    "timestamp": event.timestamp / 1e9,
                    "attributes": dict(event.attributes) if event.attributes else {}
                }
                for event in span.events
            ]

        return span_dict

    def shutdown(self) -> None:
        """Shutdown the exporter"""
        try:
            if self.custom_exporter:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.custom_exporter.shutdown())
            print("[EXPORTER] Shutdown complete")
        except Exception as e:
            print(f"[EXPORTER] Shutdown error: {e}")

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush any buffered spans"""
        return True


class OTELTracer:
    """
    Unified OpenTelemetry Tracer - Standalone Implementation

    A completely standalone tracer that handles both OpenTelemetry tracing and exporting
    in a single class. No dependencies on TraceProvider or other framework components.

    Features:
    - Direct OTEL integration with full span lifecycle management
    - HTTP request tracing with automatic SERVER span kind
    - Automatic HTTP status code to span status mapping
    - Async export via BatchSpanProcessor
    - Thread-safe singleton pattern
    - Optional integration with OTELTraceExporter

    Usage:
        tracer = OTELTracer.get_instance(service_name="my-service")

        with tracer.start_span("operation", http_method="GET", http_url="/api/users") as span:
            # Do work
            tracer.set_http_status(200, span)
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self, service_name: Optional[str] = None, endpoint: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the OTEL tracer.

        Args:
            service_name: Service name for traces (default: from env or 'default-service')
            endpoint: Export endpoint URL (default: from env or 'http://localhost:4318/v1/traces')
            config: Optional configuration dictionary with keys:
                - service_name: Service name
                - endpoint: Export endpoint
                - protocol: Protocol (http/grpc)
                - format: Format (json/protobuf)
        """
        # Handle configuration priority: explicit params > config dict > env vars > defaults
        if config is None:
            config = {}

        # Priority: explicit service_name param > config > env var > default
        if service_name:
            self.service_name = service_name
        elif "service_name" in config:
            self.service_name = config["service_name"]
        else:
            self.service_name = os.getenv("SERVICE_NAME", "default-service")

        # Priority: explicit endpoint param > config > env var > default
        if endpoint:
            self.endpoint = endpoint
        elif "endpoint" in config:
            self.endpoint = config["endpoint"]
        else:
            self.endpoint = ExporterConfig.trace_endpoint

        # Get protocol and format from config or use defaults
        self.protocol = config.get("protocol", "http")
        self.format = config.get("format", "json")

        self._tracer: Optional[trace.Tracer] = None
        self._tracer_provider: Optional[TracerProvider] = None
        self._span_processor = None
        self._initialized = False

        self._initialize()

    def _initialize(self) -> None:
        """Initialize OpenTelemetry tracer with custom exporter"""
        if self._initialized:
            return

        try:
            # Create resource with service name
            resource = Resource.create({"service.name": self.service_name})

            # Create tracer provider
            self._tracer_provider = TracerProvider(resource=resource)

            print(f"[OTEL TRACER] Initializing with endpoint: {self.endpoint}")
            print(f"[OTEL TRACER] Protocol: {self.protocol}, Format: {self.format}")

            # Create custom exporter bridge
            custom_exporter = CustomSpanExporter(
                endpoint=self.endpoint,
                protocol=self.protocol,
                format=self.format
            )

            # Add BatchSpanProcessor for async export
            self._span_processor = BatchSpanProcessor(
                custom_exporter,
                max_queue_size=2048,
                schedule_delay_millis=5000,  # Export every 5 seconds
                max_export_batch_size=512,
                export_timeout_millis=30000
            )
            self._tracer_provider.add_span_processor(self._span_processor)

            # Set global tracer provider
            trace.set_tracer_provider(self._tracer_provider)

            # Get tracer instance
            self._tracer = trace.get_tracer(
                instrumenting_module_name=self.service_name,
                instrumenting_library_version="1.0.0"
            )

            self._initialized = True
            print(f"[OTEL TRACER] Successfully initialized with service: {self.service_name}")

        except Exception as e:
            print(f"[OTEL TRACER] Initialization error: {e}")
            import traceback
            traceback.print_exc()
            raise

    @classmethod
    def get_instance(cls):
        """
        Get singleton instance of the tracer.

        Args:
            service_name: Service name (only used on first call)
            endpoint: Export endpoint (only used on first call)
            config: Optional configuration dictionary (only used on first call)

        Returns:
            OTELTracer instance
        """
        service_config = ServiceConfig(**get_config.get())
        service_name = getattr(service_config, "service_name", "unknown-service-name")
        endpoint = ExporterConfig.trace_endpoint
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(service_name, endpoint)
        return cls._instance

    @contextmanager
    def start_span(
            self,
            name: str,
            kind: str = "INTERNAL",
            attributes: Optional[Dict[str, Any]] = None,
            http_method: Optional[str] = None,
            http_url: Optional[str] = None,
    ):
        """
        Context manager to create and manage a span.

        Args:
            name: Span name
            kind: Span kind (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
            attributes: Additional span attributes
            http_method: HTTP method (GET, POST, etc.) - automatically sets kind to SERVER
            http_url: HTTP URL/route

        Yields:
            OpenTelemetry Span object

        Example:
            with tracer.start_span("my_operation") as span:
                # do work
                pass

            # For HTTP requests
            with tracer.start_span("handle_request", http_method="GET", http_url="/api/users") as span:
                # process request
                tracer.set_http_status(200, span)
        """
        if not self._tracer:
            raise RuntimeError("Tracer not initialized")

        # Prepare attributes
        attrs = attributes.copy() if attributes else {}

        # If HTTP method is provided, set kind to SERVER and add HTTP attributes
        if http_method:
            kind = "SERVER"
            attrs["http.method"] = http_method.upper()
            if http_url:
                attrs["http.url"] = http_url
                attrs["http.target"] = http_url

        # Map string kind to OTEL SpanKind
        span_kind = self._map_span_kind(kind)

        # Create span with context manager
        with self._tracer.start_as_current_span(
                name=name,
                kind=span_kind,
                attributes=attrs,
        ) as span:
            try:
                yield span

            except Exception as exc:
                # Record exception with cleaned traceback
                try:
                    tb_raw = traceback.format_exception(type(exc), exc, exc.__traceback__)
                    tb_clean = filter_traceback(tb_raw)

                    span.record_exception(
                        exc,
                        attributes={
                            "exception.cleaned_stacktrace": "".join(tb_clean)
                        },
                    )
                    span.set_status(Status(StatusCode.ERROR, str(exc)))

                    # Set HTTP status to 500 if this is an HTTP span
                    if http_method:
                        span.set_attribute("http.status_code", 500)

                except Exception as e:
                    print(f"[OTEL TRACER] Failed to record exception: {e}")

                raise

    def set_http_status(self, status_code: int, span: Optional[Any] = None):
        """
        Set HTTP status code on a span.

        Args:
            status_code: HTTP response status code (200, 404, 500, etc.)
            span: Optional span to set status on (uses current span if not provided)

        Example:
            with tracer.start_span("handle_request", http_method="GET") as span:
                result = process_request()
                tracer.set_http_status(200, span)
        """
        try:
            target = span or self.get_current_span()
            if not target:
                print("[OTEL TRACER] No span available to set HTTP status")
                return

            target.set_attribute("http.status_code", status_code)

            # Set span status based on HTTP status code
            if status_code >= 500:
                target.set_status(Status(StatusCode.ERROR, f"HTTP {status_code}"))
            elif status_code >= 400:
                target.set_status(Status(StatusCode.ERROR, f"HTTP {status_code}"))
            else:
                target.set_status(Status(StatusCode.OK))

        except Exception as e:
            print(f"[OTEL TRACER] Failed to set HTTP status: {e}")

    def add_event(
            self,
            event_name: str,
            attributes: Optional[Dict[str, Any]] = None,
            span: Optional[Any] = None
    ):
        """
        Add an event to a span.

        Args:
            event_name: Event name
            attributes: Optional event attributes
            span: Optional span (uses current span if not provided)
        """
        try:
            target = span or self.get_current_span()
            if not target:
                print("[OTEL TRACER] No span available to add event")
                return
            target.add_event(event_name, attributes or {})
        except Exception as e:
            print(f"[OTEL TRACER] Failed to add event: {e}")

    def set_attribute(
            self,
            key: str,
            value: Any,
            span: Optional[Any] = None
    ):
        """
        Set an attribute on a span.

        Args:
            key: Attribute key
            value: Attribute value
            span: Optional span (uses current span if not provided)
        """
        try:
            target = span or self.get_current_span()
            if not target:
                print("[OTEL TRACER] No span available to set attribute")
                return
            target.set_attribute(key, value)
        except Exception as e:
            print(f"[OTEL TRACER] Failed to set attribute: {e}")

    def record_error(
            self,
            error: Exception,
            span: Optional[Any] = None
    ):
        """
        Record an error on a span without ending it.

        Args:
            error: Exception to record
            span: Optional span (uses current span if not provided)
        """
        try:
            target = span or self.get_current_span()
            if not target:
                print("[OTEL TRACER] No span available to record error")
                return

            tb_raw = traceback.format_exception(type(error), error, error.__traceback__)
            tb_clean = filter_traceback(tb_raw)

            target.record_exception(
                error,
                attributes={
                    "exception.cleaned_stacktrace": "".join(tb_clean)
                }
            )
            target.set_status(Status(StatusCode.ERROR, str(error)))

        except Exception as e:
            print(f"[OTEL TRACER] Failed to record error: {e}")

    def get_current_span(self) -> Optional[trace.Span]:
        """
        Get the currently active span.

        Returns:
            Current OpenTelemetry span or None
        """
        try:
            current = trace.get_current_span()
            if current and hasattr(current, 'get_span_context'):
                context = current.get_span_context()
                if context.is_valid and context.trace_flags.sampled:
                    return current
            return None
        except Exception:
            return None

    def get_trace_id(self) -> Optional[str]:
        """Get trace ID from ObservabilityContext."""
        return ObservabilityContext.get_trace_id()

    def get_span_id(self) -> Optional[str]:
        """Get span ID from ObservabilityContext."""
        return ObservabilityContext.get_span_id()

    def get_correlation_id(self) -> Optional[str]:
        """Get correlation ID from ObservabilityContext."""
        return ObservabilityContext.get_correlation_id()

    def shutdown(self):
        """
        Shutdown the tracer and flush remaining spans.
        Call this before application exit.
        """
        try:
            if self._span_processor:
                print("[OTEL TRACER] Flushing remaining spans...")
                self._span_processor.force_flush(timeout_millis=5000)
                self._span_processor.shutdown()
            if self._tracer_provider:
                self._tracer_provider.shutdown()
            self._initialized = False
            print("[OTEL TRACER] Shutdown complete")
        except Exception as e:
            print(f"[OTEL TRACER] Shutdown error: {e}")

    @staticmethod
    def _map_span_kind(kind: str) -> trace.SpanKind:
        """Map string span kind to OpenTelemetry SpanKind"""
        mapping = {
            "INTERNAL": trace.SpanKind.INTERNAL,
            "SERVER": trace.SpanKind.SERVER,
            "CLIENT": trace.SpanKind.CLIENT,
            "PRODUCER": trace.SpanKind.PRODUCER,
            "CONSUMER": trace.SpanKind.CONSUMER,
        }
        return mapping.get(kind.upper(), trace.SpanKind.INTERNAL)


    @classmethod
    def set_tracer(
            cls,
            name: Optional[str] = None,
            kind: str = "INTERNAL",
            capture_args: bool = True,
            capture_result: bool = True,
            attributes: Optional[dict] = None,
            force_trace: bool = False,
            service_name: Optional[str] = None
    ):
        """
        Decorator for tracing function execution using context manager.
        This ensures proper span lifecycle and export.

        Automatically detects FastAPI and Flask endpoints and captures:
        - HTTP method
        - HTTP route
        - HTTP status code
        - Request URL
        - Client IP
        - User agent
        - Error messages and stack traces

        Args:
            name: Optional custom span name
            kind: Span kind (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
            capture_args: Whether to capture function arguments
            capture_result: Whether to capture return value
            attributes: Additional custom attributes
            force_trace: If True, trace regardless of global configuration
            service_name: Service name for tracing (sets it globally on first use)
        """

        def decorator(func: Callable) -> Callable:
            func_metadata = _get_function_metadata(func)
            func_id = _get_function_identifier(func)
            func_name = func.__name__

            _TRACED_FUNCTIONS.add(func_id)

            span_name = name or func.__qualname__

            base_attributes = func_metadata.copy()
            if attributes:
                base_attributes.update(attributes)

            tracer = cls.get_instance()

            # Detect endpoint type once at decoration time
            endpoint_type = _detect_endpoint_type(func)

            # Honor explicit kind parameter, but default to SERVER for endpoints
            if kind.upper() == "SERVER":
                effective_kind = "SERVER"
            elif endpoint_type:
                effective_kind = "SERVER"
            else:
                effective_kind = kind

            print(f"[TRACE DEBUG] Decorating {func_name}: endpoint_type={endpoint_type}, "
                  f"requested_kind={kind}, effective_kind={effective_kind}")

            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args, **kwargs):
                    # Quick check - no tracing overhead if disabled
                    should_trace = force_trace or _should_trace_function(func_name)

                    if not should_trace:
                        return await func(*args, **kwargs)

                    # Prepare attributes
                    attrs = base_attributes.copy()

                    # Add endpoint type marker if detected
                    if endpoint_type:
                        attrs['endpoint.type'] = endpoint_type
                        attrs['endpoint.framework'] = endpoint_type

                    # Extract HTTP info when kind is SERVER
                    http_info = {}
                    if effective_kind == "SERVER":
                        # Try both FastAPI and Flask detection
                        if endpoint_type == 'fastapi' or not endpoint_type:
                            fastapi_info = _extract_http_info_fastapi(args, kwargs)
                            if fastapi_info:
                                http_info.update(fastapi_info)

                        if not http_info and (endpoint_type == 'flask' or not endpoint_type):
                            flask_info = _extract_http_info_flask(args, kwargs)
                            if flask_info:
                                http_info.update(flask_info)

                        if http_info:
                            attrs.update(http_info)
                            print(f"[TRACE DEBUG] Extracted HTTP info: {list(http_info.keys())}")
                        else:
                            print(f"[TRACE DEBUG] No HTTP info extracted for SERVER span")

                    if capture_args:
                        try:
                            sig = inspect.signature(func)
                            bound_args = sig.bind(*args, **kwargs)
                            bound_args.apply_defaults()
                            for arg_name, arg_value in bound_args.arguments.items():
                                # Skip Request objects to avoid clutter
                                if arg_name == 'request':
                                    continue
                                if isinstance(arg_value, (str, int, float, bool, type(None))):
                                    attrs[f"function.arg.{arg_name}"] = str(arg_value)[:100]
                        except Exception as e:
                            print(f"[TRACE DEBUG] Failed to capture args: {e}")

                    # Use context manager for proper span lifecycle
                    with tracer.start_span(
                            name=span_name,
                            kind=effective_kind,
                            attributes=attrs
                    ) as span:
                        try:
                            result = await func(*args, **kwargs)

                            # ENHANCED: Extract HTTP response info for SERVER spans
                            if effective_kind == "SERVER":
                                response_info = {}

                                # Try to extract from result
                                if endpoint_type:
                                    response_info = _extract_http_response_info(result, endpoint_type)
                                else:
                                    response_info = _extract_http_response_info(result, 'fastapi')

                                # FALLBACK 1: Check if result has status_code directly
                                if not response_info.get('http.status_code') and hasattr(result, 'status_code'):
                                    response_info['http.status_code'] = result.status_code
                                    print(f"[TRACE DEBUG] Got status from result.status_code: {result.status_code}")

                                # FALLBACK 2: Default to 200 for successful execution
                                if not response_info.get('http.status_code'):
                                    response_info['http.status_code'] = 200
                                    print(f"[TRACE DEBUG] No status found, defaulting to 200")

                                # Apply all response info
                                for key, value in response_info.items():
                                    tracer.set_attribute(key, value, span)

                                print(f"[TRACE DEBUG] Final response info: {response_info}")

                            if capture_result and result is not None:
                                try:
                                    if isinstance(result, (str, int, float, bool)):
                                        tracer.set_attribute("function.result", str(result)[:100], span)
                                    elif isinstance(result, dict) and effective_kind == "SERVER":
                                        # For endpoints, capture result size
                                        tracer.set_attribute("response.body.size", len(str(result)), span)
                                except Exception as e:
                                    print(f"[TRACE DEBUG] Failed to capture result: {e}")

                            return result

                        except Exception as e:
                            # Record error details
                            error_attrs = {
                                "error": True,
                                "error.type": type(e).__name__,
                                "error.message": str(e),
                            }

                            # For HTTP endpoints, set error status code
                            if effective_kind == "SERVER":
                                # Try to extract status from exception
                                status_code = getattr(e, 'status_code', 500)
                                error_attrs['http.status_code'] = status_code
                                print(f"[TRACE DEBUG] Exception status code: {status_code}")

                            for key, value in error_attrs.items():
                                tracer.set_attribute(key, value, span)

                            raise

                return async_wrapper

            else:
                @functools.wraps(func)
                def sync_wrapper(*args, **kwargs):
                    # Quick check - no tracing overhead if disabled
                    tracer = cls.get_instance()
                    should_trace = force_trace or _should_trace_function(func_name)

                    if not should_trace:
                        return func(*args, **kwargs)

                    # Prepare attributes
                    attrs = base_attributes.copy()

                    # Add endpoint type marker if detected
                    if endpoint_type:
                        attrs['endpoint.type'] = endpoint_type
                        attrs['endpoint.framework'] = endpoint_type

                    # Extract HTTP info when kind is SERVER
                    http_info = {}
                    if effective_kind == "SERVER":
                        # Try both FastAPI and Flask detection
                        if endpoint_type == 'fastapi' or not endpoint_type:
                            fastapi_info = _extract_http_info_fastapi(args, kwargs)
                            if fastapi_info:
                                http_info.update(fastapi_info)

                        if not http_info and (endpoint_type == 'flask' or not endpoint_type):
                            flask_info = _extract_http_info_flask(args, kwargs)
                            if flask_info:
                                http_info.update(flask_info)

                        if http_info:
                            attrs.update(http_info)
                            print(f"[TRACE DEBUG] Extracted HTTP info: {list(http_info.keys())}")
                        else:
                            print(f"[TRACE DEBUG] No HTTP info extracted for SERVER span")

                    if capture_args:
                        try:
                            sig = inspect.signature(func)
                            bound_args = sig.bind(*args, **kwargs)
                            bound_args.apply_defaults()
                            for arg_name, arg_value in bound_args.arguments.items():
                                # Skip Request objects to avoid clutter
                                if arg_name == 'request':
                                    continue
                                if isinstance(arg_value, (str, int, float, bool, type(None))):
                                    attrs[f"function.arg.{arg_name}"] = str(arg_value)[:100]
                        except Exception as e:
                            print(f"[TRACE DEBUG] Failed to capture args: {e}")

                    # Use context manager for proper span lifecycle
                    with tracer.start_span(
                            name=span_name,
                            kind=effective_kind,
                            attributes=attrs
                    ) as span:
                        try:
                            result = func(*args, **kwargs)

                            # ENHANCED: Extract HTTP response info for SERVER spans
                            if effective_kind == "SERVER":
                                response_info = {}

                                # Try to extract from result
                                if endpoint_type:
                                    response_info = _extract_http_response_info(result, endpoint_type)
                                else:
                                    response_info = _extract_http_response_info(result, 'fastapi')

                                # FALLBACK 1: Check if result has status_code directly
                                if not response_info.get('http.status_code') and hasattr(result, 'status_code'):
                                    response_info['http.status_code'] = result.status_code
                                    print(f"[TRACE DEBUG] Got status from result.status_code: {result.status_code}")

                                # FALLBACK 2: Default to 200 for successful execution
                                if not response_info.get('http.status_code'):
                                    response_info['http.status_code'] = 200
                                    print(f"[TRACE DEBUG] No status found, defaulting to 200")

                                # Apply all response info
                                for key, value in response_info.items():
                                    tracer.set_attribute(key, value, span)

                                print(f"[TRACE DEBUG] Final response info: {response_info}")

                            if capture_result and result is not None:
                                try:
                                    if isinstance(result, (str, int, float, bool)):
                                        tracer.set_attribute("function.result", str(result)[:100], span)
                                    elif isinstance(result, dict) and effective_kind == "SERVER":
                                        # For endpoints, capture result size
                                        tracer.set_attribute("response.body.size", len(str(result)), span)
                                except Exception as e:
                                    print(f"[TRACE DEBUG] Failed to capture result: {e}")

                            return result

                        except Exception as e:
                            # Record error details
                            error_attrs = {
                                "error": True,
                                "error.type": type(e).__name__,
                                "error.message": str(e),
                            }

                            # For HTTP endpoints, set error status code
                            if effective_kind == "SERVER":
                                # Try to extract status from exception
                                status_code = getattr(e, 'status_code', 500)
                                error_attrs['http.status_code'] = status_code
                                print(f"[TRACE DEBUG] Exception status code: {status_code}")

                            for key, value in error_attrs.items():
                                tracer.set_attribute(key, value, span)

                            raise

                return sync_wrapper

        return decorator




