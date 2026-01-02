# =============================================================================
# Docstring
# =============================================================================

"""
DateTime Parse
==============

Parse datetime from string.

Examples
--------
>>> from rite.temporal.datetime import datetime_parse
>>> datetime_parse("2024-12-27", "%Y-%m-%d")

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


def datetime_parse(
    date_string: str, fmt: str = "%Y-%m-%d %H:%M:%S"
) -> datetime:
    """
    Parse datetime from string.

    Args:
        date_string: Date/time string.
        fmt: Format string. Defaults to "%Y-%m-%d %H:%M:%S".

    Returns:
        Parsed datetime object.

    Examples:
        >>> datetime_parse("2024-12-27", "%Y-%m-%d")
        datetime.datetime(2024, 12, 27, 0, 0)
        >>> datetime_parse("27/12/2024 15:30", "%d/%m/%Y %H:%M")
        datetime.datetime(2024, 12, 27, 15, 30)

    Notes:
        See strftime documentation for format codes.
        Returns naive datetime (no timezone).
    """
    return datetime.strptime(date_string, fmt)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["datetime_parse"]
