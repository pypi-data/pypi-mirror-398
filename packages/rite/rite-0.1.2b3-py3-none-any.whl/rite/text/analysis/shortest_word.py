# =============================================================================
# Docstring
# =============================================================================

"""
Shortest Word Finder
===================

Find the shortest word in text.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def shortest_word(text: str) -> str:
    """
    Find the shortest word in text.

    Args:
        text: Input text string

    Returns:
        The shortest word

    Raises:
        ValueError: If text contains no words

    Example:
        >>> shortest_word("hello world")
        'hello'
    """
    words = text.split()
    if not words:
        raise ValueError("Text contains no words")
    return min(words, key=len)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "shortest_word",
]
