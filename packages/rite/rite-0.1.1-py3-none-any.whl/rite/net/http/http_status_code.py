# =============================================================================
# Docstring
# =============================================================================

"""
HTTP Status Codes
=================

HTTP status code constants and utilities.

Examples
--------
>>> from rite.net.http import http_status_code
>>> http_status_code(200)
'OK'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from http import HTTPStatus

# =============================================================================
# Functions
# =============================================================================


def http_status_code(code: int) -> str:
    """
    Get HTTP status description.

    Args:
        code: HTTP status code.

    Returns:
        Status description.

    Examples:
        >>> http_status_code(200)
        'OK'
        >>> http_status_code(404)
        'Not Found'
        >>> http_status_code(500)
        'Internal Server Error'

    Notes:
        Uses http.HTTPStatus from standard library.
    """
    try:
        return HTTPStatus(code).phrase
    except ValueError:
        return "Unknown Status"


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["http_status_code"]
