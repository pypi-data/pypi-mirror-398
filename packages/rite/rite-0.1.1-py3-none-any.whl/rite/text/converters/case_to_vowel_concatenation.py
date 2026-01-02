# =============================================================================
# Docstring
# =============================================================================

"""
Vowel Concatenation Converter
=============================

Concatenate all vowels from text.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def to_vowel_concatenation_case(text: str) -> str:
    """
    Concatenates all vowels from the text.

    Args:
        text: The text to process

    Returns:
        A string of all vowels concatenated

    Example:
        >>> to_vowel_concatenation_case("Hello World")
        'eoo'
    """
    vowels = "aeiouAEIOU"
    return "".join(char for char in text if char in vowels)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "to_vowel_concatenation_case",
]
