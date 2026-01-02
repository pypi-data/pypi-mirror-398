# =============================================================================
# Docstring
# =============================================================================

"""
Format RFC 3339
===============

Format datetime to RFC 3339 string.

Examples
--------
>>> from rite.temporal.formatting import format_rfc3339
>>> from datetime import datetime, timezone
>>> format_rfc3339(datetime(2024, 12, 27, tzinfo=timezone.utc))

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


def format_rfc3339(dt: datetime) -> str:
    """
    Format datetime to RFC 3339 string.

    Args:
        dt: Datetime object.

    Returns:
        RFC 3339 formatted string.

    Examples:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(2024, 12, 27, 15, 30, tzinfo=timezone.utc)
        >>> format_rfc3339(dt)
        '2024-12-27T15:30:00+00:00'

    Notes:
        RFC 3339 is profile of ISO 8601.
        Uses isoformat() with 'T' separator.
    """
    return dt.isoformat()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["format_rfc3339"]
