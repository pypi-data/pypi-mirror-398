import threading
import logging
import asyncio
import functools
import time
import inspect
from typing import Optional, Any, Dict, Set, Callable
from queue import Queue, Full
from opentelemetry.sdk.resources import Resource
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler

from ..context_manager import ObservabilityContext
from ..otel_exporter import OTELLogExporter
from ...config.data_config import ServiceConfig
from ...config.factory import get_config

DEFAULT_EXCLUDED = {
    'obs_framework', 'asyncio', 'threading', 'concurrent',
    'logging', 'traceback', 'contextlib'
}


class OTELLogger:
    def __init__(
            self,
            auto_context: Optional[bool] = True,
            include_modules: Optional[list] = None,
            exclude_modules: Optional[list] = None,
    ):
        """
        Initialize the unified logger.
            auto_context: If True, automatically extract caller information
            include_modules: List of module prefixes to include in caller info
            exclude_modules: List of module prefixes to exclude from caller info
        """
        service_config = get_config.get()
        service_config = ServiceConfig(**service_config)
        self.service_name = getattr(service_config, "service_name", "unknown-service-name")
        self.container_logs = getattr(service_config, "container_logs", True)
        self.export_logs = getattr(service_config, "export_logs", True)
        self._auto_context_enabled = auto_context

        # Context and module filtering
        self._context_metadata: Dict[int, Dict[str, Any]] = {}
        self._excluded_modules: Set[str] = set(DEFAULT_EXCLUDED)
        if exclude_modules:
            self._excluded_modules.update(exclude_modules)
        self._include_modules: Set[str] = set(include_modules) if include_modules else set()

        # Background processing for OTEL export only
        self._background_loop: Optional[asyncio.AbstractEventLoop] = None
        self._background_thread: Optional[threading.Thread] = None
        self._queue_thread: Optional[threading.Thread] = None
        self._export_queue: Queue = Queue(maxsize=50000)  # Larger queue for faster processing
        self._shutdown_flag = threading.Event()

        # OTEL components (only if export enabled)
        self._logger: Optional[logging.Logger] = None
        self._logger_provider: Optional[LoggerProvider] = None
        self._exporter: Optional[OTELLogExporter] = None

        # Initialize components
        if self.export_logs:
            self._initialize_otel()
            self._start_background_processing()

    def _initialize_otel(self):
        """Initialize OTEL components for log export."""
        try:
            self._exporter = OTELLogExporter()

            # Create resource with service name
            resource = Resource.create({"service.name": self.service_name})

            # Create logger provider
            self._logger_provider = LoggerProvider(resource=resource)
            set_logger_provider(self._logger_provider)

            # Create logger with handler
            self._logger = logging.getLogger(f"{self.service_name}")
            self._logger.setLevel(logging.DEBUG)

            handler = LoggingHandler(
                level=logging.NOTSET,
                logger_provider=self._logger_provider
            )
            self._logger.addHandler(handler)

        except Exception as e:
            print(f"[LOGGER INIT ERROR] Failed to initialize OTEL: {e}", flush=True)
            self.export_logs = False

    def _get_caller_info(self):
        # frame 0 = this method, frame 1 = public log method, frame 2 = actual caller
        frame = inspect.currentframe()
        caller_frame = frame.f_back.f_back

        function_name = caller_frame.f_code.co_name
        module_name = caller_frame.f_globals.get("__name__", "<unknown>")

        # Optional: detect class name if method is inside a class
        self_obj = caller_frame.f_locals.get("self")
        class_name = self_obj.__class__.__name__ if self_obj else None

        return {
            "function_name": function_name,
            "module_name": module_name,
            "class_name": class_name
        }

    def _start_background_processing(self):
        """Start background event loop and processing threads for OTEL export."""

        def run_loop(loop):
            """Run the event loop in background thread."""
            asyncio.set_event_loop(loop)
            loop.run_forever()

        def process_export_queue():
            """Process OTEL exports from queue in background thread."""
            while not self._shutdown_flag.is_set():
                try:
                    record = self._export_queue.get(timeout=0.05)  # Faster polling
                    if record is not None:
                        # Schedule export in background loop
                        asyncio.run_coroutine_threadsafe(
                            self._export_to_otel(record),
                            self._background_loop
                        )
                except Exception:
                    pass

        # Start background event loop
        self._background_loop = asyncio.new_event_loop()
        self._background_thread = threading.Thread(
            target=run_loop,
            args=(self._background_loop,),
            daemon=True,
            name="Logger-EventLoop"
        )
        self._background_thread.start()

        # Start export queue processor thread (multiple workers for faster processing)
        for i in range(2):  # 2 worker threads for faster export
            queue_thread = threading.Thread(
                target=process_export_queue,
                daemon=True,
                name=f"Logger-ExportWorker-{i}"
            )
            queue_thread.start()
            if i == 0:
                self._queue_thread = queue_thread

    def _should_include_module(self, module_name: str) -> bool:
        """Check if module should be included in caller info."""
        if not module_name:
            return False
        for excluded in self._excluded_modules:
            if module_name.startswith(excluded):
                return False
        if self._include_modules:
            return any(module_name.startswith(included) for included in self._include_modules)
        return True

    def _extract_caller_info(self) -> Dict[str, Any]:
        """Extract caller information from stack."""
        caller_info: Dict[str, Any] = {}
        try:
            for frame_info in inspect.stack()[3:9]:
                module = inspect.getmodule(frame_info.frame)
                module_name = module.__name__ if module else None

                if not module_name or not self._should_include_module(module_name):
                    continue

                caller_info['module_name'] = module_name
                caller_info['function_name'] = frame_info.function
                caller_info['line_no'] = frame_info.lineno
                caller_info['file_path'] = frame_info.filename

                # Extract class name if available
                frame_locals = frame_info.frame.f_locals
                if 'self' in frame_locals:
                    caller_info['class_name'] = frame_locals['self'].__class__.__name__
                elif 'cls' in frame_locals:
                    caller_info['class_name'] = frame_locals['cls'].__name__

                break
        except Exception:
            pass

        return caller_info

    def _build_log_record(self, level: str, message: str, metadata: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Build complete log record with all context from ObservabilityContext."""
        # Get observability context - these IDs come from ObservabilityContext
        trace_id = ObservabilityContext.get_or_create_trace_id()
        span_id = ObservabilityContext.get_or_create_span_id()
        correlation_id = ObservabilityContext.get_or_create_correlation_id()

        # Build record with ObservabilityContext IDs
        record = {
            "timestamp": time.time(),
            "level": level.upper(),
            "message": message,
            "service_name": self.service_name,
            "trace_id": trace_id,
            "span_id": span_id,
            "correlation_id": correlation_id,
        }

        # Add caller info if enabled
        if self._auto_context_enabled:
            caller_info = self._extract_caller_info()
            record.update(caller_info)

        # Add metadata
        if metadata:
            record.update(metadata)

        # Add kwargs
        if kwargs:
            record.update(kwargs)

        return record

    def _shape_by_level(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Shape record based on log level."""
        level = record.get("level", "INFO").upper()

        # Base fields always included
        shaped = {
            "timestamp": record.get("timestamp"),
            "level": level,
            "service_name": self.service_name,
            "trace_id": record.get("trace_id"),
            "span_id": record.get("span_id"),
            "correlation_id": record.get("correlation_id"),
            "message": record.get("message"),
        }

        # Add caller context
        for key in ["module_name", "function_name", "class_name"]:
            if key in record:
                shaped[key] = record[key]

        # Level-specific fields
        if level == "DEBUG":
            for key in ["input", "line_no", "file_path"]:
                if key in record:
                    shaped[key] = record[key]
        elif level in ("ERROR", "CRITICAL"):
            for key in ["input", "line_no", "file_path", "exception"]:
                if key in record:
                    shaped[key] = record[key]

        # Add remaining custom fields
        for k, v in record.items():
            if k not in shaped:
                shaped[k] = v

        return shaped

    def _print_to_container(self, record: Dict[str, Any]):
        """Print log to container stdout INSTANTLY (synchronous)."""
        level = record.get("level", "INFO")
        message = record.get("message", "")
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.get("timestamp", time.time())))

        # Build log line
        log_parts = [f"[{timestamp}]", f"[{level}]", f"[{self.service_name}]"]

        if "function_name" in record:
            log_parts.append(f"[{record['function_name']}]")

        log_parts.append(message)

        # Add exception if present
        if "exception" in record:
            log_parts.append(f"| Exception: {record['exception']}")

        print(" ".join(log_parts), flush=True)

    async def _export_to_otel(self, record: Dict[str, Any]):
        """Export log to OTEL asynchronously."""
        if not self._exporter:
            return

        try:
            await self._exporter.export(record)
        except Exception as e:
            print(f"[OTEL EXPORT ERROR] {e}", flush=True)

    def _schedule_export(self, record: Dict[str, Any]):
        """Schedule log for OTEL export (fire and forget)."""
        if not self.export_logs:
            return

        try:
            self._export_queue.put_nowait(record)
        except Full:
            # Queue full - drop log to maintain performance
            pass
        except Exception:
            pass

    def _log(self, level: str, message: str, metadata: Optional[Dict] = None, **kwargs):
        """Internal logging method with instant console output."""
        try:
            # Build and shape the log record
            base = self._build_log_record(level, message, metadata, **kwargs)
            shaped = self._shape_by_level(base)

            # INSTANT console output (synchronous - happens immediately)
            if self.container_logs:
                self._print_to_container(shaped)

            # Queue for async OTEL export (fire and forget)
            self._schedule_export(shaped)

        except Exception:
            # Never let logging break the application
            pass

    # Public sync logging methods (instant console, async export)
    def info(self, *message_parts, **kwargs):
        message = " ".join(str(p) for p in message_parts)
        metadata = self._get_caller_info()
        self._log("INFO", message, metadata, **kwargs)

    def warning(self, *message_parts, **kwargs):
        message = " ".join(str(p) for p in message_parts)
        metadata = self._get_caller_info()
        self._log("WARNING", message, metadata, **kwargs)

    def error(self, *message_parts, exception: Optional[Exception] = None, **kwargs):
        message = " ".join(str(p) for p in message_parts)
        metadata = self._get_caller_info()
        if exception:
            kwargs['exception'] = repr(exception)
        self._log("ERROR", message, metadata, **kwargs)

    def debug(self, *message_parts, **kwargs):
        message = " ".join(str(p) for p in message_parts)
        metadata = self._get_caller_info()
        self._log("DEBUG", message, metadata, **kwargs)

    def critical(self, *message_parts, exception: Optional[Exception] = None, **kwargs):
        """Log critical message with instant console output."""
        message = " ".join(str(p) for p in message_parts)
        metadata = self._get_caller_info()
        if exception:
            kwargs['exception'] = repr(exception)
        self._log("CRITICAL", message, metadata, **kwargs)

    @classmethod
    def set_logger(
            cls,
            level: str = "INFO",
            log_input: bool = True,
            log_output: bool = True,
            log_execution_time: bool = True,
            log_exceptions: bool = True,
            input_sanitizer: Optional[Callable] = None,
            output_sanitizer: Optional[Callable] = None,
            function_name: Optional[str] = None,
            module_name: Optional[str] = None
    ):
        # Validate and normalize log level
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        normalized_level = level.upper()
        if normalized_level not in valid_levels:
            raise ValueError(f"Invalid log level: {level}. Must be one of {valid_levels}")

        def decorator(func: Callable) -> Callable:
            _func_name = function_name if function_name is not None else func.__name__
            _module_name = module_name if module_name is not None else func.__module__
            is_async = asyncio.iscoroutinefunction(func)
            logger = cls()

            # Get the appropriate log method based on level
            log_method = getattr(logger, normalized_level.lower())

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                trace_id = ObservabilityContext.get_trace_id()
                span_id = ObservabilityContext.get_span_id()
                correlation_id = ObservabilityContext.get_correlation_id()

                start_time = time.time()

                # Capture input data
                input_data = {}
                if log_input:
                    try:
                        sig = inspect.signature(func)
                        bound_args = sig.bind(*args, **kwargs)
                        bound_args.apply_defaults()

                        raw_input = dict(bound_args.arguments)
                        input_data = input_sanitizer(raw_input) if input_sanitizer else raw_input
                    except Exception:
                        pass

                # Log function start with specified level
                try:
                    log_method(
                        {
                            "function_name": _func_name,
                            "module_name": _module_name,
                            "input": input_data if log_input else None,
                            "trace_id": trace_id,
                            "span_id": span_id,
                            "correlation_id": correlation_id
                        },
                        f"Function '{_func_name}' started",
                    )
                except Exception:
                    pass

                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    # Capture output data
                    output_data = {}
                    if log_output:
                        try:
                            output_data = output_sanitizer(result) if output_sanitizer else result
                        except Exception:
                            pass

                    # Log success with specified level
                    try:
                        log_method(
                            {
                                "function_name": _func_name,
                                "module_name": _module_name,
                                "output": output_data if log_output else None,
                                "execution_time_seconds": round(execution_time, 4) if log_execution_time else None,
                                "status": "success",
                                "trace_id": trace_id,
                                "span_id": span_id,
                                "correlation_id": correlation_id
                            },
                            f"Function '{_func_name}' completed successfully"
                        )
                    except Exception:
                        pass

                    return result

                except Exception as e:
                    execution_time = time.time() - start_time

                    if log_exceptions:
                        try:
                            logger.error(
                                {
                                    "function_name": _func_name,
                                    "module_name": _module_name,
                                    "exception_type": type(e).__name__,
                                    "exception_message": str(e),
                                    "execution_time_seconds": round(execution_time, 4) if log_execution_time else None,
                                    "status": "error",
                                    "trace_id": trace_id,
                                    "span_id": span_id,
                                    "correlation_id": correlation_id,
                                    "input": input_data,
                                },
                                f"Function '{_func_name}' failed with exception. \n Input Data: {input_data}",
                                exception=e
                            )
                        except Exception:
                            pass

                    raise

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                logger = cls()
                trace_id = ObservabilityContext.get_trace_id()
                span_id = ObservabilityContext.get_span_id()
                correlation_id = ObservabilityContext.get_correlation_id()

                start_time = time.time()

                # Capture input data
                input_data = {}
                if log_input:
                    try:
                        sig = inspect.signature(func)
                        bound_args = sig.bind(*args, **kwargs)
                        bound_args.apply_defaults()

                        raw_input = dict(bound_args.arguments)
                        input_data = input_sanitizer(raw_input) if input_sanitizer else raw_input
                    except Exception:
                        pass

                # Log function start with specified level
                try:
                    log_method(
                        {
                            "function_name": _func_name,
                            "module_name": _module_name,
                            "input": input_data if log_input else None,
                            "trace_id": trace_id,
                            "span_id": span_id,
                            "correlation_id": correlation_id
                        },
                        f"Function '{_func_name}' started. \n Input: {input_data}"
                    )
                except Exception:
                    pass

                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    # Capture output data
                    output_data = {}
                    if log_output:
                        try:
                            output_data = output_sanitizer(result) if output_sanitizer else result
                        except Exception:
                            pass

                    # Log success with specified level
                    try:
                        log_method(
                            {
                                "function_name": _func_name,
                                "module_name": _module_name,
                                "output": output_data if log_output else None,
                                "execution_time_seconds": round(execution_time, 4) if log_execution_time else None,
                                "status": "success",
                                "trace_id": trace_id,
                                "span_id": span_id,
                                "correlation_id": correlation_id,
                            },
                            f"Function '{_func_name}' completed.",
                        )
                    except Exception:
                        pass

                    return result

                except Exception as e:
                    execution_time = time.time() - start_time

                    if log_exceptions:
                        try:
                            logger.error(
                                {
                                    "function_name": _func_name,
                                    "module_name": _module_name,
                                    "exception_type": type(e).__name__,
                                    "exception_message": str(e),
                                    "execution_time_seconds": round(execution_time, 4) if log_execution_time else None,
                                    "status": "error",
                                    "trace_id": trace_id,
                                    "span_id": span_id,
                                    "correlation_id": correlation_id
                                },
                                f"Function '{_func_name}' failed with exception",
                                exception=e
                            )
                        except Exception:
                            pass

                    raise

            return async_wrapper if is_async else sync_wrapper

        return decorator

    def shutdown(self, timeout: float = 5.0):
        """Shutdown logger and flush pending exports."""
        self._shutdown_flag.set()

        # Wait for export queue to drain
        start = time.time()
        while not self._export_queue.empty() and (time.time() - start) < timeout:
            time.sleep(0.1)

        # Stop event loop
        if self._background_loop and not self._background_loop.is_closed():
            self._background_loop.call_soon_threadsafe(self._background_loop.stop)

        # Wait for threads to finish
        if self._background_thread and self._background_thread.is_alive():
            self._background_thread.join(timeout=2)
        if self._queue_thread and self._queue_thread.is_alive():
            self._queue_thread.join(timeout=2)

        # Shutdown OTEL components
        if self._logger_provider:
            try:
                self._logger_provider.shutdown()
            except Exception:
                pass