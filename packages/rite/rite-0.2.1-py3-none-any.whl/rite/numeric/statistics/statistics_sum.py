# =============================================================================
# Docstring
# =============================================================================

"""
Sum Calculator
==============

Calculate sum of numbers.

Examples
--------
>>> from rite.numeric.statistics import statistics_sum
>>> statistics_sum([1, 2, 3, 4, 5])
15

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def statistics_sum(values: list[float]) -> float:
    """
    Calculate sum of numbers.

    Args:
        values: List of numbers.

    Returns:
        Sum of all values.

    Examples:
        >>> statistics_sum([1, 2, 3, 4, 5])
        15
        >>> statistics_sum([10, 20, 30])
        60
        >>> statistics_sum([])
        0

    Notes:
        Returns 0 for empty list.
        Wrapper around built-in sum().
    """
    return sum(values)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["statistics_sum"]
