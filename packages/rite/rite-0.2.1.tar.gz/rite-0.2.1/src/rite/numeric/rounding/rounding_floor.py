# =============================================================================
# Docstring
# =============================================================================

"""
Floor Function
==============

Round down to nearest integer.

Examples
--------
>>> from rite.numeric.rounding import rounding_floor
>>> rounding_floor(3.9)
3

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import math

# =============================================================================
# Functions
# =============================================================================


def rounding_floor(value: float) -> int:
    """
    Round down to nearest integer.

    Args:
        value: Number to round down.

    Returns:
        Floored integer value.

    Examples:
        >>> rounding_floor(3.9)
        3
        >>> rounding_floor(3.1)
        3
        >>> rounding_floor(-3.1)
        -4

    Notes:
        Rounds toward negative infinity.
    """
    return math.floor(value)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["rounding_floor"]
