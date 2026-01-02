# =============================================================================
# Docstring
# =============================================================================

"""
Hexadecimal Converter
====================

Convert text to hexadecimal form.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def to_hexadecimal_case(text: str) -> str:
    """
    Convert the text to hexadecimal form.

    Args:
        text: The text to convert

    Returns:
        The text in hexadecimal form

    Example:
        >>> to_hexadecimal_case("AB")
        '41 42'
    """
    return " ".join(format(ord(char), "x") for char in text)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "to_hexadecimal_case",
]
