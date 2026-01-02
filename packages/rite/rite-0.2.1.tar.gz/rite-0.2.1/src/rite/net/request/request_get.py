# =============================================================================
# Docstring
# =============================================================================

"""
GET Request
===========

Make HTTP GET request.

Examples
--------
>>> from rite.net.request import request_get
>>> response = request_get("https://api.example.com/data")  # doctest: +SKIP

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from urllib.error import URLError
from urllib.request import Request, urlopen

# =============================================================================
# Functions
# =============================================================================


def request_get(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> str:
    """
    Make HTTP GET request.

    Args:
        url: URL to request.
        headers: Optional request headers.
        timeout: Request timeout in seconds.

    Returns:
        Response body as string.

    Raises:
        URLError: On request failure.

    Examples:
        >>> data = request_get("http://example.com")  # doctest: +SKIP
        >>> isinstance(data, str)  # doctest: +SKIP
        True

    Notes:
        Uses urllib from standard library.
        For advanced features, use external library like requests.
    """
    if headers is None:
        headers = {}

    req = Request(url, headers=headers)

    try:
        with urlopen(req, timeout=timeout) as response:
            result: str = response.read().decode("utf-8")
            return result
    except URLError as e:
        raise URLError(f"GET request failed: {e}") from e


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["request_get"]
