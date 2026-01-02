# =============================================================================
# Docstring
# =============================================================================

"""
Function Composition
====================

Compose multiple functions into one.

Examples
--------
>>> from rite.functional.composition import composition_compose
>>> add_one = lambda x: x + 1
>>> double = lambda x: x * 2
>>> f = composition_compose(double, add_one)
>>> f(3)
8

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


def composition_compose(
    *functions: Callable[[Any], Any],
) -> Callable[[Any], Any]:
    """
    Compose functions right to left.

    Args:
        *functions: Functions to compose.

    Returns:
        Composed function.

    Examples:
        >>> inc = lambda x: x + 1
        >>> double = lambda x: x * 2
        >>> f = composition_compose(inc, double)
        >>> f(3)  # inc(double(3)) = inc(6) = 7
        7

    Notes:
        Functions are applied right to left: f(g(x)).
        For left to right, use composition_pipe.
    """
    if not functions:
        return lambda x: x

    def composed(arg: Any) -> Any:
        result = arg
        for func in reversed(functions):
            result = func(result)
        return result

    return composed


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["composition_compose"]
