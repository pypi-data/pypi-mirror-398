# =============================================================================
# Docstring
# =============================================================================

"""
Text Truncate
=============

Truncate text to maximum length.

Examples
--------
>>> from rite.text.manipulation import text_truncate
>>> text_truncate("Hello World", 5)
'Hello...'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def text_truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate.
        max_length: Maximum length (including suffix).
        suffix: Suffix to add when truncated.

    Returns:
        Truncated text with suffix if needed.

    Examples:
        >>> text_truncate("Hello World", 5)
        'Hello...'
        >>> text_truncate("Hi", 10)
        'Hi'

    Notes:
        Suffix length is included in max_length.
    """
    if len(text) <= max_length:
        return text

    truncate_at = max_length - len(suffix)
    if truncate_at < 0:
        truncate_at = 0

    return text[:truncate_at] + suffix


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["text_truncate"]
