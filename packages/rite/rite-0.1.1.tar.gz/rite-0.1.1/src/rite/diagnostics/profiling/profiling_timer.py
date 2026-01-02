# =============================================================================
# Docstring
# =============================================================================

"""
Timer Decorator
===============

Decorator to measure function execution time.

Examples
--------
>>> from rite.diagnostics.profiling import profiling_timer
>>> @profiling_timer()
... def slow_function():
...     time.sleep(1)

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


def profiling_timer(
    name: str | None = None, print_result: bool = True
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to measure function execution time.

    Args:
        name: Optional name for the operation being timed.
        print_result: If True, print timing result.

    Returns:
        Decorated function that measures execution time.

    Examples:
        >>> @profiling_timer()
        ... def compute():
        ...     sum(range(1000000))
        >>> @profiling_timer(name="API Call", print_result=False)
        ... def api_request():
        ...     pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            operation_name = name or func.__name__
            start = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.perf_counter() - start
                if print_result:
                    print(f"{operation_name}: {elapsed:.6f} seconds")

        return wrapper

    return decorator


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["profiling_timer"]
