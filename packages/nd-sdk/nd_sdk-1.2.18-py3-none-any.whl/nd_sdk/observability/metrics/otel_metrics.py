import time
import threading
import concurrent.futures
from typing import Any, Dict, Optional, Callable
from opentelemetry.sdk.resources import Resource
from opentelemetry.metrics import Observation
import asyncio
from functools import wraps
from ...config.data_config import MetricsConfig
from ...config.factory import get_config
from ..otel_exporter import OTELMetricsExporter
from ...config.data_config import ServiceConfig

class ResourceManager:
    """
    Singleton Resource Manager for OpenTelemetry.
    Ensures only one Resource instance is created across the application.
    """
    _instance: Optional['ResourceManager'] = None
    _lock = threading.Lock()
    _resource: Optional[Resource] = None
    

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ResourceManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_resource(cls) -> Resource:
        """
        Get or create the singleton Resource instance.

        Returns:
            Singleton Resource instance
        """
        service_config = ServiceConfig(**get_config.get())
        if cls._resource is None:
            with cls._lock:
                if cls._resource is None:
                    cls._resource = Resource.create({
                        "service.name": getattr(service_config, "service_name","unknown-service-name"),
                        "service.version": getattr(service_config, "service_version","1.0.0"),
                        "deployment.environment": getattr(service_config, "environment","Dev"),
                    })
        return cls._resource


