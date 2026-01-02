# =============================================================================
# Docstring
# =============================================================================

"""
DateTime To Timestamp
=====================

Convert datetime to UNIX timestamp.

Examples
--------
>>> from rite.temporal.datetime import datetime_to_timestamp
>>> from datetime import datetime
>>> datetime_to_timestamp(datetime(2024, 12, 27))

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from datetime import datetime

# =============================================================================
# Functions
# =============================================================================


def datetime_to_timestamp(dt: datetime) -> int:
    """
    Convert datetime to UNIX timestamp.

    Args:
        dt: Datetime object.

    Returns:
        UNIX timestamp as integer.

    Examples:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(1970, 1, 1, tzinfo=timezone.utc)
        >>> datetime_to_timestamp(dt)
        0

    Notes:
        Returns integer (seconds).
        For milliseconds, use int(dt.timestamp() * 1000).
    """
    return int(dt.timestamp())


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["datetime_to_timestamp"]
