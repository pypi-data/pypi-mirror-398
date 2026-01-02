# =============================================================================
# Docstring
# =============================================================================

"""
Entity Encoder
==============

Encode text to HTML entities.

Examples
--------
>>> from rite.markup.entities import entities_encode
>>> entities_encode("café")
'caf&#233;'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def entities_encode(text: str, ascii_only: bool = False) -> str:
    """
    Encode text to HTML entities.

    Args:
        text: Text to encode.
        ascii_only: Encode only non-ASCII characters.

    Returns:
        Entity-encoded text.

    Examples:
        >>> entities_encode("©")
        '&#169;'
        >>> entities_encode("Hello", ascii_only=True)
        'Hello'

    Notes:
        Converts characters to &#N; format.
        Useful for encoding special characters.
    """
    if ascii_only:
        return "".join(f"&#{ord(c)};" if ord(c) > 127 else c for c in text)
    return "".join(f"&#{ord(c)};" for c in text)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["entities_encode"]
