# =============================================================================
# Docstring
# =============================================================================

"""
Duration To Seconds
===================

Convert duration to total seconds.

Examples
--------
>>> from rite.temporal.duration import duration_to_seconds
>>> from datetime import timedelta
>>> duration_to_seconds(timedelta(hours=1))
3600.0

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


def duration_to_seconds(td: timedelta) -> float:
    """
    Convert timedelta to total seconds.

    Args:
        td: Timedelta object.

    Returns:
        Total seconds as float.

    Examples:
        >>> from datetime import timedelta
        >>> duration_to_seconds(timedelta(hours=1))
        3600.0
        >>> duration_to_seconds(timedelta(days=1))
        86400.0

    Notes:
        Returns float for precision.
    """
    return td.total_seconds()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["duration_to_seconds"]
