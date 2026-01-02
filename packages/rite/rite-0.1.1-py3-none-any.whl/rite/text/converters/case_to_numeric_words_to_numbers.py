# =============================================================================
# Docstring
# =============================================================================

"""
Numeric Words to Numbers Converter
===================================

Convert numeric words to numeral equivalents.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def to_numeric_words_to_numbers_case(text: str) -> str:
    """
    Converts numeric words to their numeral equivalents.

    Args:
        text: The text to convert

    Returns:
        The text with numeric words converted to numbers

    Example:
        >>> to_numeric_words_to_numbers_case("one two three")
        '1 2 3'
    """
    num_dict = {
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
        "zero": "0",
    }
    return " ".join(num_dict.get(word, word) for word in text.split())


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "to_numeric_words_to_numbers_case",
]
