# =============================================================================
# Docstring
# =============================================================================

"""
Duration From Days
==================

Create duration from days.

Examples
--------
>>> from rite.temporal.duration import duration_from_days
>>> duration_from_days(7)
timedelta(days=7)

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


def duration_from_days(days: int | float) -> timedelta:
    """
    Create timedelta from days.

    Args:
        days: Number of days.

    Returns:
        Timedelta object.

    Examples:
        >>> duration_from_days(7)
        timedelta(days=7)
        >>> duration_from_days(1.5)
        timedelta(days=1, seconds=43200)

    Notes:
        Standard timedelta constructor.
    """
    return timedelta(days=days)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["duration_from_days"]
