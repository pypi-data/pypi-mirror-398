# =============================================================================
# Docstring
# =============================================================================

"""
DateTime Now
============

Get current datetime.

Examples
--------
>>> from rite.temporal.datetime import datetime_now
>>> datetime_now()
datetime.datetime(2025, 12, 27, ...)

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from datetime import datetime, timezone

# =============================================================================
# Functions
# =============================================================================


def datetime_now(tz: timezone | None = None) -> datetime:
    """
    Get current datetime.

    Args:
        tz: Timezone. Defaults to UTC.

    Returns:
        Current datetime object.

    Examples:
        >>> datetime_now()
        datetime.datetime(2025, 12, 27, ...)
        >>> datetime_now(timezone.utc)
        datetime.datetime(2025, 12, 27, ..., tzinfo=...)

    Notes:
        Uses timezone-aware datetime.
        Defaults to UTC if no timezone provided.
    """
    target_tz = tz if tz is not None else timezone.utc
    return datetime.now(target_tz)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["datetime_now"]
