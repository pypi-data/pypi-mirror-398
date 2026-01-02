# =============================================================================
# Docstring
# =============================================================================

"""
Rite - String - String to Datetime Converter Module
===================================================

Provides functionality to convert strings to datetime values.

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


def convert_string_to_datetime(
    value: str | None,
) -> datetime | None:
    """
    String to Datetime Converter
    ============================

    Convert a string to a timezone-aware datetime object (UTC).

    Parses a timestamp like '2024-12-11 11:42:34.049271+00' or ISO-ish strings.
    Returns None on blank or invalid input.

    Supports ISO 8601 format with optional timezone.
    Naive datetimes are converted to UTC.

    Args:
        value: The string to convert.

    Returns:
        A timezone-aware datetime object in UTC, or None.
    """
    if not value:
        return None

    s = str(value).strip()
    if not s or s.lower() in {"none", "null"}:
        return None

    # Normalize space→T so fromisoformat() accepts it with offset
    s = s.replace(" ", "T", 1) if " " in s and "T" not in s else s

    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "convert_string_to_datetime",
]
