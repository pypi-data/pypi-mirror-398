# =============================================================================
# Docstring
# =============================================================================

"""
Text Ends With
==============

Check if text ends with suffix.

Examples
--------
>>> from rite.text.search import text_ends_with
>>> text_ends_with("Hello World", "World")
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


def text_ends_with(text: str, suffix: str) -> bool:
    """
    Check if text ends with suffix.

    Args:
        text: Text to check.
        suffix: Suffix to search for.

    Returns:
        True if text ends with suffix.

    Examples:
        >>> text_ends_with("Hello World", "World")
        True
        >>> text_ends_with("Hello", "World")
        False

    Notes:
        Uses str.endswith() method.
    """
    return text.endswith(suffix)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["text_ends_with"]
