"""
Auto-Initialization Module

This module provides automatic initialization of all SDK components from environment variables.
It ensures that all singleton factories are properly initialized before the application starts.
"""

import os
import traceback
from typing import Dict, Any, Optional

from nd_sdk.utils.singleton import singleton


class AutoInitializer:
    """
    Handles automatic initialization of SDK components from environment variables.

    This class reads environment configuration and initializes all SDK singletons
    including logging, caching, storage, exception handling, metrics, and tracing.
    """

    def __init__(self):
        self.initialized = False
        self.components: Dict[str, Any] = {}
        self.errors: Dict[str, Exception] = {}

    def initialize_all(
        self,
        force: bool = False,
        components: Optional[list] = None
    ) -> Dict[str, bool]:
        """
        Initialize all SDK components from environment variables.

        Args:
            force: Force re-initialization even if already initialized
            components: List of specific components to initialize. If None, initializes all.
                       Options: ['logger', 'cache', 'storage', 'exception_handler', 'tracer', 'metrics', 'web']

        Returns:
            Dictionary mapping component names to initialization success status

        Environment Variables:
            # Logging
            LOG_PROVIDER: Logging provider (std/cloudwatch/otel) - default: 'std'
            LOG_LEVEL: Logging level - default: 'INFO'

            # Caching
            CACHE_PROVIDER: Cache provider (redis/memory) - default: 'redis'
            CACHE_ENVIRONMENT: Cache environment prefix - default: 'dev'
            CACHE_HOST: Redis host - default: 'localhost'
            CACHE_PORT: Redis port - default: 6379

            # Storage
            STORAGE_PROVIDER: Storage provider (awss3/azureblob/minio) - optional
            STORAGE_ENABLED: Enable storage initialization - default: false

            # Exception Handler
            EXCEPTION_HANDLER_PROVIDER: Exception handler provider - default: 'idp'

            # Observability
            TRACER_PROVIDER: Tracer provider - default: 'otel'
            METRICS_PROVIDER: Metrics provider - default: 'otel'
            OTEL_ENABLED: Enable OpenTelemetry - default: true

            # Web Framework
            WEB_FRAMEWORK: Web framework (flask/fastapi) - default: 'flask'
            SERVICE_NAME: Service name - default: 'unknown-service'
        """
        if self.initialized and not force:
            return {k: True for k in self.components.keys()}

        # Determine which components to initialize
        if components is None:
            components = [
                'service_config', 'logger', 'cache', 'exception_handler',
                'tracer', 'metrics', 'storage', 'web',
            ]

        results = {}

        # Initialize each component
        for component in components:
            try:
                method = getattr(self, f'_initialize_{component}', None)
                if method:
                    self.components[component] = method()
                    results[component] = True
                else:
                    print(f"Warning: No initialization method for component: {component}", flush=True)
                    results[component] = False
            except Exception as e:
                # FIXED: Use traceback.format_exc() without arguments
                print(traceback.format_exc(), flush=True)
                print(f"Error initializing {component}: {e}", flush=True)
                self.errors[component] = e
                results[component] = False

        self.initialized = True
        return results

    def _initialize_logger(self):
        """Initialize logger from environment variables."""
        from .observability.factory import get_logger

        provider = os.getenv('LOG_PROVIDER', 'std')
        logger = get_logger.init(provider=provider)

        # Set log level if specified
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        if hasattr(logger, 'set_level'):
            logger.set_level(log_level)

        logger.info(f"Logger initialized with provider: {provider}")
        return logger

    def _initialize_cache(self):
        """Initialize cache from environment variables."""
        from .caching.factory import get_cache

        provider = os.getenv('CACHE_PROVIDER', 'redis')
        environ = os.getenv('CACHE_ENVIRONMENT', 'dev')

        cache = get_cache.init(provider=provider, environ=environ)

        # Get logger to log cache initialization
        if 'logger' in self.components:
            self.components['logger'].info(
                f"Cache initialized with provider: {provider}, environment: {environ}"
            )

        return cache

    def _initialize_service_config(self):
        from .config.factory import get_config
        config = get_config.init(config_data={}, provider="yaml")
        print(f"Service config initialized with provider: service, environment: yaml, {config}", flush=True)
        print(get_config.get(), flush=True)
        return config

    def _initialize_storage(self):
        """Initialize storage from environment variables."""
        storage_enabled = os.getenv('STORAGE_ENABLED', 'false').lower() == 'true'

        if not storage_enabled:
            if 'logger' in self.components:
                self.components['logger'].info("Storage initialization skipped (STORAGE_ENABLED=false)")
            return None

        from .storage.factory import get_storage

        storage = get_storage.init()

        if 'logger' in self.components:
            self.components['logger'].info("Storage initialized")

        return storage

    def _initialize_exception_handler(self):
        """Initialize exception handler from environment variables."""
        from .exception_handler.factory import get_exception_handler

        provider = os.getenv('EXCEPTION_HANDLER_PROVIDER', 'idp')
        exception_handler = get_exception_handler.init(provider=provider)

        if 'logger' in self.components:
            self.components['logger'].info(f"Exception handler initialized with provider: {provider}")

        return exception_handler

    def _initialize_tracer(self):
        """Initialize tracer from environment variables."""
        otel_enabled = os.getenv('OTEL_ENABLED', 'true').lower() == 'true'

        if not otel_enabled:
            if 'logger' in self.components:
                self.components['logger'].info("Tracer initialization skipped (OTEL_ENABLED=false)")
            return None

        try:
            from .observability.factory import get_tracer

            provider = os.getenv('TRACER_PROVIDER', 'otel')
            tracer = get_tracer.init(provider=provider)

            if 'logger' in self.components:
                self.components['logger'].info(f"Tracer initialized with provider: {provider}")

            return tracer
        except Exception as e:
            if 'logger' in self.components:
                self.components['logger'].warning(f"Tracer initialization failed: {e}")
            return None

    def _initialize_metrics(self):
        """Initialize metrics from environment variables."""
        otel_enabled = os.getenv('OTEL_ENABLED', 'true').lower() == 'true'

        if not otel_enabled:
            if 'logger' in self.components:
                self.components['logger'].info("Metrics initialization skipped (OTEL_ENABLED=false)")
            return None

        try:
            from .observability.factory import get_metrics

            provider = os.getenv('METRICS_PROVIDER', 'otel')
            metrics = get_metrics.init(provider=provider)

            if 'logger' in self.components:
                self.components['logger'].info(f"Metrics initialized with provider: {provider}")

            return metrics
        except Exception as e:
            if 'logger' in self.components:
                self.components['logger'].warning(f"Metrics initialization failed: {e}")
            return None

    def _initialize_web(self):
        """Initialize web framework from environment variables."""
        web_enabled = os.getenv('WEB_FRAMEWORK_ENABLED', 'true').lower() == 'true'

        if not web_enabled:
            if 'logger' in self.components:
                self.components['logger'].info("Web framework initialization skipped")
            return None

        try:
            from .web.factory import get_web_framework

            framework = os.getenv('WEB_FRAMEWORK', 'flask')
            service = os.getenv('SERVICE_NAME', 'unknown-service')

            web = get_web_framework.init(
                framework=framework,
                service=service,
                auto_initialize=True
            )

            if 'logger' in self.components:
                self.components['logger'].info(
                    f"Web framework initialized: {framework}, service: {service}"
                )

            return web
        except Exception as e:
            if 'logger' in self.components:
                self.components['logger'].warning(f"Web framework initialization failed: {e}")
            return None

    def get_component(self, component: str) -> Any:
        """
        Get an initialized component.

        Args:
            component: Component name

        Returns:
            Component instance or None if not initialized

        Raises:
            KeyError: If component doesn't exist
        """
        if component in self.errors:
            raise self.errors[component]

        return self.components.get(component)

    def get_all_components(self) -> Dict[str, Any]:
        """
        Get all initialized components.

        Returns:
            Dictionary of all initialized components
        """
        return self.components.copy()

    def print_status(self):
        """Print initialization status of all components."""
        print("\n" + "="*60, flush=True)
        print("SDK Auto-Initialization Status", flush=True)
        print("="*60, flush=True)

        for component, instance in self.components.items():
            status = "✓ Initialized" if instance is not None else "⚠ Skipped"
            print(f"{component:20s}: {status}", flush=True)

        if self.errors:
            print("\nErrors:", flush=True)
            for component, error in self.errors.items():
                print(f"{component:20s}: ✗ {error}", flush=True)

        print("="*60 + "\n", flush=True)


# Global singleton instance
_auto_initializer = AutoInitializer()

@singleton
def initialize_sdk(
    force: bool = False,
    components: Optional[list] = None,
    print_status: bool = True
) -> Dict[str, bool]:
    """
    Initialize SDK components from environment variables.

    This is the main entry point for auto-initialization.

    Args:
        force: Force re-initialization
        components: Specific components to initialize
        print_status: Print initialization status

    Returns:
        Dictionary mapping component names to success status

    Example:
        >>> from nd_sdk import initialize_sdk
        >>> results = initialize_sdk()
        >>> # All components are now initialized and ready to use
    """
    results = _auto_initializer.initialize_all(force=force, components=components)

    if print_status:
        _auto_initializer.print_status()

    return results


def get_initialized_component(component: str) -> Any:
    """
    Get an initialized component.

    Args:
        component: Component name

    Returns:
        Component instance

    Example:
        >>> logger = get_initialized_component('logger')
    """
    return _auto_initializer.get_component(component)


def get_all_initialized_components() -> Dict[str, Any]:
    """
    Get all initialized components.

    Returns:
        Dictionary of all initialized components
    """
    return _auto_initializer.get_all_components()