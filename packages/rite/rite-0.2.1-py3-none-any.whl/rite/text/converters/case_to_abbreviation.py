# =============================================================================
# Docstring
# =============================================================================

"""
Abbreviation Case Converter
===========================

Convert text to abbreviation format.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def to_abbreviation_case(text: str) -> str:
    """
    Converts text to its abbreviation.

    Example: 'As Soon As Possible' -> 'ASAP'

    Args:
        text: The text to abbreviate

    Returns:
        The abbreviation of the text

    Example:
        >>> to_abbreviation_case("As Soon As Possible")
        'ASAP'
    """
    return "".join(word[0].upper() for word in text.split() if word.isalpha())


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "to_abbreviation_case",
]
