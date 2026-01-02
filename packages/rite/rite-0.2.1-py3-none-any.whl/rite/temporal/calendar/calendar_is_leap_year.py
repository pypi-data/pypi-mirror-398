# =============================================================================
# Docstring
# =============================================================================

"""
Calendar Is Leap Year
=====================

Check if year is leap year.

Examples
--------
>>> from rite.temporal.calendar import calendar_is_leap_year
>>> calendar_is_leap_year(2024)
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import calendar

# =============================================================================
# Functions
# =============================================================================


def calendar_is_leap_year(year: int) -> bool:
    """
    Check if year is a leap year.

    Args:
        year: Year to check.

    Returns:
        True if leap year, False otherwise.

    Examples:
        >>> calendar_is_leap_year(2024)
        True
        >>> calendar_is_leap_year(2023)
        False
        >>> calendar_is_leap_year(2000)
        True

    Notes:
        Uses calendar.isleap().
    """
    return calendar.isleap(year)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["calendar_is_leap_year"]
