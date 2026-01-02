# =============================================================================
# Docstring
# =============================================================================

"""
Calendar Module
===============

Calendar operations.

This submodule provides utilities for calendar operations
like leap years, days in month, and weekday calculations.

Examples
--------
>>> from rite.temporal.calendar import calendar_is_leap_year
>>> from rite.temporal.calendar import calendar_month_days
>>> calendar_is_leap_year(2024)
True
>>> calendar_month_days(2024, 2)
29

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .calendar_is_leap_year import calendar_is_leap_year
from .calendar_month_days import calendar_month_days
from .calendar_weekday import calendar_weekday

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "calendar_is_leap_year",
    "calendar_month_days",
    "calendar_weekday",
]
