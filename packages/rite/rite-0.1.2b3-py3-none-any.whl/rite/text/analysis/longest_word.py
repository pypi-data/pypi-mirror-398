# =============================================================================
# Docstring
# =============================================================================

"""
Longest Word Finder
==================

Find the longest word in text.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def longest_word(text: str) -> str:
    """
    Find the longest word in text.

    Args:
        text: Input text string

    Returns:
        The longest word

    Raises:
        ValueError: If text contains no words

    Example:
        >>> longest_word("hello world")
        'hello'
    """
    words = text.split()
    if not words:
        raise ValueError("Text contains no words")
    return max(words, key=len)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "longest_word",
]
