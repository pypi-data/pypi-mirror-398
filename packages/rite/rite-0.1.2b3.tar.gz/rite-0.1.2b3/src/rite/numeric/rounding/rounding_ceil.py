# =============================================================================
# Docstring
# =============================================================================

"""
Ceil Function
=============

Round up to nearest integer.

Examples
--------
>>> from rite.numeric.rounding import rounding_ceil
>>> rounding_ceil(3.1)
4

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


def rounding_ceil(value: float) -> int:
    """
    Round up to nearest integer.

    Args:
        value: Number to round up.

    Returns:
        Ceiling integer value.

    Examples:
        >>> rounding_ceil(3.1)
        4
        >>> rounding_ceil(3.9)
        4
        >>> rounding_ceil(-3.1)
        -3

    Notes:
        Rounds toward positive infinity.
    """
    return math.ceil(value)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["rounding_ceil"]
