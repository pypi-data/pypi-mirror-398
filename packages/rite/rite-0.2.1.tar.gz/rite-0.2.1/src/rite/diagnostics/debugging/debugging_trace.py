# =============================================================================
# Docstring
# =============================================================================

"""
Function Tracer
===============

Trace function calls with arguments and returns.

Examples
--------
>>> from rite.diagnostics.debugging import debugging_trace
>>> @debugging_trace()
... def add(a, b):
...     return a + b

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


def debugging_trace(
    show_args: bool = True,
    show_return: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to trace function calls.

    Args:
        show_args: Show function arguments.
        show_return: Show return value.

    Returns:
        Decorated function with tracing.

    Examples:
        >>> @debugging_trace()
        ... def multiply(x, y):
        ...     return x * y
        >>> @debugging_trace(show_args=False)
        ... def process():
        ...     pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            func_name = func.__name__

            if show_args:
                args_repr = ", ".join(repr(arg) for arg in args)
                kwargs_repr = ", ".join(
                    f"{k}={v!r}" for k, v in kwargs.items()
                )
                all_args = ", ".join(filter(None, [args_repr, kwargs_repr]))
                print(f"→ {func_name}({all_args})")
            else:
                print(f"→ {func_name}()")

            result = func(*args, **kwargs)

            if show_return:
                print(f"← {func_name} = {result!r}")
            else:
                print(f"← {func_name}")

            return result

        return wrapper

    return decorator


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["debugging_trace"]
