# =============================================================================
# Docstring
# =============================================================================

"""
Normalize Function
==================

Normalize value to 0-1 range.

Examples
--------
>>> from rite.numeric.range import range_normalize
>>> range_normalize(5, 0, 10)
0.5

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def range_normalize(value: float, minimum: float, maximum: float) -> float:
    """
    Normalize value to 0-1 range.

    Args:
        value: Value to normalize.
        minimum: Minimum of input range.
        maximum: Maximum of input range.

    Returns:
        Normalized value (0.0 to 1.0).

    Examples:
        >>> range_normalize(5, 0, 10)
        0.5
        >>> range_normalize(0, 0, 10)
        0.0
        >>> range_normalize(10, 0, 10)
        1.0

    Notes:
        Formula: (value - min) / (max - min).
        Assumes maximum > minimum.
    """
    if maximum == minimum:
        return 0.0

    return (value - minimum) / (maximum - minimum)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["range_normalize"]
