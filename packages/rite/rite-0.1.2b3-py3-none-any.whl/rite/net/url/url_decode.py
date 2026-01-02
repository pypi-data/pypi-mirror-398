# =============================================================================
# Docstring
# =============================================================================

"""
URL Decoder
===========

Decode URL-encoded text.

Examples
--------
>>> from rite.net.url import url_decode
>>> url_decode("hello%20world")
'hello world'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from urllib.parse import unquote

# =============================================================================
# Functions
# =============================================================================


def url_decode(text: str) -> str:
    """
    URL-decode text.

    Args:
        text: URL-encoded text.

    Returns:
        Decoded text.

    Examples:
        >>> url_decode("hello%20world")
        'hello world'
        >>> url_decode("caf%C3%A9")
        'café'

    Notes:
        Uses urllib.parse.unquote.
        Decodes %XX sequences.
    """
    return unquote(text)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["url_decode"]
