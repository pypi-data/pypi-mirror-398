# =============================================================================
# Docstring
# =============================================================================

"""
Timezone List
=============

List available timezones.

Examples
--------
>>> from rite.temporal.timezone import timezone_list
>>> zones = timezone_list()
>>> "UTC" in zones
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from zoneinfo import available_timezones

# =============================================================================
# Functions
# =============================================================================


def timezone_list() -> list[str]:
    """
    Get list of available timezones.

    Returns:
        Sorted list of timezone names.

    Examples:
        >>> zones = timezone_list()
        >>> "UTC" in zones
        True
        >>> "America/New_York" in zones
        True

    Notes:
        Uses IANA timezone database.
        Returns sorted list.
    """
    return sorted(available_timezones())


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["timezone_list"]
