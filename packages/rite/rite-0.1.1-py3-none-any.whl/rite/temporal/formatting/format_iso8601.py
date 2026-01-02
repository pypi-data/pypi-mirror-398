# =============================================================================
# Docstring
# =============================================================================

"""
Format ISO 8601
===============

Format datetime to ISO 8601 string.

Examples
--------
>>> from rite.temporal.formatting import format_iso8601
>>> from datetime import datetime, timezone
>>> format_iso8601(datetime(2024, 12, 27, tzinfo=timezone.utc))

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


def format_iso8601(dt: datetime) -> str:
    """
    Format datetime to ISO 8601 string.

    Args:
        dt: Datetime object.

    Returns:
        ISO 8601 formatted string.

    Examples:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(2024, 12, 27, 15, 30, tzinfo=timezone.utc)
        >>> format_iso8601(dt)
        '2024-12-27T15:30:00+00:00'

    Notes:
        Same as datetime.isoformat().
    """
    return dt.isoformat()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["format_iso8601"]
