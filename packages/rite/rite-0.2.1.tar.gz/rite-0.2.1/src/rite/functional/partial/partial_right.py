# =============================================================================
# Docstring
# =============================================================================

"""
Partial Right
=============

Partially apply arguments from the right.

Examples
--------
>>> from rite.functional.partial import partial_right
>>> def divide(x, y):
...     return x / y
>>> halve = partial_right(divide, 2)
>>> halve(10)
5.0

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


def partial_right(
    func: Callable[..., T], *fixed_args: Any
) -> Callable[..., T]:
    """
    Partially apply arguments from the right.

    Args:
        func: Function to partially apply.
        *fixed_args: Arguments to fix from right.

    Returns:
        Partially applied function.

    Examples:
        >>> def subtract(x, y, z):
        ...     return x - y - z
        >>> f = partial_right(subtract, 5, 2)
        >>> f(10)  # 10 - 5 - 2
        3

    Notes:
        Fixed arguments are appended to the right.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        return func(*args, *fixed_args, **kwargs)

    return wrapper


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["partial_right"]
