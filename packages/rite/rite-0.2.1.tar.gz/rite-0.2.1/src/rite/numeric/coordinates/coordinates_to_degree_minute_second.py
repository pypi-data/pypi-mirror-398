# =============================================================================
# Docstring
# =============================================================================

"""
Degree-Minute-Second Converter
===============================

Convert float to degree-minute-second format.

Examples
--------
>>> from rite.numeric.coordinates import (
...     coordinates_to_degree_minute_second
... )
>>> coordinates_to_degree_minute_second(12.5)
(12, 30, 0.0)

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


def coordinates_to_degree_minute_second(
    value: float, absolute: bool = False
) -> tuple[int, int, float]:
    """
    Convert float to degree-minute-second format.

    Args:
        value: Float value to convert.
        absolute: Use absolute value.

    Returns:
        Tuple of (degrees, minutes, seconds).

    Examples:
        >>> coordinates_to_degree_minute_second(12.5)
        (12, 30, 0.0)
        >>> coordinates_to_degree_minute_second(-12.508333)
        (-12, 30, 30.0)
        >>> coordinates_to_degree_minute_second(-12.5, absolute=True)
        (12, 30, 0.0)

    Notes:
        Seconds are in range [0, 60).
    """
    invert = not absolute and value < 0
    value = abs(value)

    degrees = int(value)
    minutes_float = (value - degrees) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60

    if invert:
        degrees = -degrees

    return degrees, minutes, seconds


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["coordinates_to_degree_minute_second"]
