"""
Web Framework Factory

This module provides a factory for creating web framework wrappers with automatic
initialization from environment variables.
"""

import os
from typing import Optional, Union
from ..utils.singleton import singleton


@singleton
def get_web_framework(
    framework: Optional[str] = None,
    app: Optional[Union['Flask', 'FastAPI']] = None,
    service: Optional[str] = None,
    auto_initialize: bool = True
):
    """
    Get a web framework wrapper instance.

    This factory supports both Flask and FastAPI frameworks with automatic
    initialization from environment variables.

    Args:
        framework: Framework type ('flask' or 'fastapi'). If None, reads from WEB_FRAMEWORK env var
        app: Framework application instance. If None, creates a new instance
        service: Service name for observability. If None, reads from SERVICE_NAME env var
        auto_initialize: If True, automatically calls initialize() on the wrapper

    Returns:
        WebFrameworkWrapper instance (FlaskWrapper or FastAPIWrapper)

    Environment Variables:
        WEB_FRAMEWORK: Framework type (flask/fastapi) - defaults to 'flask'
        SERVICE_NAME: Service name for observability - defaults to 'unknown-service'
        FLASK_ENV: Flask environment (for Flask apps)
        FASTAPI_ENV: FastAPI environment (for FastAPI apps)

    Examples:
        # Automatic initialization from environment
        >>> web_framework = get_web_framework.get()

        # With explicit framework and app
        >>> from flask import Flask
        >>> app = Flask(__name__)
        >>> web_framework = get_web_framework.get(framework='flask', app=app, service='my-service')

        # With FastAPI
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> web_framework = get_web_framework.get(framework='fastapi', app=app, service='my-api')

    Raises:
        ValueError: If framework type is invalid or app creation fails
    """
    # Get framework type from parameter or environment
    if framework is None:
        framework = os.getenv('WEB_FRAMEWORK', 'flask').lower()

    # Get service name from parameter or environment
    if service is None:
        service = os.getenv('SERVICE_NAME', 'unknown-service')

    # Validate framework type
    if framework not in ['flask', 'fastapi']:
        raise ValueError(f"Unknown framework type: {framework}. Must be 'flask' or 'fastapi'")

    # Create or use provided app instance
    if app is None:
        app = _create_app(framework, service)

    # Create appropriate wrapper
    if framework == 'flask':
        from .flask_wrapper import FlaskWrapper
        wrapper = FlaskWrapper(app, service)
    elif framework == 'fastapi':
        from .fastapi_wrapper import FastAPIWrapper
        wrapper = FastAPIWrapper(app, service)
    else:
        raise ValueError(f"Unsupported framework: {framework}")

    # Auto-initialize if requested
    if auto_initialize:
        wrapper.initialize()

    return wrapper


def _create_app(framework: str, service: str):
    """
    Create a new application instance for the specified framework.

    Args:
        framework: Framework type ('flask' or 'fastapi')
        service: Service name

    Returns:
        Application instance

    Raises:
        ValueError: If framework is not supported
        ImportError: If required framework package is not installed
    """
    if framework == 'flask':
        try:
            from flask import Flask
            app = Flask(service)

            # Configure Flask from environment
            flask_env = os.getenv('FLASK_ENV', 'production')
            app.config['ENV'] = flask_env
            app.config['DEBUG'] = flask_env == 'development'
            app.config['TESTING'] = flask_env == 'testing'

            return app

        except ImportError as e:
            raise ImportError(
                "Flask is not installed. Install it with: pip install Flask"
            ) from e

    elif framework == 'fastapi':
        try:
            from fastapi import FastAPI

            # Configure FastAPI from environment
            fastapi_env = os.getenv('FASTAPI_ENV', 'production')
            debug = fastapi_env == 'development'

            app = FastAPI(
                title=service,
                debug=debug,
                docs_url="/docs" if debug else None,
                redoc_url="/redoc" if debug else None,
            )

            return app

        except ImportError as e:
            raise ImportError(
                "FastAPI is not installed. Install it with: pip install fastapi uvicorn"
            ) from e

    else:
        raise ValueError(f"Unsupported framework: {framework}")


def create_app(
    framework: Optional[str] = None,
    service: Optional[str] = None,
    **config
):
    """
    Convenience function to create and initialize a web application.

    This is a higher-level function that combines app creation and wrapper initialization.

    Args:
        framework: Framework type ('flask' or 'fastapi')
        service: Service name
        **config: Additional configuration parameters

    Returns:
        Tuple of (app, wrapper) where app is the framework instance and wrapper is the WebFrameworkWrapper

    Example:
        >>> app, wrapper = create_app(framework='fastapi', service='my-api')
        >>> # app is ready to use with all middleware and error handlers configured
    """
    wrapper = get_web_framework.get(
        framework=framework,
        service=service,
        auto_initialize=True
    )

    return wrapper.app, wrapper