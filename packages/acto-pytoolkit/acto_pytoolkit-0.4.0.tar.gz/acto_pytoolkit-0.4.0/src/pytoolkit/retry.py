import logging
import random
import time
from collections.abc import Iterable
from functools import wraps
from typing import Any, Callable, Optional


def retry(
    exceptions: Iterable[type[BaseException]] = (Exception,),
    max_attempts: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    max_delay: Optional[float] = None,
    jitter: float = 0.1,
    logger: Optional[logging.Logger] = None,
) -> Callable:
    """Retry decorator with exponential backoff and optional jitter.

    Parameters
    ----------
    exceptions:
        Iterable of exception types to catch and retry.
    max_attempts:
        Maximum number of attempts including the first attempt.
    initial_delay:
        Initial delay in seconds before the first retry.
    backoff_factor:
        Factor used to increase the delay for each attempt.
    max_delay:
        Optional maximum delay between retries.
    jitter:
        Random jitter factor in seconds added or subtracted from the delay.
    logger:
        Optional logger for messages. If not provided, the module logger is used.
    """

    exc_tuple: tuple[type[BaseException], ...] = tuple(exceptions)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            log = logger or logging.getLogger(func.__module__)
            delay = initial_delay
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exc_tuple as exc:
                    attempt += 1
                    if attempt >= max_attempts:
                        log.error("Maximum attempts reached for %s: %s", func.__name__, exc)
                        raise
                    # Apply exponential backoff
                    effective_delay = delay
                    if max_delay is not None:
                        effective_delay = min(effective_delay, max_delay)
                    # Add jitter
                    if jitter:
                        effective_delay += random.uniform(-jitter, jitter)
                        effective_delay = max(0.0, effective_delay)
                    log.warning(
                        "Error in %s on attempt %s: %s. Retrying in %.2f seconds.",
                        func.__name__,
                        attempt,
                        exc,
                        effective_delay,
                    )
                    time.sleep(effective_delay)
                    delay *= backoff_factor

        return wrapper

    return decorator
