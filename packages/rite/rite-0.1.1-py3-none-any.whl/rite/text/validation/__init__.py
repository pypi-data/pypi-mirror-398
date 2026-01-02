# =============================================================================
# Docstring
# =============================================================================

"""
Validation Module
=================

Text validation utilities.

This submodule provides utilities for validating text formats
and content types.

Examples
--------
>>> from rite.text.validation import text_is_email, text_is_numeric
>>> text_is_email("user@example.com")
True
>>> text_is_numeric("123")
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .text_is_alpha import text_is_alpha
from .text_is_alphanumeric import text_is_alphanumeric
from .text_is_email import text_is_email
from .text_is_numeric import text_is_numeric

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "text_is_email",
    "text_is_numeric",
    "text_is_alpha",
    "text_is_alphanumeric",
]
