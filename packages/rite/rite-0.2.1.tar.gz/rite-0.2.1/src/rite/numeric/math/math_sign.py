# =============================================================================
# Docstring
# =============================================================================

"""
Sign Function
=============

Get sign of a number (-1, 0, or 1).

Examples
--------
>>> from rite.numeric.math import math_sign
>>> math_sign(-5)
-1

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def math_sign(value: float) -> int:
    """
    Get sign of a number.

    Args:
        value: Number to get sign of.

    Returns:
        -1 if negative, 0 if zero, 1 if positive.

    Examples:
        >>> math_sign(-5)
        -1
        >>> math_sign(0)
        0
        >>> math_sign(5)
        1

    Notes:
        Uses integer comparison for zero check.
    """
    if value < 0:
        return -1
    elif value > 0:
        return 1
    else:
        return 0


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["math_sign"]
