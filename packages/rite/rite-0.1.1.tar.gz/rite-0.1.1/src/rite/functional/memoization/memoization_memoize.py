# =============================================================================
# Docstring
# =============================================================================

"""
Simple Memoization
==================

Cache function results based on arguments.

Examples
--------
>>> from rite.functional.memoization import memoization_memoize
>>> @memoization_memoize()
... def fibonacci(n):
...     if n <= 1:
...         return n
...     return fibonacci(n-1) + fibonacci(n-2)

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

# =============================================================================
# Types
# =============================================================================

T = TypeVar("T")

# =============================================================================
# Functions
# =============================================================================


def memoization_memoize() -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to memoize function results.

    Caches results based on arguments.

    Returns:
        Decorated function with caching.

    Examples:
        >>> @memoization_memoize()
        ... def expensive_computation(n):
        ...     return sum(range(n))
        >>> expensive_computation(100)
        4950
        >>> expensive_computation(100)  # Returns cached result
        4950

    Notes:
        Only works with hashable arguments.
        For unhashable args, use custom cache key.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache: dict[tuple[Any, ...], T] = {}

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create cache key from args and kwargs
            key = (args, tuple(sorted(kwargs.items())))

            if key not in cache:
                cache[key] = func(*args, **kwargs)

            return cache[key]

        wrapper.cache = cache  # type: ignore
        wrapper.cache_clear = lambda: cache.clear()  # type: ignore
        return wrapper

    return decorator


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["memoization_memoize"]
