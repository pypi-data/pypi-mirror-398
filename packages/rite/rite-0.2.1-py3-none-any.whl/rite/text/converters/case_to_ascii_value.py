# =============================================================================
# Docstring
# =============================================================================

"""
ASCII Value Converter
====================

Convert characters to ASCII values.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def to_ascii_value_case(text: str) -> str:
    """
    Converts each character to its ASCII value.

    Args:
        text: The text to convert

    Returns:
        A string of ASCII values for each character

    Example:
        >>> to_ascii_value_case("AB")
        '65 66'
    """
    return " ".join(str(ord(char)) for char in text)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "to_ascii_value_case",
]
