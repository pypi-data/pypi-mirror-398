# =============================================================================
# Docstring
# =============================================================================

"""
Search Module
=============

Text search utilities.

This submodule provides utilities for searching within text including
contains, starts_with, ends_with, find, and count operations.

Examples
--------
>>> from rite.text.search import text_contains, text_find
>>> text_contains("Hello World", "World")
True
>>> text_find("Hello World", "World")
6

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .text_contains import text_contains
from .text_count import text_count
from .text_ends_with import text_ends_with
from .text_find import text_find
from .text_starts_with import text_starts_with

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "text_contains",
    "text_starts_with",
    "text_ends_with",
    "text_find",
    "text_count",
]
