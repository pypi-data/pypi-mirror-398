# =============================================================================
# Docstring
# =============================================================================

"""
Text Starts With
================

Check if text starts with prefix.

Examples
--------
>>> from rite.text.search import text_starts_with
>>> text_starts_with("Hello World", "Hello")
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def text_starts_with(text: str, prefix: str) -> bool:
    """
    Check if text starts with prefix.

    Args:
        text: Text to check.
        prefix: Prefix to search for.

    Returns:
        True if text starts with prefix.

    Examples:
        >>> text_starts_with("Hello World", "Hello")
        True
        >>> text_starts_with("Hello", "World")
        False

    Notes:
        Uses str.startswith() method.
    """
    return text.startswith(prefix)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["text_starts_with"]
