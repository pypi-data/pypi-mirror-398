# =============================================================================
# Docstring
# =============================================================================

"""
Partial Application
===================

Partially apply function arguments.

Examples
--------
>>> from rite.functional.partial import partial_apply
>>> def greet(greeting, name):
...     return f"{greeting}, {name}!"
>>> say_hello = partial_apply(greet, "Hello")
>>> say_hello("Alice")
'Hello, Alice!'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections.abc import Callable
from functools import partial
from typing import Any, TypeVar

# =============================================================================
# Types
# =============================================================================

T = TypeVar("T")

# =============================================================================
# Functions
# =============================================================================


def partial_apply(
    func: Callable[..., T], *args: Any, **kwargs: Any
) -> Callable[..., T]:
    """
    Partially apply function arguments.

    Args:
        func: Function to partially apply.
        *args: Positional arguments to fix.
        **kwargs: Keyword arguments to fix.

    Returns:
        Partially applied function.

    Examples:
        >>> def multiply(x, y, z):
        ...     return x * y * z
        >>> double = partial_apply(multiply, 2)
        >>> double(3, 4)
        24
        >>> def power(base, exponent):
        ...     return base ** exponent
        >>> square = partial_apply(power, exponent=2)
        >>> square(5)
        25

    Notes:
        Uses functools.partial internally.
    """
    return partial(func, *args, **kwargs)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["partial_apply"]
