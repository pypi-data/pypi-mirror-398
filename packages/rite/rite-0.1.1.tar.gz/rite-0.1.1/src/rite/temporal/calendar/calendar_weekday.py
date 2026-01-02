# =============================================================================
# Docstring
# =============================================================================

"""
Calendar Weekday
================

Get weekday for date.

Examples
--------
>>> from rite.temporal.calendar import calendar_weekday
>>> calendar_weekday(2024, 12, 27)
4

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


def calendar_weekday(year: int, month: int, day: int) -> int:
    """
    Get weekday for date.

    Args:
        year: Year.
        month: Month (1-12).
        day: Day of month.

    Returns:
        Weekday (0=Monday, 6=Sunday).

    Examples:
        >>> calendar_weekday(2024, 12, 27)
        4
        >>> calendar_weekday(2024, 1, 1)
        0

    Notes:
        Uses calendar.weekday().
        0=Monday, 6=Sunday.
    """
    return calendar.weekday(year, month, day)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["calendar_weekday"]
