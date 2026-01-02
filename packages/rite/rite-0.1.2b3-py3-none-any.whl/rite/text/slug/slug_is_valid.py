# =============================================================================
# Docstring
# =============================================================================

"""
Is Valid Slug Function
=======================

Validate slug format.

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


def is_valid_slug(slug: str, delimiter: str = "-") -> bool:
    """
    Validate if a string is a valid slug.

    A valid slug contains only lowercase letters, numbers, and delimiters,
    and does not start or end with a delimiter.

    Args:
        slug: The string to validate.
        delimiter: The delimiter used in the slug (default: "-").

    Returns:
        True if the string is a valid slug, False otherwise.

    Example:
        >>> is_valid_slug("hello-world")
        True
        >>> is_valid_slug("Hello-World")
        False
        >>> is_valid_slug("-hello-world")
        False
        >>> is_valid_slug("hello--world")
        False
    """
    pattern = re.compile(f"^[a-z0-9]+(?:{re.escape(delimiter)}[a-z0-9]+)*$")
    return bool(pattern.match(slug))


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "is_valid_slug",
]
