# =============================================================================
# Docstring
# =============================================================================

"""
Snake Case Conversion
======================

Convert text to snake_case format.

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


def to_snake_case(text: str) -> str:
    """
    Convert text to snake_case.

    Converts the input text to snake case by replacing spaces and special
    characters with underscores and converting to lowercase.

    Args:
        text: The text to convert.

    Returns:
        The text converted to snake_case.

    Example:
        >>> to_snake_case("Hello World")
        'hello_world'
        >>> to_snake_case("helloWorld")
        'hello_world'
    """
    # Handle camelCase and PascalCase
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    # Replace non-alphanumeric characters with underscores
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text)
    # Convert to lowercase and strip leading/trailing underscores
    return text.lower().strip("_")


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "to_snake_case",
]
