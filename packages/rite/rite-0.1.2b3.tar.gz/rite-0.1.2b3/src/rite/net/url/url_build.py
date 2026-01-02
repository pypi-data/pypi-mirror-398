# =============================================================================
# Docstring
# =============================================================================

"""
URL Builder
===========

Build URL from components.

Examples
--------
>>> from rite.net.url import url_build
>>> url_build("https", "example.com", "/path", query="q=1")
'https://example.com/path?q=1'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from urllib.parse import urlencode, urlunparse

# =============================================================================
# Functions
# =============================================================================


def url_build(
    scheme: str = "",
    netloc: str = "",
    path: str = "",
    params: str = "",
    query: str | dict[str, str] = "",
    fragment: str = "",
) -> str:
    """
    Build URL from components.

    Args:
        scheme: URL scheme (http, https, etc.).
        netloc: Network location (domain:port).
        path: Path component.
        params: Parameters (rarely used).
        query: Query string or dict.
        fragment: Fragment identifier.

    Returns:
        Complete URL string.

    Examples:
        >>> url_build("https", "example.com", "/api")
        'https://example.com/api'
        >>> url_build("http", "test.com", query={"a": "1", "b": "2"})
        'http://test.com?a=1&b=2'

    Notes:
        Uses urllib.parse.urlunparse.
        Query can be string or dict.
    """
    if isinstance(query, dict):
        query = urlencode(query)

    return urlunparse((scheme, netloc, path, params, query, fragment))


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["url_build"]
