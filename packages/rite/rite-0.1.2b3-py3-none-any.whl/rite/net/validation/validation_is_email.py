# =============================================================================
# Docstring
# =============================================================================

"""
Email Validator
===============

Validate email address format.

Examples
--------
>>> from rite.net.validation import validation_is_email
>>> validation_is_email("user@example.com")
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


def validation_is_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate.

    Returns:
        True if valid email format.

    Examples:
        >>> validation_is_email("user@example.com")
        True
        >>> validation_is_email("invalid.email")
        False
        >>> validation_is_email("test+tag@domain.co.uk")
        True

    Notes:
        Basic validation using regex.
        Does not verify email existence.
    """
    pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    return bool(pattern.match(email))


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["validation_is_email"]
