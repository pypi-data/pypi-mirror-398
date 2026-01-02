# =============================================================================
# Docstring
# =============================================================================

"""
DateTime To ISO
===============

Convert datetime to ISO 8601 string.

Examples
--------
>>> from rite.temporal.datetime import datetime_to_iso
>>> from datetime import datetime
>>> datetime_to_iso(datetime.now())

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


def datetime_to_iso(dt: datetime) -> str:
    """
    Convert datetime to ISO 8601 string.

    Args:
        dt: Datetime object.

    Returns:
        ISO 8601 formatted string.

    Examples:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(2024, 12, 27, 15, 30, tzinfo=timezone.utc)
        >>> datetime_to_iso(dt)
        '2024-12-27T15:30:00+00:00'

    Notes:
        Uses isoformat() method.
        Includes timezone if present.
    """
    return dt.isoformat()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["datetime_to_iso"]
