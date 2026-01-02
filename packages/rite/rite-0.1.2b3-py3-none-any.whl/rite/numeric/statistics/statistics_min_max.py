# =============================================================================
# Docstring
# =============================================================================

"""
Min/Max Functions
=================

Find minimum and maximum values.

Examples
--------
>>> from rite.numeric.statistics import statistics_min
>>> statistics_min([3, 1, 4, 1, 5])
1

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def statistics_min(values: list[float]) -> float:
    """
    Find minimum value in list.

    Args:
        values: List of numbers.

    Returns:
        Minimum value.

    Raises:
        ValueError: If values list is empty.

    Examples:
        >>> statistics_min([3, 1, 4, 1, 5])
        1
        >>> statistics_min([10, 20, 5])
        5

    Notes:
        Wrapper around built-in min().
    """
    if not values:
        raise ValueError("Cannot find min of empty list")
    return min(values)


def statistics_max(values: list[float]) -> float:
    """
    Find maximum value in list.

    Args:
        values: List of numbers.

    Returns:
        Maximum value.

    Raises:
        ValueError: If values list is empty.

    Examples:
        >>> statistics_max([3, 1, 4, 1, 5])
        5
        >>> statistics_max([10, 20, 5])
        20

    Notes:
        Wrapper around built-in max().
    """
    if not values:
        raise ValueError("Cannot find max of empty list")
    return max(values)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["statistics_min", "statistics_max"]
