# =============================================================================
# Docstring
# =============================================================================

"""
HTML Cleaner
============

Remove HTML tags from text.

Examples
--------
>>> from rite.markup.html import html_clean
>>> html_clean("<p>Hello <b>World</b></p>")
'Hello World'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import re

# =============================================================================
# Functions
# =============================================================================


def html_clean(
    raw_html: str,
    strip: bool = True,
) -> str:
    """
    Remove HTML tags from string.

    Args:
        raw_html: Raw HTML string to clean.
        strip: Strip whitespace from result.

    Returns:
        Cleaned text without HTML tags.

    Examples:
        >>> html_clean("<p>Hello</p>")
        'Hello'
        >>> html_clean("<div>  Text  </div>", strip=False)
        '  Text  '

    Notes:
        Uses regex to remove tags.
        Does not parse HTML structure.
    """
    pattern = re.compile(r"<.*?>")
    cleaned = re.sub(pattern, "", raw_html)
    return cleaned.strip() if strip else cleaned


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["html_clean"]
