# =============================================================================
# Docstring
# =============================================================================

"""
Kebab Case Conversion
======================

Convert text to kebab-case format.

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


def to_kebab_case(text: str) -> str:
    """
    Convert text to kebab-case.

    Converts the input text to kebab case by replacing spaces and special
    characters with hyphens and converting to lowercase.

    Args:
        text: The text to convert.

    Returns:
        The text converted to kebab-case.

    Example:
        >>> to_kebab_case("Hello World")
        'hello-world'
        >>> to_kebab_case("helloWorld")
        'hello-world'
    """
    # Handle camelCase and PascalCase
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", text)
    # Replace non-alphanumeric characters with hyphens
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    # Convert to lowercase and strip leading/trailing hyphens
    return text.lower().strip("-")


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "to_kebab_case",
]
