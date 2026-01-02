# =============================================================================
# Docstring
# =============================================================================

"""
Filename to Date String Module
==============================

Extracts date strings from filenames using pattern matching.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import re


def date_format_to_regex(date_format: str) -> re.Pattern[str]:
    """Convert a simple ``strftime`` format string to a compiled regex.

    This is a lightweight implementation that supports the most common
    directives used in filenames (``%Y``, ``%m``, ``%d``, ``%H``, ``%M``,
    ``%S``). Other characters are treated literally.
    """

    mapping = {
        "%Y": r"(?P<Y>\d{4})",
        "%m": r"(?P<m>\d{2})",
        "%d": r"(?P<d>\d{2})",
        "%H": r"(?P<H>\d{2})",
        "%M": r"(?P<M>\d{2})",
        "%S": r"(?P<S>\d{2})",
    }

    pattern = re.escape(date_format)
    for directive, replacement in mapping.items():
        pattern = pattern.replace(re.escape(directive), replacement)

    return re.compile(pattern)


# =============================================================================
# Functions
# =============================================================================


def filename_to_datestring(
    filename: str,
    date_format: str = "%Y-%m-%d-%H%M%S",
) -> str | None:
    """
    Extract the date string from a filename using the given format.

    Args:
    ----
        filename: Filename to search for date pattern.
        date_format: strftime format string to match against.

    Returns:
    -------
        Date string if found, otherwise None.

    """
    regex = date_format_to_regex(date_format)
    search = regex.search(filename)
    if search:
        # Return the full matched substring so that it can be
        # parsed directly with ``date_format``.
        return search.group(0)
    return None


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "filename_to_datestring",
]