class OTELMetrics:

    # Pre-computed set for faster attribute filtering
    _EXCLUDED_KEYS = frozenset({
        'description', 'unit', 'attributes', 'metric_type',
        'name', 'value', 'service_name', 'timestamp',
        'trace_id', 'span_id', 'correlation_id'
    })

    _instance: Optional['OTELMetrics'] = None
    _lock = threading.Lock()

    def __init__(self):
        service_config = get_config.get()
        service_config = ServiceConfig(**service_config)
        self.service_name = getattr(service_config, "service_name", "unknown-service-name")
        self._service_version = getattr(service_config, "service_version", "1.0.0")
        self._environment = getattr(service_config, "environment", "Dev")
        self._initialized = False
        self._shutdown_flag = False

        # Custom exporter
        self._exporter = OTELMetricsExporter()

        # Memory management
        self._gauge_ttl = 3600
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # Cleanup every 5 minutes

        max_workers = MetricsConfig.max_workers if hasattr(MetricsConfig, 'max_workers') else 4

        # Thread pool for async metric processing
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="metrics_worker"
        )

        # Context cache for performance
        self._context_cache = {}
        self._context_cache_time = 0
        self._context_cache_ttl = 0.1  # 100ms cache

        # Error logging deduplication
        self._logged_errors = set()

        self._initialized = True
        print(f"[OTEL_METRICS] Initialized with OTELMetricsExporter for service: {self.service_name}")

    @classmethod
    def get_instance(cls) -> 'OTELMetrics':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def set_context(
            self,
            trace_id: Optional[str] = None,
            span_id: Optional[str] = None,
            correlation_id: Optional[str] = None
    ) -> None:
        """
        Set observability context for metric enrichment.

        Args:
            trace_id: Distributed trace ID
            span_id: Current span ID
            correlation_id: Correlation ID for request tracking
        """
        self._context_cache = {
            'trace_id': trace_id,
            'span_id': span_id,
            'correlation_id': correlation_id
        }
        self._context_cache_time = time.time()

    def _enrich_attributes(self, attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Enrich attributes with observability context.

        Args:
            attributes: Optional base attributes

        Returns:
            Enriched attributes dict
        """
        try:
            enriched = attributes.copy() if attributes else {}

            # Add cached context IDs
            if self._context_cache.get('trace_id'):
                enriched["trace_id"] = self._context_cache['trace_id']
            if self._context_cache.get('span_id'):
                enriched["span_id"] = self._context_cache['span_id']
            if self._context_cache.get('correlation_id'):
                enriched["correlation_id"] = self._context_cache['correlation_id']

            return enriched
        except Exception:
            return attributes.copy() if attributes else {}

    def _export_metric(self, data: Dict[str, Any]) -> None:
        """
        Export metric data using the custom exporter.

        Args:
            data: Metric data to export
        """
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Loop is closed")
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run export
            if loop.is_running():
                # If loop is running, schedule the coroutine
                asyncio.ensure_future(self._exporter.export(data))
            else:
                # If loop is not running, run it
                loop.run_until_complete(self._exporter.export(data))

        except Exception as e:
            error_key = f"export:{type(e).__name__}"
            if error_key not in self._logged_errors:
                print(f"[OTEL_METRICS ERROR] Export failed: {e}")
                self._logged_errors.add(error_key)

    def _record_metric_safe(self, metric_func, *args, **kwargs):
        """
        Safely record a metric, catching all exceptions.

        Args:
            metric_func: The metric method to call
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        if self._shutdown_flag:
            return

        try:
            metric_func(*args, **kwargs)
        except Exception as e:
            # Log but never raise - only log first occurrence
            error_key = f"{metric_func.__name__}:{type(e).__name__}"
            if error_key not in self._logged_errors:
                print(f"[OTEL_METRICS ERROR] {metric_func.__name__} failed: {e}")
                self._logged_errors.add(error_key)

    def counter(
            self,
            name: str,
            value: float = 1.0,
            attributes: Optional[Dict[str, Any]] = None,
            **kwargs
    ) -> None:
        """
        Record a counter metric (fire and forget).

        Args:
            name: Metric name
            value: Counter increment value (default 1.0)
            attributes: Optional metric attributes/labels
            **kwargs: Additional attributes (description, unit, etc.)
        """
        if self._shutdown_flag:
            return

        try:
            enriched_attrs = self._enrich_attributes(attributes)
            self._executor.submit(
                self._record_metric_safe,
                self._counter_impl,
                name,
                value,
                enriched_attrs,
                **kwargs
            )
        except Exception:
            pass

    def _counter_impl(
            self,
            name: str,
            value: float,
            attributes: Dict[str, Any],
            **kwargs
    ) -> None:
        """Internal counter implementation."""
        if not self._initialized:
            return

        # Build attributes
        attrs = self._build_attributes(attributes, **kwargs)

        # Prepare data for export
        data = {
            "name": name,
            "metric_type": "COUNTER",
            "value": value,
            "timestamp": time.time(),
            "attributes": attrs,
            "service_name": self.service_name
        }

        # Export the metric
        self._export_metric(data)

    def gauge(
            self,
            name: str,
            value: float,
            attributes: Optional[Dict[str, Any]] = None,
            **kwargs
    ) -> None:
        """
        Record a gauge metric (fire and forget).

        Args:
            name: Metric name
            value: Gauge value to set
            attributes: Optional metric attributes/labels
            **kwargs: Additional attributes (description, unit, etc.)
        """
        if self._shutdown_flag:
            return

        try:
            enriched_attrs = self._enrich_attributes(attributes)
            self._executor.submit(
                self._record_metric_safe,
                self._gauge_impl,
                name,
                value,
                enriched_attrs,
                **kwargs
            )
        except Exception:
            pass

    def _gauge_impl(
            self,
            name: str,
            value: float,
            attributes: Dict[str, Any],
            **kwargs
    ) -> None:
        """Internal gauge implementation."""
        if not self._initialized:
            return

        # Build attributes
        attrs = self._build_attributes(attributes, **kwargs)

        # Prepare data for export
        data = {
            "name": name,
            "metric_type": "GAUGE",
            "value": value,
            "timestamp": time.time(),
            "attributes": attrs,
            "service_name": self.service_name
        }

        # Export the metric
        self._export_metric(data)

    def histogram(
            self,
            name: str,
            value: float,
            attributes: Optional[Dict[str, Any]] = None,
            **kwargs
    ) -> None:
        """
        Record a histogram metric (fire and forget).

        Args:
            name: Metric name
            value: Value to record in histogram
            attributes: Optional metric attributes/labels
            **kwargs: Additional attributes (description, unit, etc.)
        """
        if self._shutdown_flag:
            return

        try:
            enriched_attrs = self._enrich_attributes(attributes)
            self._executor.submit(
                self._record_metric_safe,
                self._histogram_impl,
                name,
                value,
                enriched_attrs,
                **kwargs
            )
        except Exception:
            pass

    def _histogram_impl(
            self,
            name: str,
            value: float,
            attributes: Dict[str, Any],
            **kwargs
    ) -> None:
        """Internal histogram implementation."""
        if not self._initialized:
            return

        # Build attributes
        attrs = self._build_attributes(attributes, **kwargs)

        # Prepare data for export
        data = {
            "name": name,
            "metric_type": "HISTOGRAM",
            "value": value,
            "timestamp": time.time(),
            "attributes": attrs,
            "service_name": self.service_name
        }

        # Export the metric
        self._export_metric(data)

    @classmethod
    def _build_attributes(cls, attributes: Optional[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Build metric attributes from provided attributes and kwargs.

        Args:
            attributes: Explicit attributes dict
            **kwargs: Additional keyword arguments

        Returns:
            Combined attributes dictionary
        """
        attrs = {}

        # Add explicit attributes
        if attributes:
            attrs.update(attributes)

        # Add kwargs, excluding internal keys
        for k, v in kwargs.items():
            if k not in cls._EXCLUDED_KEYS:
                attrs[k] = v

        return attrs

    @classmethod
    def set_metrics(
            cls,
            prefix: Optional[str] = None,
            record_counter: bool = True,
            record_gauge: bool = True,
            record_histogram: bool = True,
            extra_attrs: Optional[Dict[str, Any]] = None
    ):
        """
        Decorator for automatic function metrics collection.
        Includes circuit breaker to prevent metric storms.
        """
        extra_attrs = extra_attrs or {}
        _metrics_handler = cls.get_instance()

        def decorator(func: Callable) -> Callable:
            func_name = func.__name__
            module_name = func.__module__

            class_name = "N/A"
            if '.' in func.__qualname__:
                class_name = func.__qualname__.rsplit('.', 1)[0]

            base_attrs = {
                "service_name": getattr(get_config.get(), "service_name","unknown-service-name"),
                "function_name": func_name,
                "class_name": class_name,
                "module_name": module_name,
                **extra_attrs
            }

            def get_metric_name(suffix: str) -> str:
                if prefix:
                    return f"{prefix}.{suffix}"
                return suffix

            counter_name = get_metric_name("function_calls")
            gauge_name = get_metric_name("function_active")
            histogram_name = get_metric_name("function_duration_ms")

            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    start_time = time.perf_counter()

                    if record_counter:
                        _safe_metric_call(_metrics_handler.counter, counter_name, 1.0, base_attrs)

                    if record_gauge:
                        _safe_metric_call(_metrics_handler.gauge, gauge_name, 1.0, base_attrs)

                    try:
                        result = await func(*args, **kwargs)

                        if record_counter:
                            success_attrs = {**base_attrs, "status": "success"}
                            _safe_metric_call(_metrics_handler.counter, get_metric_name("function_success"), 1.0,
                                              success_attrs)

                        return result

                    except Exception as e:
                        if record_counter:
                            error_attrs = {**base_attrs, "status": "error", "error_type": type(e).__name__}
                            _safe_metric_call(_metrics_handler.counter, get_metric_name("function_errors"), 1.0,
                                              error_attrs)
                        raise

                    finally:
                        if record_gauge:
                            _safe_metric_call(_metrics_handler.gauge, gauge_name, 0.0, base_attrs)

                        if record_histogram:
                            duration_ms = (time.perf_counter() - start_time) * 1000
                            _safe_metric_call(_metrics_handler.histogram, histogram_name, duration_ms, base_attrs)

                return async_wrapper

            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    start_time = time.perf_counter()

                    if record_counter:
                        _safe_metric_call(_metrics_handler.counter, counter_name, 1.0, base_attrs)

                    if record_gauge:
                        _safe_metric_call(_metrics_handler.gauge, gauge_name, 1.0, base_attrs)

                    try:
                        result = func(*args, **kwargs)

                        if record_counter:
                            success_attrs = {**base_attrs, "status": "success"}
                            _safe_metric_call(_metrics_handler.counter, get_metric_name("function_success"), 1.0,
                                              success_attrs)

                        return result

                    except Exception as e:
                        if record_counter:
                            error_attrs = {**base_attrs, "status": "error", "error_type": type(e).__name__}
                            _safe_metric_call(_metrics_handler.counter, get_metric_name("function_errors"), 1.0,
                                              error_attrs)
                        raise

                    finally:
                        if record_gauge:
                            _safe_metric_call(_metrics_handler.gauge, gauge_name, 0.0, base_attrs)

                        if record_histogram:
                            duration_ms = (time.perf_counter() - start_time) * 1000
                            _safe_metric_call(_metrics_handler.histogram, histogram_name, duration_ms, base_attrs)

                return sync_wrapper

        return decorator

    def shutdown(self, wait: bool = True, timeout: float = 5.0) -> None:
        """
        Shutdown metrics handler and flush pending metrics.

        Args:
            wait: Whether to wait for pending metrics to complete
            timeout: Maximum time to wait in seconds
        """
        self._shutdown_flag = True

        try:
            # Shutdown thread pool
            if wait:
                self._executor.shutdown(wait=True, cancel_futures=False)
            else:
                self._executor.shutdown(wait=False, cancel_futures=True)
        except Exception as e:
            print(f"[OTEL_METRICS ERROR] Executor shutdown failed: {e}")

        try:
            # Shutdown exporter
            print("[OTEL_METRICS] Shutting down exporter...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._exporter.shutdown())
            loop.close()
            self._initialized = False
        except Exception as e:
            print(f"[OTEL_METRICS ERROR] Exporter shutdown failed: {e}")


class CircuitBreaker:
    """
    Simple circuit breaker for metrics to prevent error storms.
    """

    def __init__(self, failure_threshold: int = 10, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = 0
        self.is_open = False

    def record_success(self):
        """Record successful operation - resets failure count."""
        self.failures = 0
        self.is_open = False

    def record_failure(self):
        """Record failed operation - may open circuit."""
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.is_open = True

    def can_attempt(self) -> bool:
        """Check if operation should be attempted."""
        if not self.is_open:
            return True

        # Check if timeout has passed - attempt to close circuit
        if time.time() - self.last_failure_time > self.timeout:
            self.is_open = False
            self.failures = 0
            return True

        return False


# Shared circuit breaker across all decorated functions
_circuit_breaker = CircuitBreaker(failure_threshold=10, timeout=60.0)


def _safe_metric_call(metric_func, *args, **kwargs):
    """Safely call metric function with circuit breaker."""
    if not _circuit_breaker.can_attempt():
        return  # Circuit open, skip metric

    try:
        metric_func(*args, **kwargs)
        _circuit_breaker.record_success()
    except Exception as e:
        _circuit_breaker.record_failure()
        # Only log occasionally to prevent log spam
        if _circuit_breaker.failures % 10 == 1:
            print(f"[METRICS] Error (failures: {_circuit_breaker.failures}): {e}")