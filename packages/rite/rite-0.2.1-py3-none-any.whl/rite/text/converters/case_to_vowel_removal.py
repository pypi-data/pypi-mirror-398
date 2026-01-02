# =============================================================================
# Docstring
# =============================================================================

"""
Vowel Removal Converter
=======================

Remove all vowels from text.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def to_vowel_removal_case(text: str) -> str:
    """
    Remove all vowels from the text.

    Args:
        text: The text to convert

    Returns:
        The text with all vowels removed

    Example:
        >>> to_vowel_removal_case("Hello World")
        'Hll Wrld'
    """
    vowels = "aeiouAEIOU"
    return "".join(char for char in text if char not in vowels)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "to_vowel_removal_case",
]
