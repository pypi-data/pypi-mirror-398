# =============================================================================
# Docstring
# =============================================================================

"""
XML Unescaper
=============

Unescape XML entities.

Examples
--------
>>> from rite.markup.xml import xml_unescape
>>> xml_unescape("&lt;tag&gt;value&lt;/tag&gt;")
'<tag>value</tag>'

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


def xml_unescape(text: str) -> str:
    """
    Unescape XML entities.

    Args:
        text: XML-escaped text.

    Returns:
        Unescaped text.

    Examples:
        >>> xml_unescape("&lt;root&gt;&lt;/root&gt;")
        '<root></root>'
        >>> xml_unescape("&amp;&apos;&quot;")
        "&'\""

    Notes:
        Converts entities like &lt; back to <.
        Uses xml.sax.saxutils.unescape.
    """
    return xml.sax.saxutils.unescape(text, {"&apos;": "'", "&quot;": '"'})


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["xml_unescape"]
