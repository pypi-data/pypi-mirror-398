import logging
import time
from contextlib import ContextDecorator
from functools import wraps
from typing import Any, Callable, Optional


class Timer(ContextDecorator):
    """Context manager and decorator for measuring execution time.

    Example as context manager:

        with Timer("sleep", logger=my_logger):
            time.sleep(1)

    Example as decorator:

        @Timer("expensive_call")
        def my_function():
            ...
    """

    def __init__(self, label: str, logger: Optional[logging.Logger] = None) -> None:
        self.label = label
        self.logger = logger
        self.start: float = 0.0
        self.duration: float = 0.0

    def __enter__(self) -> "Timer":
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.duration = time.perf_counter() - self.start
        if self.logger:
            self.logger.info("%s took %.4f seconds", self.label, self.duration)


def time_function(label: Optional[str] = None, logger: Optional[logging.Logger] = None) -> Callable:
    """Decorator that measures the runtime of a function.

    Parameters
    ----------
    label:
        Optional label to use. If omitted, the function name is used.
    logger:
        Logger to use for reporting. If None, the standard library `logging` root
        logger is used.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            effective_label = label or func.__name__
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                active_logger = logger or logging.getLogger(__name__)
                active_logger.info("%s took %.4f seconds", effective_label, duration)

        return wrapper

    return decorator
