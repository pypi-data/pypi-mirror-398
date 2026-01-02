# =============================================================================
# Docstring
# =============================================================================

"""
Text Is Alpha
=============

Check if text is alphabetic.

Examples
--------
>>> from rite.text.validation import text_is_alpha
>>> text_is_alpha("Hello")
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


def text_is_alpha(text: str) -> bool:
    """
    Check if text contains only alphabetic characters.

    Args:
        text: String to validate.

    Returns:
        True if alphabetic, False otherwise.

    Examples:
        >>> text_is_alpha("Hello")
        True
        >>> text_is_alpha("Hello123")
        False

    Notes:
        Uses str.isalpha() method.
    """
    return text.isalpha()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["text_is_alpha"]
