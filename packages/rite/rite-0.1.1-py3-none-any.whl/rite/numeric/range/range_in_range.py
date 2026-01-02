# =============================================================================
# Docstring
# =============================================================================

"""
In Range Checker
================

Check if value is within range.

Examples
--------
>>> from rite.numeric.range import range_in_range
>>> range_in_range(5, 0, 10)
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def range_in_range(
    value: float,
    minimum: float,
    maximum: float,
    inclusive: bool = True,
) -> bool:
    """
    Check if value is within range.

    Args:
        value: Value to check.
        minimum: Lower bound.
        maximum: Upper bound.
        inclusive: Include bounds in check.

    Returns:
        True if value is in range.

    Examples:
        >>> range_in_range(5, 0, 10)
        True
        >>> range_in_range(0, 0, 10, inclusive=True)
        True
        >>> range_in_range(0, 0, 10, inclusive=False)
        False
        >>> range_in_range(15, 0, 10)
        False

    Notes:
        Inclusive by default (<=, >=).
        Non-inclusive uses (<, >).
    """
    if inclusive:
        return minimum <= value <= maximum
    else:
        return minimum < value < maximum


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["range_in_range"]
