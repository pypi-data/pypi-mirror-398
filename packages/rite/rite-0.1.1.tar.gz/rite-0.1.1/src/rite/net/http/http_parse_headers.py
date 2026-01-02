# =============================================================================
# Docstring
# =============================================================================

"""
HTTP Headers Parser
===================

Parse HTTP headers from string.

Examples
--------
>>> from rite.net.http import http_parse_headers
>>> headers = "Content-Type: application/json\\r\\nHost: example.com"
>>> http_parse_headers(headers)
{'Content-Type': 'application/json', 'Host': 'example.com'}

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def http_parse_headers(headers_str: str) -> dict[str, str]:
    """
    Parse HTTP headers from string.

    Args:
        headers_str: Raw headers string.

    Returns:
        Dictionary of header name to value.

    Examples:
        >>> http_parse_headers("User-Agent: Mozilla/5.0")
        {'User-Agent': 'Mozilla/5.0'}
        >>> http_parse_headers(
        ...     "Accept: text/html\\r\\nAccept-Encoding: gzip"
        ... )
        {'Accept': 'text/html', 'Accept-Encoding': 'gzip'}

    Notes:
        Splits on colon (:).
        Handles \\r\\n line endings.
    """
    headers: dict[str, str] = {}

    for line in headers_str.split("\r\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue

        key, value = line.split(":", 1)
        headers[key.strip()] = value.strip()

    return headers


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["http_parse_headers"]
