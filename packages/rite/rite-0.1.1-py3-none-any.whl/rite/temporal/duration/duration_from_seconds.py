# =============================================================================
# Docstring
# =============================================================================

"""
Duration From Seconds
=====================

Create duration from seconds.

Examples
--------
>>> from rite.temporal.duration import duration_from_seconds
>>> duration_from_seconds(3600)
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


def duration_from_seconds(seconds: int | float) -> timedelta:
    """
    Create timedelta from seconds.

    Args:
        seconds: Number of seconds.

    Returns:
        Timedelta object.

    Examples:
        >>> duration_from_seconds(3600)
        timedelta(seconds=3600)
        >>> duration_from_seconds(90.5)
        timedelta(seconds=90, microseconds=500000)

    Notes:
        Supports both int and float values.
    """
    return timedelta(seconds=seconds)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["duration_from_seconds"]
