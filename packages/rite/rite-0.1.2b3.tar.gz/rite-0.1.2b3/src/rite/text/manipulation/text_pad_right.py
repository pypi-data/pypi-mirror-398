# =============================================================================
# Docstring
# =============================================================================

"""
Text Pad Right
==============

Pad text on the right.

Examples
--------
>>> from rite.text.manipulation import text_pad_right
>>> text_pad_right("Hi", 5)
'Hi   '

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def text_pad_right(text: str, width: int, fill_char: str = " ") -> str:
    """
    Pad text on the right to width.

    Args:
        text: Text to pad.
        width: Target width.
        fill_char: Character to pad with.

    Returns:
        Right-padded text.

    Examples:
        >>> text_pad_right("Hi", 5)
        'Hi   '
        >>> text_pad_right("5", 3, "0")
        '500'

    Notes:
        Uses str.ljust() method.
    """
    return text.ljust(width, fill_char)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["text_pad_right"]
