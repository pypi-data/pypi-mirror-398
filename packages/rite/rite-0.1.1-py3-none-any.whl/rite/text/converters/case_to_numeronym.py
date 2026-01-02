# =============================================================================
# Docstring
# =============================================================================

"""
Numeronym Converter
===================

Convert words to numeronym format.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def to_numeronym_case(text: str) -> str:
    """
    Converts a word into a numeronym.

    Args:
        text: The word to convert

    Returns:
        The word converted into a numeronym

    Example:
        >>> to_numeronym_case("Internationalization")
        'I18n'
    """
    if len(text) <= 3:
        return text
    return text[0] + str(len(text) - 2) + text[-1]


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "to_numeronym_case",
]
