# =============================================================================
# Docstring
# =============================================================================

"""
LRU Cache
=========

Least Recently Used cache with size limit.

Examples
--------
>>> from rite.functional.memoization import memoization_lru_cache
>>> @memoization_lru_cache(maxsize=128)
... def compute(n):
...     return n * n

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections.abc import Callable
from functools import lru_cache
from typing import TypeVar

# =============================================================================
# Types
# =============================================================================

T = TypeVar("T")

# =============================================================================
# Functions
# =============================================================================


def memoization_lru_cache(
    maxsize: int | None = 128,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    LRU cache decorator with size limit.

    Args:
        maxsize: Maximum cache size (None for unlimited).

    Returns:
        Decorated function with LRU caching.

    Examples:
        >>> @memoization_lru_cache(maxsize=100)
        ... def factorial(n):
        ...     if n <= 1:
        ...         return 1
        ...     return n * factorial(n - 1)
        >>> factorial(5)
        120

    Notes:
        Uses functools.lru_cache internally.
        Set maxsize=None for unlimited cache.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        return lru_cache(maxsize=maxsize)(func)

    return decorator


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["memoization_lru_cache"]
