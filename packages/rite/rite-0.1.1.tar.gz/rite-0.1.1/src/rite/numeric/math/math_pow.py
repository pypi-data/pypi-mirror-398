# =============================================================================
# Docstring
# =============================================================================

"""
Power Function
==============

Raise a number to a power.

Examples
--------
>>> from rite.numeric.math import math_pow
>>> math_pow(2, 3)
8.0

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def math_pow(base: float, exponent: float) -> float:
    """
    Raise a number to a power.

    Args:
        base: Base number.
        exponent: Exponent.

    Returns:
        Result of base ** exponent.

    Examples:
        >>> math_pow(2, 3)
        8.0
        >>> math_pow(5, 2)
        25.0
        >>> math_pow(2, -1)
        0.5

    Notes:
        Wrapper around ** operator for consistency.
    """
    result: float = base**exponent
    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["math_pow"]
