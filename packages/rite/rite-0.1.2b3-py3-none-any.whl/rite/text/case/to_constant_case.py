# =============================================================================
# Docstring
# =============================================================================

"""
Constant Case Conversion
=========================

Convert text to CONSTANT_CASE format.

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


def to_constant_case(text: str) -> str:
    """
    Convert text to CONSTANT_CASE.

    Converts the input text to constant case (screaming snake case) by
    replacing spaces and special characters with underscores and converting
    to uppercase.

    Args:
        text: The text to convert.

    Returns:
        The text converted to CONSTANT_CASE.

    Example:
        >>> to_constant_case("Hello World")
        'HELLO_WORLD'
        >>> to_constant_case("helloWorld")
        'HELLO_WORLD'
    """
    # Handle camelCase and PascalCase
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    # Replace non-alphanumeric characters with underscores
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text)
    # Convert to uppercase and strip leading/trailing underscores
    return text.upper().strip("_")


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "to_constant_case",
]
