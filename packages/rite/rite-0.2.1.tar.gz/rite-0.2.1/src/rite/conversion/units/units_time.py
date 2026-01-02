# =============================================================================
# Docstring
# =============================================================================

"""
Time Unit Conversion
====================

Convert between seconds, minutes, hours, and days.

Examples
--------
>>> from rite.conversion.units import units_seconds_to_minutes
>>> units_seconds_to_minutes(60)
1.0
>>> units_seconds_to_minutes(120)
2.0

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def units_seconds_to_minutes(seconds: float) -> float:
    """
    Convert seconds to minutes.

    Args:
        seconds: Time in seconds.

    Returns:
        Time in minutes.

    Examples:
        >>> units_seconds_to_minutes(60)
        1.0
        >>> units_seconds_to_minutes(120)
        2.0
    """
    return seconds / 60


def units_minutes_to_seconds(minutes: float) -> float:
    """
    Convert minutes to seconds.

    Args:
        minutes: Time in minutes.

    Returns:
        Time in seconds.

    Examples:
        >>> units_minutes_to_seconds(1)
        60.0
        >>> units_minutes_to_seconds(2)
        120.0
    """
    return minutes * 60


def units_seconds_to_hours(seconds: float) -> float:
    """
    Convert seconds to hours.

    Args:
        seconds: Time in seconds.

    Returns:
        Time in hours.

    Examples:
        >>> units_seconds_to_hours(3600)
        1.0
        >>> units_seconds_to_hours(7200)
        2.0
    """
    return seconds / 3600


def units_hours_to_seconds(hours: float) -> float:
    """
    Convert hours to seconds.

    Args:
        hours: Time in hours.

    Returns:
        Time in seconds.

    Examples:
        >>> units_hours_to_seconds(1)
        3600.0
        >>> units_hours_to_seconds(2)
        7200.0
    """
    return hours * 3600


def units_seconds_to_days(seconds: float) -> float:
    """
    Convert seconds to days.

    Args:
        seconds: Time in seconds.

    Returns:
        Time in days.

    Examples:
        >>> units_seconds_to_days(86400)
        1.0
        >>> units_seconds_to_days(172800)
        2.0
    """
    return seconds / 86400


def units_days_to_seconds(days: float) -> float:
    """
    Convert days to seconds.

    Args:
        days: Time in days.

    Returns:
        Time in seconds.

    Examples:
        >>> units_days_to_seconds(1)
        86400.0
        >>> units_days_to_seconds(2)
        172800.0
    """
    return days * 86400


def units_minutes_to_hours(minutes: float) -> float:
    """
    Convert minutes to hours.

    Args:
        minutes: Time in minutes.

    Returns:
        Time in hours.

    Examples:
        >>> units_minutes_to_hours(60)
        1.0
        >>> units_minutes_to_hours(120)
        2.0
    """
    return minutes / 60


def units_hours_to_minutes(hours: float) -> float:
    """
    Convert hours to minutes.

    Args:
        hours: Time in hours.

    Returns:
        Time in minutes.

    Examples:
        >>> units_hours_to_minutes(1)
        60.0
        >>> units_hours_to_minutes(2)
        120.0
    """
    return hours * 60


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "units_seconds_to_minutes",
    "units_minutes_to_seconds",
    "units_seconds_to_hours",
    "units_hours_to_seconds",
    "units_seconds_to_days",
    "units_days_to_seconds",
    "units_minutes_to_hours",
    "units_hours_to_minutes",
]
