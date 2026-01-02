# =============================================================================
# Docstring
# =============================================================================

"""
Dot Case Conversion
====================

Convert text to dot.case format.

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


def to_dot_case(text: str) -> str:
    """
    Convert text to dot.case.

    Converts the input text to dot case by replacing spaces and special
    characters with dots and converting to lowercase.

    Args:
        text: The text to convert.

    Returns:
        The text converted to dot.case.

    Example:
        >>> to_dot_case("Hello World")
        'hello.world'
        >>> to_dot_case("helloWorld")
        'hello.world'
    """
    # Handle camelCase and PascalCase
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1.\2", text)
    # Replace non-alphanumeric characters with dots
    text = re.sub(r"[^a-zA-Z0-9]+", ".", text)
    # Convert to lowercase and strip leading/trailing dots
    return text.lower().strip(".")


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "to_dot_case",
]
