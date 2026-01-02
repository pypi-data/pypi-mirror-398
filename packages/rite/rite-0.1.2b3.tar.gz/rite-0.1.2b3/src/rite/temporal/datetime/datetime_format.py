# =============================================================================
# Docstring
# =============================================================================

"""
DateTime Format
===============

Format datetime to string.

Examples
--------
>>> from rite.temporal.datetime import datetime_format
>>> from datetime import datetime
>>> datetime_format(datetime.now())

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


def datetime_format(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime to string.

    Args:
        dt: Datetime object.
        fmt: Format string. Defaults to "%Y-%m-%d %H:%M:%S".

    Returns:
        Formatted datetime string.

    Examples:
        >>> from datetime import datetime
        >>> dt = datetime(2024, 12, 27, 15, 30)
        >>> datetime_format(dt)
        '2024-12-27 15:30:00'
        >>> datetime_format(dt, "%d/%m/%Y")
        '27/12/2024'

    Notes:
        See strftime documentation for format codes.
    """
    return dt.strftime(fmt)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["datetime_format"]
