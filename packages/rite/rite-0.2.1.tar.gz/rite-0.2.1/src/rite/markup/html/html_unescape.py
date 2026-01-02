# =============================================================================
# Docstring
# =============================================================================

"""
HTML Unescaper
==============

Unescape HTML entities.

Examples
--------
>>> from rite.markup.html import html_unescape
>>> html_unescape("&lt;div&gt;Hello&lt;/div&gt;")
'<div>Hello</div>'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import html

# =============================================================================
# Functions
# =============================================================================


def html_unescape(text: str) -> str:
    """
    Unescape HTML entities.

    Args:
        text: HTML-escaped text.

    Returns:
        Unescaped text.

    Examples:
        >>> html_unescape("&lt;p&gt;Hello&lt;/p&gt;")
        '<p>Hello</p>'
        >>> html_unescape("&amp;")
        '&'

    Notes:
        Converts entities like &lt; back to <.
        Uses html.unescape from standard library.
    """
    return html.unescape(text)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["html_unescape"]
