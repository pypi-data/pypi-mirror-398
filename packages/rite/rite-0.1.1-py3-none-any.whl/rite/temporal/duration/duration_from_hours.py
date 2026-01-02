# =============================================================================
# Docstring
# =============================================================================

"""
Duration From Hours
===================

Create duration from hours.

Examples
--------
>>> from rite.temporal.duration import duration_from_hours
>>> duration_from_hours(24)
timedelta(days=1)

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from datetime import timedelta

# =============================================================================
# Functions
# =============================================================================


def duration_from_hours(hours: int | float) -> timedelta:
    """
    Create timedelta from hours.

    Args:
        hours: Number of hours.

    Returns:
        Timedelta object.

    Examples:
        >>> duration_from_hours(24)
        timedelta(days=1)
        >>> duration_from_hours(1.5)
        timedelta(seconds=5400)

    Notes:
        Converts to seconds internally.
    """
    return timedelta(hours=hours)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["duration_from_hours"]
