# =============================================================================
# Docstring
# =============================================================================

"""
Markdown to HTML
================

Convert Markdown to HTML (basic).

Examples
--------
>>> from rite.markup.markdown import markdown_to_html
>>> markdown_to_html("**bold** text")
'<strong>bold</strong> text'

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


def markdown_to_html(markdown: str) -> str:
    """
    Convert basic Markdown to HTML.

    Args:
        markdown: Markdown text.

    Returns:
        HTML string.

    Examples:
        >>> markdown_to_html("# Heading")
        '<h1>Heading</h1>'
        >>> markdown_to_html("**bold** and *italic*")
        '<strong>bold</strong> and <em>italic</em>'

    Notes:
        Basic conversion only.
        Supports: headings, bold, italic, code.
        For full Markdown, use external library.
    """
    html = markdown

    # Headers
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)

    # Bold
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"__(.+?)__", r"<strong>\1</strong>", html)

    # Italic
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    html = re.sub(r"_(.+?)_", r"<em>\1</em>", html)

    # Code
    html = re.sub(r"`(.+?)`", r"<code>\1</code>", html)

    return html


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["markdown_to_html"]
