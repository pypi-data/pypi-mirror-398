# =============================================================================
# Docstring
# =============================================================================

"""
XML Escaper
===========

Escape special XML characters.

Examples
--------
>>> from rite.markup.xml import xml_escape
>>> xml_escape("<tag>value & more</tag>")
'&lt;tag&gt;value &amp; more&lt;/tag&gt;'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import xml.sax.saxutils

# =============================================================================
# Functions
# =============================================================================


def xml_escape(text: str) -> str:
    """
    Escape special XML characters.

    Args:
        text: Text to escape.

    Returns:
        XML-escaped text.

    Examples:
        >>> xml_escape("5 < 10 & 10 > 5")
        '5 &lt; 10 &amp; 10 &gt; 5'
        >>> xml_escape('"quoted"')
        '&quot;quoted&quot;'

    Notes:
        Escapes: &, <, >, ", '
        Uses xml.sax.saxutils.escape.
    """
    return xml.sax.saxutils.escape(text, {"'": "&apos;", '"': "&quot;"})


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["xml_escape"]
