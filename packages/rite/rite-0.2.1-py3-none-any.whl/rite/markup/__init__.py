# =============================================================================
# Docstring
# =============================================================================

"""
Markup Module
=============

Comprehensive markup language processing utilities.

This module provides utilities for HTML, XML, Markdown processing,
entity encoding/decoding, and content sanitization.

Submodules
----------
- html: HTML cleaning, escaping, unescaping, tag stripping
- xml: XML escaping, unescaping, formatting
- markdown: Markdown to HTML conversion, escaping
- entities: HTML entity encoding and decoding
- sanitize: URL, filename, and HTML sanitization

Examples
--------
HTML:
    >>> from rite.markup import html_clean, html_escape
    >>> html_clean("<p>Hello</p>")
    'Hello'
    >>> html_escape("<tag>")
    '&lt;tag&gt;'

XML:
    >>> from rite.markup import xml_escape
    >>> xml_escape("<tag>value</tag>")
    '&lt;tag&gt;value&lt;/tag&gt;'

Markdown:
    >>> from rite.markup import markdown_to_html
    >>> markdown_to_html("**bold**")
    '<strong>bold</strong>'

Entities:
    >>> from rite.markup import entities_encode
    >>> entities_encode("©")
    '&#169;'

Sanitize:
    >>> from rite.markup import sanitize_url
    >>> sanitize_url("javascript:alert(1)")
    ''

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .entities import entities_decode, entities_encode
from .html import html_clean, html_escape, html_strip_tags, html_unescape
from .markdown import markdown_escape, markdown_to_html
from .sanitize import sanitize_filename, sanitize_html, sanitize_url
from .xml import xml_escape, xml_format, xml_unescape

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    # HTML
    # HTML
    "html_clean",
    "html_escape",
    "html_unescape",
    "html_strip_tags",
    # XML
    "xml_escape",
    "xml_unescape",
    "xml_format",
    # Markdown
    "markdown_to_html",
    "markdown_escape",
    # Entities
    "entities_encode",
    "entities_decode",
    # Sanitize
    "sanitize_url",
    "sanitize_filename",
    "sanitize_html",
]
