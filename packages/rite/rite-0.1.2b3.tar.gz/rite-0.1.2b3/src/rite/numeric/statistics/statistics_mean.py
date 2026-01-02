# =============================================================================
# Docstring
# =============================================================================

"""
Mean Calculator
===============

Calculate arithmetic mean of numbers.

Examples
--------
>>> from rite.numeric.statistics import statistics_mean
>>> statistics_mean([1, 2, 3, 4, 5])
3.0

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def statistics_mean(values: list[float]) -> float:
    """
    Calculate arithmetic mean of numbers.

    Args:
        values: List of numbers.

    Returns:
        Mean value.

    Raises:
        ValueError: If values list is empty.

    Examples:
        >>> statistics_mean([1, 2, 3, 4, 5])
        3.0
        >>> statistics_mean([10, 20, 30])
        20.0
        >>> statistics_mean([5.5])
        5.5

    Notes:
        Sum divided by count.
    """
    if not values:
        raise ValueError("Cannot calculate mean of empty list")

    return sum(values) / len(values)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["statistics_mean"]
