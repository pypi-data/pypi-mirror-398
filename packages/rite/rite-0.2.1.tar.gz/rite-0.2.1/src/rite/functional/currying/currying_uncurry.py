# =============================================================================
# Docstring
# =============================================================================

"""
Function Uncurrying
===================

Transform curried function back to multi-argument form.

Examples
--------
>>> from rite.functional.currying import currying_uncurry
>>> curried = lambda a: lambda b: lambda c: a + b + c
>>> uncurried = currying_uncurry(curried, 3)
>>> uncurried(1, 2, 3)
6

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections.abc import Callable
from typing import Any, TypeVar

# =============================================================================
# Types
# =============================================================================

T = TypeVar("T")

# =============================================================================
# Functions
# =============================================================================


def currying_uncurry(
    func: Callable[..., Any], arity: int
) -> Callable[..., Any]:
    """
    Uncurry a curried function.

    Transforms f(a)(b)(c) back to f(a, b, c).

    Args:
        func: Curried function.
        arity: Number of arguments.

    Returns:
        Uncurried function.

    Examples:
        >>> curried = lambda x: lambda y: x + y
        >>> uncurried = currying_uncurry(curried, 2)
        >>> uncurried(5, 3)
        8

    Notes:
        Arity must be specified as it cannot be inferred.
    """

    def uncurried(*args: Any) -> Any:
        if len(args) != arity:
            raise TypeError(f"Expected {arity} arguments, got {len(args)}")

        result = func
        for arg in args:
            result = result(arg)
        return result

    return uncurried


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["currying_uncurry"]
