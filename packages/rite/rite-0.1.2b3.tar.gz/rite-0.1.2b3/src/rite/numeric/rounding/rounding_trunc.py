# =============================================================================
# Docstring
# =============================================================================

"""
Truncate Function
=================

Truncate decimal portion of number.

Examples
--------
>>> from rite.numeric.rounding import rounding_trunc
>>> rounding_trunc(3.9)
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


def rounding_trunc(value: float) -> int:
    """
    Truncate decimal portion of number.

    Args:
        value: Number to truncate.

    Returns:
        Truncated integer value.

    Examples:
        >>> rounding_trunc(3.9)
        3
        >>> rounding_trunc(3.1)
        3
        >>> rounding_trunc(-3.9)
        -3

    Notes:
        Rounds toward zero.
    """
    return math.trunc(value)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["rounding_trunc"]
