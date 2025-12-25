import traceback
import time
from typing import Optional, Callable
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from .base import WebFrameworkWrapper
from ..observability.factory import get_logger, get_tracer, get_metrics
from ..utils.string_utils import to_snake_case


class FastAPIWrapper(WebFrameworkWrapper):
    """
    FastAPI framework wrapper with integrated observability.
    Provides automatic logging, tracing, and metrics for FastAPI applications.
    """

    def __init__(self, app: FastAPI, service: str):
        """
        Initialize FastAPI wrapper.

        Args:
            app: FastAPI application instance
            service: Service name for observability
        """
        self.app = app
        self.service = service
        self.logger = get_logger.get()
        self.tracer = None
        self.metrics = None

        # Try to initialize tracer and metrics if available
        try:
            self.tracer = get_tracer.get()
        except Exception as e:
            self.logger.warning(f"Tracer not available: {e}")

        try:
            self.metrics = get_metrics.get()
        except Exception as e:
            self.logger.warning(f"Metrics not available: {e}")

    def initialize(self):
        """Initialize all FastAPI middleware and handlers."""
        self.register_middlewares()
        self.register_error_handlers()
        self.register_health_check()
        self.logger.info(f"FastAPIWrapper initialized for service: {self.service}")

    def register_health_check(self):
        """Register health check endpoint."""
        @self.app.get(f"/{to_snake_case(self.service)}/health_check")
        @self.app.get(f"/health")
        async def health_check():
            return {
                "status": "healthy",
                "service": self.service,
                "timestamp": time.time()
            }

    def register_middlewares(self):
        """Register request/response middleware for observability."""

        class ObservabilityMiddleware(BaseHTTPMiddleware):
            def __init__(self, app, wrapper: 'FastAPIWrapper'):
                super().__init__(app)
                self.wrapper = wrapper

            async def dispatch(self, request: Request, call_next: Callable):
                start_time = time.time()

                # Extract request info
                path = request.url.path
                method = request.method
                client_ip = request.client.host if request.client else "unknown"

                # Log incoming request
                self.wrapper.logger.info({
                    "event": "request_started",
                    "method": method,
                    "path": path,
                    "client_ip": client_ip
                })

                # Start tracing span if available
                span = None
                if self.wrapper.tracer:
                    try:
                        span = self.wrapper.tracer.start_span(f"{method} {path}")
                        span.set_attribute("http.method", method)
                        span.set_attribute("http.url", str(request.url))
                        span.set_attribute("http.client_ip", client_ip)
                    except Exception as e:
                        self.wrapper.logger.warning(f"Failed to start tracing span: {e}")

                # Process request
                try:
                    response = await call_next(request)
                    status_code = response.status_code

                    # Record metrics
                    if self.wrapper.metrics:
                        try:
                            self.wrapper.metrics.increment(
                                "http_requests_total",
                                {"method": method, "path": path, "status": status_code}
                            )
                        except Exception as e:
                            self.wrapper.logger.warning(f"Failed to record metrics: {e}")

                    # Log response
                    duration = time.time() - start_time
                    self.wrapper.logger.info({
                        "event": "request_completed",
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                        "duration_ms": round(duration * 1000, 2)
                    })

                    # Add response headers
                    response.headers["X-Request-Duration"] = str(duration)
                    response.headers["X-Service-Name"] = self.wrapper.service

                    return response

                except Exception as e:
                    # Log error
                    duration = time.time() - start_time
                    self.wrapper.logger.error({
                        "event": "request_failed",
                        "method": method,
                        "path": path,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "duration_ms": round(duration * 1000, 2)
                    })

                    if span:
                        span.set_attribute("error", True)
                        span.set_attribute("error.message", str(e))

                    raise

                finally:
                    # End tracing span
                    if span:
                        try:
                            self.wrapper.tracer.end_span(span)
                        except Exception as e:
                            self.wrapper.logger.warning(f"Failed to end tracing span: {e}")

        # Add middleware to app
        self.app.add_middleware(ObservabilityMiddleware, wrapper=self)

    def register_error_handlers(self):
        """Register global error handlers."""

        @self.app.exception_handler(StarletteHTTPException)
        async def http_exception_handler(request: Request, exc: StarletteHTTPException):
            """Handle HTTP exceptions."""
            self.logger.warning({
                "event": "http_exception",
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
                "detail": exc.detail
            })

            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "message": exc.detail,
                        "type": "HTTPException",
                        "status_code": exc.status_code
                    }
                }
            )

        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            """Handle request validation errors."""
            self.logger.warning({
                "event": "validation_error",
                "path": request.url.path,
                "method": request.method,
                "errors": exc.errors()
            })

            return JSONResponse(
                status_code=422,
                content={
                    "error": {
                        "message": "Request validation failed",
                        "type": "ValidationError",
                        "status_code": 422,
                        "details": exc.errors()
                    }
                }
            )

        @self.app.exception_handler(Exception)
        async def generic_exception_handler(request: Request, exc: Exception):
            """Handle all other exceptions."""
            self.logger.error({
                "event": "unhandled_exception",
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown",
                "error": str(exc),
                "error_type": type(exc).__name__,
                "traceback": traceback.format_exc()
            })

            # Get status code if available
            status_code = getattr(exc, 'status_code', 500)

            return JSONResponse(
                status_code=status_code,
                content={
                    "error": {
                        "message": str(exc),
                        "type": type(exc).__name__,
                        "status_code": status_code
                    }
                }
            )