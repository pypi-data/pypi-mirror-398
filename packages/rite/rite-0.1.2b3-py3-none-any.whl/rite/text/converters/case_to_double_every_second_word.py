# =============================================================================
# Docstring
# =============================================================================

"""
Double Every Second Word Converter
==================================

Double every second word in text.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def to_double_every_second_word_case(text: str) -> str:
    """
    Doubles every second word in the text.

    Args:
        text: The text to process

    Returns:
        The text with every second word doubled

    Example:
        >>> to_double_every_second_word_case("Hello world program")
        'Hello Hello world world program program'
    """
    words = text.split()
    return " ".join(
        word if i % 2 == 0 else word + " " + word
        for i, word in enumerate(words)
    )


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "to_double_every_second_word_case",
]
