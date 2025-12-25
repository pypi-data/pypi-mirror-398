import traceback
import time
from functools import wraps
from typing import Optional

from flask import Flask, request, jsonify, g
from .base import WebFrameworkWrapper
from ..observability.factory import get_logger, get_tracer, get_metrics
from ..utils.string_utils import to_snake_case


class FlaskWrapper(WebFrameworkWrapper):
    """
    Flask framework wrapper with integrated observability.
    Provides automatic logging, tracing, and metrics for Flask applications.
    """

    def __init__(self, app: Flask, service: str):
        """
        Initialize Flask wrapper.

        Args:
            app: Flask application instance
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
        """Initialize all Flask middleware and handlers."""
        self.register_middlewares()
        self.register_error_handlers()
        self.register_health_check()
        self.logger.info(f"FlaskWrapper initialized for service: {self.service}")

    def register_health_check(self):
        """Register health check endpoint."""
        @self.app.route(f"/{to_snake_case(self.service)}/health_check")
        @self.app.route(f"/health")
        def health_check():
            return jsonify({
                "status": "healthy",
                "service": self.service,
                "timestamp": time.time()
            })

    def register_middlewares(self):
        """Register before/after request handlers for observability."""

        @self.app.before_request
        def before_request():
            """Log incoming requests and start tracing."""
            g.start_time = time.time()

            # Extract request info
            path = request.path
            method = request.method
            client_ip = request.remote_addr or "unknown"

            # Log incoming request
            self.logger.info({
                "event": "request_started",
                "method": method,
                "path": path,
                "client_ip": client_ip
            })

            # Start tracing span if available
            if self.tracer:
                try:
                    span = self.tracer.start_span(f"{method} {path}")
                    span.set_attribute("http.method", method)
                    span.set_attribute("http.url", request.url)
                    span.set_attribute("http.client_ip", client_ip)
                    g.span = span
                except Exception as e:
                    self.logger.warning(f"Failed to start tracing span: {e}")

        @self.app.after_request
        def after_request(response):
            """Log response and record metrics."""
            # Calculate duration
            duration = time.time() - g.get('start_time', time.time())

            # Extract request info
            path = request.path
            method = request.method
            status_code = response.status_code

            # Log response
            self.logger.info({
                "event": "request_completed",
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration * 1000, 2)
            })

            # Record metrics if available
            if self.metrics:
                try:
                    self.metrics.increment(
                        "http_requests_total",
                        {"method": method, "path": path, "status": status_code}
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to record metrics: {e}")

            # End tracing span if available
            if hasattr(g, 'span') and self.tracer:
                try:
                    g.span.set_attribute("http.status_code", status_code)
                    self.tracer.end_span(g.span)
                except Exception as e:
                    self.logger.warning(f"Failed to end tracing span: {e}")

            # Add response headers
            response.headers["X-Request-Duration"] = str(duration)
            response.headers["X-Service-Name"] = self.service

            return response

        @self.app.teardown_request
        def teardown_request(exception=None):
            """Clean up resources and handle errors."""
            if exception:
                self.logger.error({
                    "event": "request_teardown_error",
                    "path": request.path,
                    "method": request.method,
                    "error": str(exception),
                    "error_type": type(exception).__name__
                })

                # Mark span as error if available
                if hasattr(g, 'span'):
                    try:
                        g.span.set_attribute("error", True)
                        g.span.set_attribute("error.message", str(exception))
                    except Exception:
                        pass

    def register_error_handlers(self):
        """Register global error handlers."""

        @self.app.errorhandler(400)
        def bad_request_handler(e):
            """Handle bad request errors."""
            self.logger.warning({
                "event": "bad_request",
                "path": request.path,
                "method": request.method,
                "error": str(e)
            })

            return jsonify({
                "error": {
                    "message": str(e),
                    "type": "BadRequest",
                    "status_code": 400
                }
            }), 400

        @self.app.errorhandler(404)
        def not_found_handler(e):
            """Handle not found errors."""
            self.logger.warning({
                "event": "not_found",
                "path": request.path,
                "method": request.method
            })

            return jsonify({
                "error": {
                    "message": "Resource not found",
                    "type": "NotFound",
                    "status_code": 404
                }
            }), 404

        @self.app.errorhandler(500)
        def internal_error_handler(e):
            """Handle internal server errors."""
            self.logger.error({
                "event": "internal_server_error",
                "path": request.path,
                "method": request.method,
                "error": str(e),
                "traceback": traceback.format_exc()
            })

            return jsonify({
                "error": {
                    "message": "Internal server error",
                    "type": "InternalServerError",
                    "status_code": 500
                }
            }), 500

        @self.app.errorhandler(Exception)
        def handle_exception(e):
            """Handle all other exceptions."""
            self.logger.error({
                "event": "unhandled_exception",
                "path": request.path,
                "method": request.method,
                "client_ip": request.remote_addr or "unknown",
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            })

            # Get status code if available
            status_code = getattr(e, 'code', 500)

            return jsonify({
                "error": {
                    "message": str(e),
                    "type": type(e).__name__,
                    "status_code": status_code
                }
            }), status_code