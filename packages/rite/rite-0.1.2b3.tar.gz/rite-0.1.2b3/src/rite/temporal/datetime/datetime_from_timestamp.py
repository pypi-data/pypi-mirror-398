# =============================================================================
# Docstring
# =============================================================================

"""
DateTime From Timestamp
=======================

Create datetime from UNIX timestamp.

Examples
--------
>>> from rite.temporal.datetime import datetime_from_timestamp
>>> datetime_from_timestamp(1735315200)

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


def datetime_from_timestamp(
    timestamp: int | float, tz: timezone | None = None
) -> datetime:
    """
    Create datetime from UNIX timestamp.

    Args:
        timestamp: UNIX timestamp (seconds since epoch).
        tz: Timezone. Defaults to UTC.

    Returns:
        Datetime object.

    Examples:
        >>> datetime_from_timestamp(1735315200)
        datetime.datetime(2024, 12, 27, ...)
        >>> datetime_from_timestamp(0, timezone.utc)
        datetime.datetime(1970, 1, 1, 0, 0, tzinfo=...)

    Notes:
        Handles both int and float timestamps.
        Defaults to UTC timezone.
    """
    target_tz = tz if tz is not None else timezone.utc
    return datetime.fromtimestamp(timestamp, tz=target_tz)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["datetime_from_timestamp"]
