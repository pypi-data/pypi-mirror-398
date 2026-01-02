# =============================================================================
# Docstring
# =============================================================================

"""
URL Decoding
============

Convert URL-encoded strings back to normal format.

Examples
--------
>>> from rite.conversion.formats import formats_url_decode
>>> formats_url_decode('hello+world')
'hello world'
>>> formats_url_decode('key%3Dvalue')
'key=value'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from urllib.parse import unquote_plus

# =============================================================================
# Functions
# =============================================================================


def formats_url_decode(s: str, encoding: str = "utf-8") -> str:
    """
    Decode URL-encoded string.

    Args:
        s: URL-encoded string.
        encoding: Character encoding to use.

    Returns:
        Decoded string.

    Examples:
        >>> formats_url_decode('hello+world')
        'hello world'
        >>> formats_url_decode('key%3Dvalue')
        'key=value'
        >>> formats_url_decode('a%2Fb%2Fc')
        'a/b/c'
    """
    return unquote_plus(s, encoding=encoding)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["formats_url_decode"]
