# =============================================================================
# Docstring
# =============================================================================

"""
Function Currying
=================

Transform multi-argument function into chain of single-argument functions.

Examples
--------
>>> from rite.functional.currying import currying_curry
>>> def add(a, b, c):
...     return a + b + c
>>> curried = currying_curry(add)
>>> curried(1)(2)(3)
6

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections.abc import Callable
from functools import wraps
import inspect
from typing import Any, TypeVar

# =============================================================================
# Types
# =============================================================================

T = TypeVar("T")

# =============================================================================
# Functions
# =============================================================================


def currying_curry(
    func: Callable[..., T],
) -> Callable[..., T | Callable[..., Any]]:
    """
    Curry a function.

    Transforms f(a, b, c) into f(a)(b)(c).

    Args:
        func: Function to curry.

    Returns:
        Curried function.

    Examples:
        >>> def multiply(x, y, z):
        ...     return x * y * z
        >>> curried = currying_curry(multiply)
        >>> curried(2)(3)(4)
        24
        >>> partial = curried(2)(3)
        >>> partial(4)
        24

    Notes:
        Automatically detects function arity from signature.
    """
    sig = inspect.signature(func)
    arity = len(sig.parameters)

    @wraps(func)
    def curried(*args: Any) -> T | Callable[..., Any]:
        if len(args) >= arity:
            return func(*args[:arity])

        def partial(*more_args: Any) -> T | Callable[..., Any]:
            return curried(*(args + more_args))

        return partial

    return curried


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["currying_curry"]
