# =============================================================================
# Docstring
# =============================================================================

"""
Sentence Case Conversion
=========================

Convert text to Sentence case format.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def to_sentence_case(text: str) -> str:
    """
    Convert text to Sentence case.

    Converts the input text to sentence case where only the first letter
    of the first word is capitalized and the rest is lowercase.

    Args:
        text: The text to convert.

    Returns:
        The text converted to Sentence case.

    Example:
        >>> to_sentence_case("hello world")
        'Hello world'
        >>> to_sentence_case("HELLO WORLD")
        'Hello world'
    """
    if not text:
        return text
    return text[0].upper() + text[1:].lower()


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "to_sentence_case",
]
