# =============================================================================
# Docstring
# =============================================================================

"""
Sanitize Module
===============

Content sanitization utilities.

This submodule provides utilities for sanitizing URLs, filenames,
and HTML content for security.

Examples
--------
>>> from rite.markup.sanitize import (
...     sanitize_url,
...     sanitize_filename,
...     sanitize_html
... )
>>> sanitize_url("javascript:alert(1)")
''

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .sanitize_filename import sanitize_filename
from .sanitize_html import sanitize_html
from .sanitize_url import sanitize_url

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "sanitize_url",
    "sanitize_filename",
    "sanitize_html",
]
