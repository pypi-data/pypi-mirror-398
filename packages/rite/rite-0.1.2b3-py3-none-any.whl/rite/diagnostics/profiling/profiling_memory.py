# =============================================================================
# Docstring
# =============================================================================

"""
Memory Profiler
===============

Measure memory usage of function.

Examples
--------
>>> from rite.diagnostics.profiling import profiling_memory
>>> @profiling_memory()
... def memory_intensive():
...     data = [0] * 1000000

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections.abc import Callable
from functools import wraps
import gc
import sys
from typing import Any, TypeVar

# =============================================================================
# Types
# =============================================================================

T = TypeVar("T")

# =============================================================================
# Functions
# =============================================================================


def profiling_memory(
    print_result: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to measure memory usage of function.

    Args:
        print_result: If True, print memory usage.

    Returns:
        Decorated function that measures memory.

    Examples:
        >>> @profiling_memory()
        ... def create_large_list():
        ...     return [0] * 1000000
        >>> @profiling_memory(print_result=False)
        ... def process_data():
        ...     pass

    Notes:
        Uses sys.getsizeof for basic measurement.
        For detailed profiling, use memory_profiler package.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            gc.collect()
            before = _get_memory_usage()

            result = func(*args, **kwargs)

            gc.collect()
            after = _get_memory_usage()
            delta = after - before

            if print_result:
                print(
                    f"{func.__name__}: "
                    f"{delta / 1024 / 1024:.2f} MB memory delta"
                )

            return result

        return wrapper

    return decorator


def _get_memory_usage() -> int:
    """Get approximate memory usage."""
    return sum(sys.getsizeof(obj) for obj in gc.get_objects())


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["profiling_memory"]
