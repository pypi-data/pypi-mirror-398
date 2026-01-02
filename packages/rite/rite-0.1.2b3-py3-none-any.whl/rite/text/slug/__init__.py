# =============================================================================
# Docstring
# =============================================================================

"""
Slug Generation Module
=======================

Functions for generating URL-friendly slugs.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .slug_add_prefix import add_slug_prefix
from .slug_add_suffix import add_slug_suffix
from .slug_is_valid import is_valid_slug
from .slug_unique import unique_slug
from .slugify import slugify

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "add_slug_prefix",
    "add_slug_suffix",
    "is_valid_slug",
    "slugify",
    "unique_slug",
]
