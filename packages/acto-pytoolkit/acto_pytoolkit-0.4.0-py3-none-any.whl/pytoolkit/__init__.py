"""Top level package for pytoolkit.

The package exposes selected helpers directly for convenience.
"""

from . import context_utils, serialization
from .cache import SimpleCache, cached
from .config_loader import ConfigLoader
from .http_client import HttpClient
from .logger import configure_from_env, get_logger
from .timer import Timer, time_function

# Async module is optional (requires aiohttp)
try:
    from .async_http_client import AsyncHttpClient

    __all__ = [
        "AsyncHttpClient",
        "ConfigLoader",
        "HttpClient",
        "SimpleCache",
        "Timer",
        "cached",
        "configure_from_env",
        "context_utils",
        "get_logger",
        "serialization",
        "time_function",
    ]
except ImportError:
    __all__ = [
        "ConfigLoader",
        "HttpClient",
        "SimpleCache",
        "Timer",
        "cached",
        "configure_from_env",
        "context_utils",
        "get_logger",
        "serialization",
        "time_function",
    ]
