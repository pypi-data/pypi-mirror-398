# =============================================================================
# Docstring
# =============================================================================

"""
Text Find
=========

Find substring position in text.

Examples
--------
>>> from rite.text.search import text_find
>>> text_find("Hello World", "World")
6

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def text_find(text: str, substring: str) -> int:
    """
    Find substring position in text.

    Args:
        text: Text to search in.
        substring: Substring to find.

    Returns:
        Index of substring or -1 if not found.

    Examples:
        >>> text_find("Hello World", "World")
        6
        >>> text_find("Hello", "Goodbye")
        -1

    Notes:
        Uses str.find() method. Returns -1 if not found.
    """
    return text.find(substring)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["text_find"]
