# =============================================================================
# Docstring
# =============================================================================

"""
Clamp Function
==============

Clamp a value between minimum and maximum bounds.

Examples
--------
>>> from rite.numeric.math import math_clamp
>>> math_clamp(5, 0, 10)
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


def math_clamp(value: float, minimum: float, maximum: float) -> float:
    """
    Clamp a value between minimum and maximum bounds.

    Args:
        value: Value to clamp.
        minimum: Lower bound.
        maximum: Upper bound.

    Returns:
        Clamped value.

    Examples:
        >>> math_clamp(5, 0, 10)
        5
        >>> math_clamp(-5, 0, 10)
        0
        >>> math_clamp(15, 0, 10)
        10

    Notes:
        If minimum > maximum, behavior is undefined.
    """
    return max(minimum, min(maximum, value))


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["math_clamp"]
