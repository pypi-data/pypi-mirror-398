# =============================================================================
# Docstring
# =============================================================================

"""
Markdown Module
===============

Markdown processing utilities.

This submodule provides utilities for converting and escaping
Markdown content.

Examples
--------
>>> from rite.markup.markdown import (
...     markdown_to_html,
...     markdown_escape
... )
>>> markdown_to_html("**bold**")
'<strong>bold</strong>'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .markdown_escape import markdown_escape
from .markdown_to_html import markdown_to_html

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "markdown_to_html",
    "markdown_escape",
]
