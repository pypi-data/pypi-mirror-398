# =============================================================================
# Docstring
# =============================================================================

"""
Function Pipe
=============

Pipe value through functions left to right.

Examples
--------
>>> from rite.functional.composition import composition_pipe
>>> add_one = lambda x: x + 1
>>> double = lambda x: x * 2
>>> f = composition_pipe(add_one, double)
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
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def composition_pipe(
    *functions: Callable[[Any], Any],
) -> Callable[[Any], Any]:
    """
    Pipe value through functions left to right.

    Args:
        *functions: Functions to pipe through.

    Returns:
        Piped function.

    Examples:
        >>> inc = lambda x: x + 1
        >>> double = lambda x: x * 2
        >>> f = composition_pipe(inc, double)
        >>> f(3)  # double(inc(3)) = double(4) = 8
        8

    Notes:
        Functions are applied left to right: h = g ∘ f.
        For right to left, use composition_compose.
    """
    if not functions:
        return lambda x: x

    def piped(arg: Any) -> Any:
        result = arg
        for func in functions:
            result = func(result)
        return result

    return piped


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["composition_pipe"]
