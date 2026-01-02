# =============================================================================
# Docstring
# =============================================================================

"""
URL Encoder
===========

Encode URL component.

Examples
--------
>>> from rite.net.url import url_encode
>>> url_encode("hello world")
'hello%20world'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from urllib.parse import quote

# =============================================================================
# Functions
# =============================================================================


def url_encode(text: str, safe: str = "") -> str:
    """
    URL-encode text.

    Args:
        text: Text to encode.
        safe: Characters not to encode.

    Returns:
        URL-encoded text.

    Examples:
        >>> url_encode("hello world")
        'hello%20world'
        >>> url_encode("a/b/c", safe="/")
        'a/b/c'

    Notes:
        Uses urllib.parse.quote.
        Encodes special characters to %XX format.
    """
    return quote(text, safe=safe)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["url_encode"]
