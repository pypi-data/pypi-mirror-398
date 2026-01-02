# =============================================================================
# Docstring
# =============================================================================

"""
Degree-Minute-Second Conversion
===============================

Convert float values to degree, minute, and second components.

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


def float_to_degree_minute_second(
    value: float,
    absolute: bool = False,
) -> tuple[int, int, float]:
    """
    Split a float value into DMS (degree, minute, second) parts.

    Args:
        value: Float value to split
        absolute: Obtain the absolute value

    Returns:
        Tuple containing (degree, minute, second)

    Example:
        >>> float_to_degree_minute_second(12.5)
        (12, 30, 0.0)
        >>> float_to_degree_minute_second(-12.5, absolute=True)
        (12, 30, 0.0)
    """
    invert = not absolute and value < 0
    value = abs(value)
    degree = int(math.floor(value))
    value = (value - degree) * 60
    minute = int(math.floor(value))
    second = (value - minute) * 60
    return (degree * -1 if invert else degree, minute, second)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "float_to_degree_minute_second",
]
