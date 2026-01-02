# =============================================================================
# Docstring
# =============================================================================

"""
Once Decorator
==============

Ensures function is called only once.

Examples
--------
>>> from rite.functional.decorators import decorators_once
>>> @decorators_once()
... def initialize():
...     return "initialized"

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


def decorators_once() -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to execute function only once.

    Subsequent calls return cached result.

    Returns:
        Decorated function that runs once.

    Examples:
        >>> @decorators_once()
        ... def setup():
        ...     return "configured"
        >>> setup()
        'configured'
        >>> setup()  # Returns cached result
        'configured'

    Notes:
        Result is cached regardless of arguments.
        For argument-sensitive caching, use memoization.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        called: bool = False
        result: T | None = None

        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> T:
            nonlocal called, result

            if not called:
                result = func(*args, **kwargs)
                called = True

            return result  # type: ignore

        return wrapped

    return decorator


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["decorators_once"]
