# =============================================================================
# Docstring
# =============================================================================

"""
Absolute Value
==============

Get absolute value of a number.

Examples
--------
>>> from rite.numeric.math import math_abs
>>> math_abs(-5)
5

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def math_abs(value: float) -> float:
    """
    Get absolute value of a number.

    Args:
        value: Number to get absolute value of.

    Returns:
        Absolute value.

    Examples:
        >>> math_abs(-5)
        5
        >>> math_abs(5)
        5
        >>> math_abs(0)
        0

    Notes:
        Wrapper around built-in abs() for consistency.
    """
    return abs(value)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["math_abs"]
