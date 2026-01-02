# =============================================================================
# Docstring
# =============================================================================

"""
HTML Module
===========

HTML processing utilities.

This submodule provides utilities for cleaning, escaping,
and manipulating HTML content.

Examples
--------
>>> from rite.markup.html import (
...     html_clean,
...     html_escape,
...     html_unescape
... )
>>> html_clean("<p>Hello</p>")
'Hello'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .html_clean import html_clean
from .html_escape import html_escape
from .html_strip_tags import html_strip_tags
from .html_unescape import html_unescape

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "html_clean",
    "html_escape",
    "html_unescape",
    "html_strip_tags",
]
