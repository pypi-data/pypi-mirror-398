# =============================================================================
# Docstring
# =============================================================================

"""
Path Case Conversion
=====================

Convert text to path/case format.

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


def to_path_case(text: str) -> str:
    """
    Convert text to path/case.

    Converts the input text to path case by replacing spaces and special
    characters with forward slashes and converting to lowercase.

    Args:
        text: The text to convert.

    Returns:
        The text converted to path/case.

    Example:
        >>> to_path_case("Hello World")
        'hello/world'
        >>> to_path_case("helloWorld")
        'hello/world'
    """
    # Handle camelCase and PascalCase
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1/\2", text)
    # Replace non-alphanumeric characters with slashes
    text = re.sub(r"[^a-zA-Z0-9]+", "/", text)
    # Convert to lowercase and strip leading/trailing slashes
    return text.lower().strip("/")


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "to_path_case",
]
