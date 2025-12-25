"""
ND-SDK - Unified Framework for Observability, Storage & Caching

This SDK provides a comprehensive set of tools for building enterprise microservices
with built-in observability, caching, storage, and exception handling.
"""

# Core factories
from .storage.factory import get_storage
from .caching.factory import get_cache
from .observability.factory import get_logger, get_tracer, get_metrics
from .exception_handler.factory import get_exception_handler

# Web framework factory
from .web.factory import get_web_framework, create_app

# Auto-initialization
from .auto_init import (
    initialize_sdk,
    get_initialized_component,
    get_all_initialized_components
)

__version__ = "1.3.0"

__all__ = [
    # Core factories
    "get_logger",
    "get_tracer",
    "get_metrics",
    "get_storage",
    "get_cache",
    "get_exception_handler",

    # Web framework
    "get_web_framework",
    "create_app",

    # Auto-initialization
    "initialize_sdk",
    "get_initialized_component",
    "get_all_initialized_components",
]