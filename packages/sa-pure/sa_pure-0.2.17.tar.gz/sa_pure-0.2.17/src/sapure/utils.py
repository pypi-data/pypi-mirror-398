import time
from functools import wraps
from typing import Callable


def async_timed_lru_cache(ttl_seconds: int = 3600):
    """Decorator for async functions with time-based LRU cache.

    Args:
        ttl_seconds: Time to live for cached results in seconds (default: 1 hour)
    """

    def decorator(func: Callable) -> Callable:
        cache = {}

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function args/kwargs
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()

            # Check if we have a valid cached result
            if key in cache:
                result, timestamp = cache[key]
                if current_time - timestamp < ttl_seconds:
                    return result

            # Call the function and cache the result
            result = await func(*args, **kwargs)
            cache[key] = (result, current_time)

            # Clean up expired entries (simple cleanup)
            expired_keys = [
                k for k, (_, ts) in cache.items() if current_time - ts >= ttl_seconds
            ]
            for k in expired_keys:
                del cache[k]

            return result

        return wrapper

    return decorator
