# =============================================================================
# Docstring
# =============================================================================

"""
Calendar Month Days
===================

Get number of days in month.

Examples
--------
>>> from rite.temporal.calendar import calendar_month_days
>>> calendar_month_days(2024, 2)
29

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


def calendar_month_days(year: int, month: int) -> int:
    """
    Get number of days in month.

    Args:
        year: Year.
        month: Month (1-12).

    Returns:
        Number of days in month.

    Examples:
        >>> calendar_month_days(2024, 2)
        29
        >>> calendar_month_days(2023, 2)
        28
        >>> calendar_month_days(2024, 4)
        30

    Notes:
        Uses calendar.monthrange().
    """
    return calendar.monthrange(year, month)[1]


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["calendar_month_days"]
