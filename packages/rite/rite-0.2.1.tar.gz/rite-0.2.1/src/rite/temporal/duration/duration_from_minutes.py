# =============================================================================
# Docstring
# =============================================================================

"""
Duration From Minutes
=====================

Create duration from minutes.

Examples
--------
>>> from rite.temporal.duration import duration_from_minutes
>>> duration_from_minutes(60)
timedelta(seconds=3600)

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


def duration_from_minutes(minutes: int | float) -> timedelta:
    """
    Create timedelta from minutes.

    Args:
        minutes: Number of minutes.

    Returns:
        Timedelta object.

    Examples:
        >>> duration_from_minutes(60)
        timedelta(seconds=3600)
        >>> duration_from_minutes(1.5)
        timedelta(seconds=90)

    Notes:
        Converts to seconds internally.
    """
    return timedelta(minutes=minutes)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["duration_from_minutes"]
