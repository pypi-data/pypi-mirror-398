# =============================================================================
# Docstring
# =============================================================================

"""
DMS to Float Converter
======================

Convert degree-minute-second to float.

Examples
--------
>>> from rite.numeric.coordinates import (
...     coordinates_from_degree_minute_second
... )
>>> coordinates_from_degree_minute_second(12, 30, 0)
12.5

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def coordinates_from_degree_minute_second(
    degrees: int, minutes: int, seconds: float
) -> float:
    """
    Convert degree-minute-second to float.

    Args:
        degrees: Degrees component.
        minutes: Minutes component (0-59).
        seconds: Seconds component (0-59.999...).

    Returns:
        Float representation.

    Examples:
        >>> coordinates_from_degree_minute_second(12, 30, 0)
        12.5
        >>> coordinates_from_degree_minute_second(-12, 30, 30)
        -12.508333333333333
        >>> coordinates_from_degree_minute_second(0, 0, 30)
        0.008333333333333333

    Notes:
        Handles negative degrees correctly.
    """
    sign = -1 if degrees < 0 else 1
    degrees = abs(degrees)

    result = degrees + minutes / 60 + seconds / 3600
    return result * sign


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["coordinates_from_degree_minute_second"]
