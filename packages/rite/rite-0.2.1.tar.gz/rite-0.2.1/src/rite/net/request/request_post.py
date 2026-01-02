# =============================================================================
# Docstring
# =============================================================================

"""
POST Request
============

Make HTTP POST request.

Examples
--------
>>> from rite.net.request import request_post
>>> response = request_post(
...     "https://api.example.com/data",
...     data={"key": "value"}
... )  # doctest: +SKIP

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# =============================================================================
# Functions
# =============================================================================


def request_post(
    url: str,
    data: dict[str, str] | bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> str:
    """
    Make HTTP POST request.

    Args:
        url: URL to request.
        data: Data to send (dict or bytes).
        headers: Optional request headers.
        timeout: Request timeout in seconds.

    Returns:
        Response body as string.

    Raises:
        URLError: On request failure.

    Examples:
        >>> response = request_post(
        ...     "http://httpbin.org/post",
        ...     data={"test": "data"}
        ... )  # doctest: +SKIP

    Notes:
        Dict data is URL-encoded automatically.
        Uses urllib from standard library.
    """
    if headers is None:
        headers = {}

    if isinstance(data, dict):
        data = urlencode(data).encode("utf-8")
    elif data is None:
        data = b""

    req = Request(url, data=data, headers=headers, method="POST")

    try:
        with urlopen(req, timeout=timeout) as response:
            result: str = response.read().decode("utf-8")
            return result
    except URLError as e:
        raise URLError(f"POST request failed: {e}") from e


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["request_post"]
