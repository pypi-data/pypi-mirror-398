# =============================================================================
# Docstring
# =============================================================================

"""
Throttle Decorator
==================

Limits function execution frequency.

Examples
--------
>>> from rite.functional.decorators import decorators_throttle
>>> @decorators_throttle(1.0)
... def api_call():
...     return "response"

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections.abc import Callable
from functools import wraps
import time
from typing import Any, TypeVar

# =============================================================================
# Types
# =============================================================================

T = TypeVar("T")

# =============================================================================
# Functions
# =============================================================================


def decorators_throttle(
    interval: float,
) -> Callable[[Callable[..., T]], Callable[..., T | None]]:
    """
    Decorator to throttle function calls.

    Ensures function is not called more frequently than interval.

    Args:
        interval: Minimum time between calls in seconds.

    Returns:
        Decorated function with throttling.

    Examples:
        >>> @decorators_throttle(1.0)
        ... def process():
        ...     return "done"
        >>> process()  # First call executes immediately
        'done'
        >>> process()  # Subsequent calls within 1s are skipped

    Notes:
        Returns None if called within throttle interval.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T | None]:
        last_called: float = 0.0

        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> T | None:
            nonlocal last_called
            now = time.time()

            if now - last_called >= interval:
                last_called = now
                return func(*args, **kwargs)

            return None

        return wrapped

    return decorator


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["decorators_throttle"]
