# =============================================================================
# Docstring
# =============================================================================

"""
Format Human Readable
======================

Format datetime to human-readable string.

Examples
--------
>>> from rite.temporal.formatting import format_human_readable
>>> from datetime import datetime
>>> format_human_readable(datetime(2024, 12, 27, 15, 30))

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


def format_human_readable(dt: datetime) -> str:
    """
    Format datetime to human-readable string.

    Args:
        dt: Datetime object.

    Returns:
        Human-readable formatted string.

    Examples:
        >>> from datetime import datetime
        >>> dt = datetime(2024, 12, 27, 15, 30)
        >>> format_human_readable(dt)
        'December 27, 2024 at 3:30 PM'

    Notes:
        Uses strftime with full month name.
        12-hour format with AM/PM.
    """
    return dt.strftime("%B %d, %Y at %I:%M %p")


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["format_human_readable"]
