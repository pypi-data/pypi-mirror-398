# =============================================================================
# Docstring
# =============================================================================

"""
Text Is Numeric
===============

Check if text is numeric.

Examples
--------
>>> from rite.text.validation import text_is_numeric
>>> text_is_numeric("123")
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


def text_is_numeric(text: str) -> bool:
    """
    Check if text contains only numeric characters.

    Args:
        text: String to validate.

    Returns:
        True if numeric, False otherwise.

    Examples:
        >>> text_is_numeric("123")
        True
        >>> text_is_numeric("12.34")
        False
        >>> text_is_numeric("abc")
        False

    Notes:
        Uses str.isnumeric() method.
        Returns False for floats with decimals.
    """
    return text.isnumeric()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["text_is_numeric"]
