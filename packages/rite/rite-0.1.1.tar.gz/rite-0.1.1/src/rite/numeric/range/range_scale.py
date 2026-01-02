# =============================================================================
# Docstring
# =============================================================================

"""
Scale Function
==============

Scale value from one range to another.

Examples
--------
>>> from rite.numeric.range import range_scale
>>> range_scale(5, 0, 10, 0, 100)
50.0

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def range_scale(
    value: float,
    from_min: float,
    from_max: float,
    to_min: float,
    to_max: float,
) -> float:
    """
    Scale value from one range to another.

    Args:
        value: Value to scale.
        from_min: Source range minimum.
        from_max: Source range maximum.
        to_min: Target range minimum.
        to_max: Target range maximum.

    Returns:
        Scaled value.

    Examples:
        >>> range_scale(5, 0, 10, 0, 100)
        50.0
        >>> range_scale(0, 0, 10, 100, 200)
        100.0
        >>> range_scale(10, 0, 10, 100, 200)
        200.0

    Notes:
        Linear interpolation between ranges.
    """
    if from_max == from_min:
        return to_min

    # Normalize to 0-1, then scale to target range
    normalized = (value - from_min) / (from_max - from_min)
    return to_min + normalized * (to_max - to_min)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["range_scale"]
