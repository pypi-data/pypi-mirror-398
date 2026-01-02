# =============================================================================
# Docstring
# =============================================================================

"""
Degree-Minute Converter
=======================

Convert float to degree-minute format.

Examples
--------
>>> from rite.numeric.coordinates import coordinates_to_degree_minute
>>> coordinates_to_degree_minute(12.5)
(12, 30.0)

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


def coordinates_to_degree_minute(
    value: float, absolute: bool = False
) -> tuple[int, float]:
    """
    Convert float to degree-minute format.

    Args:
        value: Float value to convert.
        absolute: Use absolute value.

    Returns:
        Tuple of (degrees, minutes).

    Examples:
        >>> coordinates_to_degree_minute(12.5)
        (12, 30.0)
        >>> coordinates_to_degree_minute(-12.5)
        (-12, 30.0)
        >>> coordinates_to_degree_minute(-12.5, absolute=True)
        (12, 30.0)

    Notes:
        Minutes are in range [0, 60).
    """
    invert = not absolute and value < 0
    value = abs(value)

    degrees = int(value)
    minutes = (value - degrees) * 60

    if invert:
        degrees = -degrees

    return degrees, minutes


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["coordinates_to_degree_minute"]
