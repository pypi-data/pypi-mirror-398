# =============================================================================
# Docstring
# =============================================================================

"""
Text Pad Left
=============

Pad text on the left.

Examples
--------
>>> from rite.text.manipulation import text_pad_left
>>> text_pad_left("5", 3, "0")
'005'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def text_pad_left(text: str, width: int, fill_char: str = " ") -> str:
    """
    Pad text on the left to width.

    Args:
        text: Text to pad.
        width: Target width.
        fill_char: Character to pad with.

    Returns:
        Left-padded text.

    Examples:
        >>> text_pad_left("5", 3, "0")
        '005'
        >>> text_pad_left("Hi", 5)
        '   Hi'

    Notes:
        Uses str.rjust() method.
    """
    return text.rjust(width, fill_char)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["text_pad_left"]
