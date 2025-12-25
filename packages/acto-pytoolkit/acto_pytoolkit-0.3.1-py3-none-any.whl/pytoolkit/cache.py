import hashlib
import pickle
import threading
import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple


@dataclass
class SimpleCache:
    """Simple in memory cache with optional time to live per key.

    This cache is safe for basic multi thread use and is meant for small data.
    """

    _store: Dict[str, Tuple[Any, Optional[float]]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Store a value with an optional time to live in seconds."""
        expires_at = time.time() + ttl if ttl is not None else None
        with self._lock:
            self._store[key] = (value, expires_at)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the cache with an optional default."""
        with self._lock:
            if key not in self._store:
                return default
            value, expires_at = self._store[key]
            if expires_at is not None and expires_at < time.time():
                del self._store[key]
                return default
            return value

    def delete(self, key: str) -> None:
        """Remove a key from the cache if it exists."""
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        """Remove all entries from the cache."""
        with self._lock:
            self._store.clear()


_global_cache = SimpleCache()
_SENTINEL = object()


def cached(ttl: Optional[float] = None, key_func: Optional[Callable[..., str]] = None) -> Callable:
    """Decorator that caches return values of a function.

    Parameters
    ----------
    ttl:
        Optional time to live in seconds. If omitted, entries do not expire.
    key_func:
        Optional function to compute a cache key from *args and **kwargs.
        If omitted, a robust hash-based representation is used.

    Examples
    --------
    >>> @cached(ttl=60)
    ... def expensive_computation(x, y):
    ...     return x + y
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Use pickle + hash for robust key generation
                try:
                    key_data = pickle.dumps((func.__module__, func.__name__, args, kwargs))
                    cache_key = hashlib.sha256(key_data).hexdigest()
                except (pickle.PicklingError, TypeError):
                    # Fallback for unpicklable objects
                    cache_key = f"{func.__module__}.{func.__name__}:{args}:{kwargs}"
            cached_value = _global_cache.get(cache_key, default=_SENTINEL)
            if cached_value is not _SENTINEL:
                return cached_value
            result = func(*args, **kwargs)
            _global_cache.set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator
