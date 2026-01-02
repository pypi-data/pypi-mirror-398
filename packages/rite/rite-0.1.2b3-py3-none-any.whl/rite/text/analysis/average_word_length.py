# =============================================================================
# Docstring
# =============================================================================

"""
Average Word Length
==================

Calculate average word length in text.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def average_word_length(text: str) -> float:
    """
    Calculate the average word length in text.

    Args:
        text: Input text string

    Returns:
        Average length of words

    Raises:
        ValueError: If text contains no words

    Example:
        >>> average_word_length("hello world")
        5.0
    """
    words = text.split()
    if not words:
        raise ValueError("Text contains no words")
    return sum(len(word) for word in words) / len(words)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "average_word_length",
]
