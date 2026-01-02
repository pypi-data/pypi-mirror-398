# =============================================================================
# Docstring
# =============================================================================

"""
Timezone Convert
================

Convert datetime to different timezone.

Examples
--------
>>> from rite.temporal.timezone import timezone_convert
>>> from datetime import datetime, timezone
>>> dt = datetime.now(timezone.utc)
>>> timezone_convert(dt, "America/New_York")

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from datetime import datetime
from zoneinfo import ZoneInfo

# =============================================================================
# Functions
# =============================================================================


def timezone_convert(dt: datetime, target_tz: str) -> datetime:
    """
    Convert datetime to target timezone.

    Args:
        dt: Datetime object (should be timezone-aware).
        target_tz: Target timezone name (IANA).

    Returns:
        Datetime in target timezone.

    Examples:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(2024, 12, 27, 12, 0, tzinfo=timezone.utc)
        >>> timezone_convert(dt, "America/New_York")
        datetime.datetime(2024, 12, 27, 7, 0, ...)

    Notes:
        Input datetime should be timezone-aware.
        Returns new datetime object.
    """
    return dt.astimezone(ZoneInfo(target_tz))


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["timezone_convert"]
