# =============================================================================
# Docstring
# =============================================================================

"""
Median Calculator
=================

Calculate median of numbers.

Examples
--------
>>> from rite.numeric.statistics import statistics_median
>>> statistics_median([1, 2, 3, 4, 5])
3

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def statistics_median(values: list[float]) -> float:
    """
    Calculate median of numbers.

    Args:
        values: List of numbers.

    Returns:
        Median value.

    Raises:
        ValueError: If values list is empty.

    Examples:
        >>> statistics_median([1, 2, 3, 4, 5])
        3
        >>> statistics_median([1, 2, 3, 4])
        2.5
        >>> statistics_median([5])
        5

    Notes:
        Middle value for odd length.
        Average of two middle values for even length.
    """
    if not values:
        raise ValueError("Cannot calculate median of empty list")

    sorted_values = sorted(values)
    n = len(sorted_values)

    if n % 2 == 0:
        # Even: average of two middle values
        return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
    else:
        # Odd: middle value
        return sorted_values[n // 2]


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["statistics_median"]
