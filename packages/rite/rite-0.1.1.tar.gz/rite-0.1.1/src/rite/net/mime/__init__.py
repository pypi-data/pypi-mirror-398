# =============================================================================
# Docstring
# =============================================================================

"""
MIME Module
===========

MIME type utilities.

This submodule provides utilities for working with MIME types,
including type guessing and parsing.

Examples
--------
>>> from rite.net.mime import mime_guess_type, mime_parse
>>> mime_guess_type("file.json")
'application/json'
>>> mime_parse("text/html")
('text', 'html')

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .mime_guess_extension import mime_guess_extension
from .mime_guess_type import mime_guess_type
from .mime_parse import mime_parse

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "mime_guess_type",
    "mime_guess_extension",
    "mime_parse",
]
