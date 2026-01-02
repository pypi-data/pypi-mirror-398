# =============================================================================
# Docstring
# =============================================================================

"""
Entities Module
===============

HTML entity encoding and decoding utilities.

This submodule provides utilities for encoding text to HTML
entities and decoding entities back to text.

Examples
--------
>>> from rite.markup.entities import (
...     entities_encode,
...     entities_decode
... )
>>> entities_encode("©")
'&#169;'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .entities_decode import entities_decode
from .entities_encode import entities_encode

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "entities_encode",
    "entities_decode",
]
