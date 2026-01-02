# =============================================================================
# Docstring
# =============================================================================

"""
Camel Case Conversion
======================

Convert text to camelCase format.

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


def to_camel_case(text: str) -> str:
    """
    Convert text to camelCase.

    Converts the input text to camel case where the first word is lowercase
    and subsequent words are capitalized.

    Args:
        text: The text to convert.

    Returns:
        The text converted to camelCase.

    Example:
        >>> to_camel_case("hello world")
        'helloWorld'
        >>> to_camel_case("Hello World")
        'helloWorld'

    """

    # Split on non-alphanumeric characters
    words = re.split(r"[^a-zA-Z0-9]+", text)
    words = [w for w in words if w]  # Remove empty strings

    if not words:
        return ""

    return words[0].lower() + "".join(word.capitalize() for word in words[1:])


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "to_camel_case",
]
