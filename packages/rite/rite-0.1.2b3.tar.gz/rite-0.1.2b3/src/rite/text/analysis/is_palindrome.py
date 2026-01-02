# =============================================================================
# Docstring
# =============================================================================

"""
Palindrome Checker
==================

Check if text is a palindrome.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def is_palindrome(
    text: str,
    ignore_case: bool = True,
    ignore_spaces: bool = True,
) -> bool:
    """
    Check if text is a palindrome.

    Args:
        text: Input text string
        ignore_case: Whether to ignore case differences
        ignore_spaces: Whether to ignore spaces and non-alphanumeric

    Returns:
        True if text is a palindrome, False otherwise

    Example:
        >>> is_palindrome("A man a plan a canal Panama")
        True
    """
    if ignore_spaces:
        cleaned = "".join(char for char in text if char.isalnum())
    else:
        cleaned = text

    if ignore_case:
        cleaned = cleaned.lower()

    return cleaned == cleaned[::-1]


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "is_palindrome",
]
