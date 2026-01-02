# =============================================================================
# Docstring
# =============================================================================

"""
Pascal Case Conversion
=======================

Convert text to PascalCase format.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import re

# =============================================================================
# Functions
# =============================================================================


def to_pascal_case(text: str) -> str:
    """
    Convert text to PascalCase.

    Converts the input text to Pascal case where all words are capitalized
    and joined without separators.

    Args:
        text: The text to convert.

    Returns:
        The text converted to PascalCase.

    Example:
        >>> to_pascal_case("hello world")
        'HelloWorld'
        >>> to_pascal_case("hello_world")
        'HelloWorld'
    """
    # Split on non-alphanumeric characters
    words = re.split(r"[^a-zA-Z0-9]+", text)
    words = [w for w in words if w]  # Remove empty strings

    return "".join(word.capitalize() for word in words)


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "to_pascal_case",
]
