# =============================================================================
# Docstring
# =============================================================================

"""
Deprecated Decorator
====================

Mark functions as deprecated with warnings.

Examples
--------
>>> from rite.functional.decorators import decorators_deprecated
>>> @decorators_deprecated("Use new_function instead")
... def old_function():
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
import warnings

# =============================================================================
# Types
# =============================================================================

T = TypeVar("T")

# =============================================================================
# Functions
# =============================================================================


def decorators_deprecated(
    message: str = "This function is deprecated",
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to mark function as deprecated.

    Issues DeprecationWarning when function is called.

    Args:
        message: Deprecation message to show.

    Returns:
        Decorated function that shows warning.

    Examples:
        >>> @decorators_deprecated("Use process_v2() instead")
        ... def process_v1():
        ...     return "old"
        >>> process_v1()  # doctest: +SKIP
        'old'

    Notes:
        Warnings can be controlled with warnings module.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> T:
            warnings.warn(
                f"{func.__name__} is deprecated. {message}",
                category=DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return wrapped

    return decorator


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["decorators_deprecated"]
