# =============================================================================
# Docstring
# =============================================================================

"""
Text Is Email
=============

Validate email address format.

Examples
--------
>>> from rite.text.validation import text_is_email
>>> text_is_email("user@example.com")
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import re

# =============================================================================
# Functions
# =============================================================================


def text_is_email(text: str) -> bool:
    """
    Check if text is valid email format.

    Args:
        text: String to validate.

    Returns:
        True if valid email format, False otherwise.

    Examples:
        >>> text_is_email("user@example.com")
        True
        >>> text_is_email("invalid.email")
        False

    Notes:
        Basic email validation using regex.
        Not RFC-compliant, for simple checks only.
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, text))


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["text_is_email"]
