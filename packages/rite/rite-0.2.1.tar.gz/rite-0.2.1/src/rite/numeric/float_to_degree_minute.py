# =============================================================================
# Docstring
# =============================================================================

"""
Degree-Minute Conversion
=======================

Convert float values to degree and minute components.

Example:
    >>> float_to_degree_minute(12.5)
    (12, 30.0)
    >>> float_to_degree_minute(-12.5)
    (-12, 30.0)

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


def float_to_degree_minute(
    value: float, absolute: bool = False
) -> tuple[int, float]:
    """
    Split a float value into DM (degree, minute) parts.

    Args:
        value: Float value to split
        absolute: Obtain the absolute value

    Returns:
        Tuple containing (degree, minute)

    Example:
        >>> float_to_degree_minute(12.5)
        (12, 30.0)
        >>> float_to_degree_minute(-12.5, absolute=True)
        (12, 30.0)
    """
    invert = not absolute and value < 0
    value = abs(value)
    degree = int(math.floor(value))
    minute = (value - degree) * 60
    return (degree * -1 if invert else degree, minute)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "float_to_degree_minute",
]
