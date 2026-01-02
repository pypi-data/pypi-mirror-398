# =============================================================================
# Docstring
# =============================================================================

"""
Text Is Alphanumeric
====================

Check if text is alphanumeric.

Examples
--------
>>> from rite.text.validation import text_is_alphanumeric
>>> text_is_alphanumeric("Hello123")
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def text_is_alphanumeric(text: str) -> bool:
    """
    Check if text contains only alphanumeric characters.

    Args:
        text: String to validate.

    Returns:
        True if alphanumeric, False otherwise.

    Examples:
        >>> text_is_alphanumeric("Hello123")
        True
        >>> text_is_alphanumeric("Hello 123")
        False

    Notes:
        Uses str.isalnum() method.
    """
    return text.isalnum()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["text_is_alphanumeric"]
