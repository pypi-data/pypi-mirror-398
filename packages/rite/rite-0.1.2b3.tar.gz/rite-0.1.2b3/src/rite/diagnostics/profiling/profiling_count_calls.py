# =============================================================================
# Docstring
# =============================================================================

"""
Function Call Counter
=====================

Count how many times a function is called.

Examples
--------
>>> from rite.diagnostics.profiling import profiling_count_calls
>>> @profiling_count_calls()
... def api_call():
...     pass

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


def profiling_count_calls(
    print_every: int | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to count function calls.

    Args:
        print_every: Print count every N calls (None = don't print).

    Returns:
        Decorated function with call counter.

    Examples:
        >>> @profiling_count_calls()
        ... def process():
        ...     pass
        >>> process()
        >>> process.call_count
        1
        >>> @profiling_count_calls(print_every=10)
        ... def api_request():
        ...     pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            wrapper.call_count += 1  # type: ignore

            if (
                print_every
                and wrapper.call_count % print_every == 0  # type: ignore
            ):
                print(
                    f"{func.__name__} called "
                    f"{wrapper.call_count} times"  # type: ignore
                )

            return func(*args, **kwargs)

        wrapper.call_count = 0  # type: ignore
        return wrapper

    return decorator


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["profiling_count_calls"]
