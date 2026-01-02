# =============================================================================
# Docstring
# =============================================================================

"""
Timezone Get
============

Get timezone object.

Examples
--------
>>> from rite.temporal.timezone import timezone_get
>>> timezone_get("UTC")
ZoneInfo(key='UTC')

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from zoneinfo import ZoneInfo

# =============================================================================
# Functions
# =============================================================================


def timezone_get(name: str = "UTC") -> ZoneInfo:
    """
    Get timezone object by name.

    Args:
        name: Timezone name (IANA). Defaults to UTC.

    Returns:
        ZoneInfo timezone object.

    Raises:
        ZoneInfoNotFoundError: If timezone not found.

    Examples:
        >>> timezone_get("UTC")
        ZoneInfo(key='UTC')
        >>> timezone_get("America/New_York")
        ZoneInfo(key='America/New_York')

    Notes:
        Uses IANA timezone database.
        Python 3.9+ required.
    """
    return ZoneInfo(name)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["timezone_get"]
