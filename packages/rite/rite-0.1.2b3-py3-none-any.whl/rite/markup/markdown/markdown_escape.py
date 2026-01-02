# =============================================================================
# Docstring
# =============================================================================

"""
Markdown Escape
===============

Escape Markdown special characters.

Examples
--------
>>> from rite.markup.markdown import markdown_escape
>>> markdown_escape("*not italic*")
'\\\\*not italic\\\\*'

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


def markdown_escape(text: str) -> str:
    """
    Escape Markdown special characters.

    Args:
        text: Text to escape.

    Returns:
        Escaped text.

    Examples:
        >>> markdown_escape("# Not a heading")
        '\\\\# Not a heading'
        >>> markdown_escape("[not](link)")
        '\\\\[not\\\\]\\\\(link\\\\)'

    Notes:
        Escapes: *, _, #, [, ], (, ), `, ~
        Prevents Markdown interpretation.
    """
    special_chars = r"[\*_#\[\]\(\)`~]"
    return re.sub(special_chars, r"\\\\\g<0>", text)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["markdown_escape"]
