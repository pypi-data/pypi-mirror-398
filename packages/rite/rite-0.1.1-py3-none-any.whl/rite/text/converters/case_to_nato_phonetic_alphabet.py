# =============================================================================
# Docstring
# =============================================================================

"""
NATO Phonetic Alphabet Converter
=================================

Translate text to NATO phonetic alphabet.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def to_nato_phonetic_alphabet_case(text: str) -> str:
    """
    Translates each letter to its corresponding NATO phonetic alphabet word.

    Args:
        text: The text to convert

    Returns:
        The text in NATO phonetic alphabet

    Example:
        >>> to_nato_phonetic_alphabet_case("AB")
        'Alpha Bravo'
    """
    nato_dict = {
        "A": "Alpha",
        "B": "Bravo",
        "C": "Charlie",
        "D": "Delta",
        "E": "Echo",
        "F": "Foxtrot",
        "G": "Golf",
        "H": "Hotel",
        "I": "India",
        "J": "Juliett",
        "K": "Kilo",
        "L": "Lima",
        "M": "Mike",
        "N": "November",
        "O": "Oscar",
        "P": "Papa",
        "Q": "Quebec",
        "R": "Romeo",
        "S": "Sierra",
        "T": "Tango",
        "U": "Uniform",
        "V": "Victor",
        "W": "Whiskey",
        "X": "X-ray",
        "Y": "Yankee",
        "Z": "Zulu",
        " ": " ",
    }
    return " ".join(nato_dict.get(char.upper(), "") for char in text)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "to_nato_phonetic_alphabet_case",
]
