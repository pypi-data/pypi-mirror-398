# =============================================================================
# Docstring
# =============================================================================

"""
Text Contains
=============

Check if text contains a substring.

Examples
--------
>>> from rite.text.search import text_contains
>>> text_contains("Hello World", "World")
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


def text_contains(text: str, substring: str) -> bool:
    """
    Check if text contains substring.

    Args:
        text: Text to search in.
        substring: Substring to search for.

    Returns:
        True if substring found.

    Examples:
        >>> text_contains("Hello World", "World")
        True
        >>> text_contains("Hello", "Goodbye")
        False

    Notes:
        Case-sensitive search.
    """
    return substring in text


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["text_contains"]
