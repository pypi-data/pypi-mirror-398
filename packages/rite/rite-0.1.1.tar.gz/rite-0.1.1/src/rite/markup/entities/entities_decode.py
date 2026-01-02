# =============================================================================
# Docstring
# =============================================================================

"""
Entity Decoder
==============

Decode HTML entities to text.

Examples
--------
>>> from rite.markup.entities import entities_decode
>>> entities_decode("caf&#233;")
'café'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import html

# =============================================================================
# Functions
# =============================================================================


def entities_decode(text: str) -> str:
    """
    Decode HTML entities to text.

    Args:
        text: Entity-encoded text.

    Returns:
        Decoded text.

    Examples:
        >>> entities_decode("&#169;")
        '©'
        >>> entities_decode("&copy;")
        '©'

    Notes:
        Decodes both numeric (&#N;) and named (&copy;).
        Uses html.unescape from standard library.
    """
    return html.unescape(text)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["entities_decode"]
