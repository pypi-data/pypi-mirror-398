# =============================================================================
# Docstring
# =============================================================================

"""
HTML Escaper
============

Escape special HTML characters.

Examples
--------
>>> from rite.markup.html import html_escape
>>> html_escape("<div>Hello & goodbye</div>")
'&lt;div&gt;Hello &amp; goodbye&lt;/div&gt;'

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


def html_escape(text: str) -> str:
    """
    Escape special HTML characters.

    Args:
        text: Text to escape.

    Returns:
        HTML-escaped text.

    Examples:
        >>> html_escape("5 < 10 & 10 > 5")
        '5 &lt; 10 &amp; 10 &gt; 5'
        >>> html_escape('"quoted"')
        '&quot;quoted&quot;'

    Notes:
        Escapes: &, <, >, ", '
        Uses html.escape from standard library.
    """
    return html.escape(text, quote=True)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["html_escape"]
