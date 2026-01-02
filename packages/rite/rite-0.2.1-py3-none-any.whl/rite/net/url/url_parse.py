# =============================================================================
# Docstring
# =============================================================================

"""
URL Parser
==========

Parse URL into components.

Examples
--------
>>> from rite.net.url import url_parse
>>> url_parse("https://example.com:8080/path?q=1#frag")  # doctest: +SKIP
{'scheme': 'https', 'netloc': 'example.com:8080', ...}

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from urllib.parse import ParseResult, urlparse

# =============================================================================
# Functions
# =============================================================================


def url_parse(url: str) -> ParseResult:
    """
    Parse URL into components.

    Args:
        url: URL string to parse.

    Returns:
        ParseResult with scheme, netloc, path, params, query, fragment.

    Examples:
        >>> result = url_parse("http://example.com/path")
        >>> result.scheme
        'http'
        >>> result.netloc
        'example.com'

    Notes:
        Uses urllib.parse.urlparse.
        Returns ParseResult named tuple.
    """
    return urlparse(url)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["url_parse"]
