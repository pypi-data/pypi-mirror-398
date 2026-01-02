# =============================================================================
# Docstring
# =============================================================================

"""
Temporal Module
===============

Date, time, and timezone operations.

This module provides comprehensive utilities for working with dates,
times, durations, timezones, calendars, and formatting using only
Python's standard library.

Submodules
----------
- datetime: Date and time operations
- duration: Time duration utilities
- timezone: Timezone conversions
- calendar: Calendar operations
- formatting: Date/time formatting

Examples
--------
>>> from rite.temporal import datetime_now, duration_from_hours
>>> now = datetime_now()
>>> dur = duration_from_hours(2)

Notes
-----
Legacy classes Timestamp, Duration, and Timezone are still
available for backward compatibility.
"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .calendar import (
    calendar_is_leap_year,
    calendar_month_days,
    calendar_weekday,
)
from .datetime import (
    datetime_format,
    datetime_from_timestamp,
    datetime_now,
    datetime_parse,
    datetime_to_iso,
    datetime_to_timestamp,
)
from .duration import (
    duration_from_days,
    duration_from_hours,
    duration_from_minutes,
    duration_from_seconds,
    duration_to_seconds,
)
from .formatting import (
    format_human_readable,
    format_iso8601,
    format_rfc3339,
)
from .timezone import timezone_convert, timezone_get, timezone_list

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    # DateTime
    "datetime_now",
    "datetime_from_timestamp",
    "datetime_to_timestamp",
    "datetime_parse",
    "datetime_format",
    "datetime_to_iso",
    # Duration
    "duration_from_seconds",
    "duration_from_minutes",
    "duration_from_hours",
    "duration_from_days",
    "duration_to_seconds",
    # Timezone
    "timezone_get",
    "timezone_convert",
    "timezone_list",
    # Calendar
    "calendar_is_leap_year",
    "calendar_month_days",
    "calendar_weekday",
    # Formatting
    "format_iso8601",
    "format_rfc3339",
    "format_human_readable",
]
