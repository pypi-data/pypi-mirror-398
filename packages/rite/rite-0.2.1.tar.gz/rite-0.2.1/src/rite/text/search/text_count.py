# =============================================================================
# Docstring
# =============================================================================

"""
Text Count
==========

Count substring occurrences in text.

Examples
--------
>>> from rite.text.search import text_count
>>> text_count("Hello Hello World", "Hello")
2

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def text_count(text: str, substring: str) -> int:
    """
    Count substring occurrences.

    Args:
        text: Text to search in.
        substring: Substring to count.

    Returns:
        Number of non-overlapping occurrences.

    Examples:
        >>> text_count("Hello Hello World", "Hello")
        2
        >>> text_count("aaa", "aa")
        1

    Notes:
        Uses str.count() which counts non-overlapping occurrences.
    """
    return text.count(substring)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["text_count"]
