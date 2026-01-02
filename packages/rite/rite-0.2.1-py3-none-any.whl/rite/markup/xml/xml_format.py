# =============================================================================
# Docstring
# =============================================================================

"""
XML Formatter
=============

Format XML with proper indentation.

Examples
--------
>>> from rite.markup.xml import xml_format
>>> xml_format("<root><child>text</child></root>")  # doctest: +SKIP
'<root>\\n  <child>text</child>\\n</root>'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import xml.dom.minidom

# =============================================================================
# Functions
# =============================================================================


def xml_format(xml_string: str, indent: str = "  ") -> str:
    """
    Format XML string with indentation.

    Args:
        xml_string: Unformatted XML string.
        indent: Indentation string (default: 2 spaces).

    Returns:
        Formatted XML string.

    Examples:
        >>> xml = "<root><child>text</child></root>"
        >>> formatted = xml_format(xml)  # doctest: +SKIP
        >>> print(formatted)  # doctest: +SKIP
        <root>
          <child>text</child>
        </root>

    Notes:
        Uses xml.dom.minidom for formatting.
        May fail on malformed XML.
    """
    try:
        dom = xml.dom.minidom.parseString(xml_string)
        return dom.toprettyxml(indent=indent)
    except Exception as e:
        raise ValueError(f"Invalid XML: {e}") from e


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["xml_format"]
