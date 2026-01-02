# =============================================================================
# Docstring
# =============================================================================

"""
Title Case Conversion
======================

Convert text to Title Case format.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def to_title_case(text: str) -> str:
    """
    Convert text to Title Case.

    Converts the input text to title case where the first letter of each
    word is capitalized.

    Args:
        text: The text to convert.

    Returns:
        The text converted to Title Case.

    Example:
        >>> to_title_case("hello world")
        'Hello World'
        >>> to_title_case("HELLO WORLD")
        'Hello World'
    """
    return text.title()


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "to_title_case",
]
