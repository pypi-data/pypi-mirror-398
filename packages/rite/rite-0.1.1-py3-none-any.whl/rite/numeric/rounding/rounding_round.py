# =============================================================================
# Docstring
# =============================================================================

"""
Round Function
==============

Round number to specified decimal places.

Examples
--------
>>> from rite.numeric.rounding import rounding_round
>>> rounding_round(3.14159, 2)
3.14

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def rounding_round(value: float, decimals: int = 0) -> float:
    """
    Round number to specified decimal places.

    Args:
        value: Number to round.
        decimals: Number of decimal places.

    Returns:
        Rounded value.

    Examples:
        >>> rounding_round(3.14159, 2)
        3.14
        >>> rounding_round(3.5)
        4.0
        >>> rounding_round(123.456, 1)
        123.5

    Notes:
        Uses banker's rounding (round half to even).
    """
    return round(value, decimals)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["rounding_round"]
