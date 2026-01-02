# =============================================================================
# Docstring
# =============================================================================

"""
Manipulation Module
===================

Text manipulation utilities.

This submodule provides utilities for manipulating text including
truncation, padding, and wrapping.

Examples
--------
>>> from rite.text.manipulation import text_truncate, text_pad_left
>>> text_truncate("Hello World", 8)
'Hello...'
>>> text_pad_left("5", 3, "0")
'005'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .text_pad_left import text_pad_left
from .text_pad_right import text_pad_right
from .text_truncate import text_truncate
from .text_wrap import text_wrap

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "text_truncate",
    "text_pad_left",
    "text_pad_right",
    "text_wrap",
]
