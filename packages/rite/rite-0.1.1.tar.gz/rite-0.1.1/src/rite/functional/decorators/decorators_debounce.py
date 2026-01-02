# =============================================================================
# Docstring
# =============================================================================

"""
Debounce Decorator
==================

Delays function execution by specified wait time.

Examples
--------
>>> from rite.functional.decorators import decorators_debounce
>>> @decorators_debounce(0.5)
... def process():
...     return "done"

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


def decorators_debounce(
    wait_time: float,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to debounce function call.

    Args:
        wait_time: Time to wait in seconds before execution.

    Returns:
        Decorated function that delays execution.

    Examples:
        >>> @decorators_debounce(0.5)
        ... def greet():
        ...     return "Hello"
        >>> greet()
        'Hello'

    Notes:
        This implementation waits before each execution.
        For event-driven debouncing, use throttle pattern.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> T:
            time.sleep(wait_time)
            return func(*args, **kwargs)

        return wrapped

    return decorator


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["decorators_debounce"]
