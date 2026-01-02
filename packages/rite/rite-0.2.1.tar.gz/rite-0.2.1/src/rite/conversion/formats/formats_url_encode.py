# =============================================================================
# Docstring
# =============================================================================

"""
URL Encoding
============

Convert strings to URL-safe format.

Examples
--------
>>> from rite.conversion.formats import formats_url_encode
>>> formats_url_encode("hello world")
'hello+world'
>>> formats_url_encode("key=value&foo=bar")
'key%3Dvalue%26foo%3Dbar'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from urllib.parse import quote_plus

# =============================================================================
# Functions
# =============================================================================


def formats_url_encode(s: str, safe: str = "", encoding: str = "utf-8") -> str:
    """
    Encode string for use in URLs.

    Args:
        s: String to encode.
        safe: Characters that should not be encoded.
        encoding: Character encoding to use.

    Returns:
        URL-encoded string.

    Examples:
        >>> formats_url_encode("hello world")
        'hello+world'
        >>> formats_url_encode("key=value")
        'key%3Dvalue'
        >>> formats_url_encode("a/b/c", safe="/")
        'a/b/c'
    """
    return quote_plus(s, safe=safe, encoding=encoding)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["formats_url_encode"]
