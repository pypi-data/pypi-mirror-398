# =============================================================================
# Docstring
# =============================================================================

"""
HTTP Methods
============

Check if HTTP method is valid.

Examples
--------
>>> from rite.net.http import http_is_method
>>> http_is_method("GET")
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Constants
# =============================================================================

VALID_HTTP_METHODS = frozenset(
    ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"]
)

# =============================================================================
# Functions
# =============================================================================


def http_is_method(method: str) -> bool:
    """
    Check if HTTP method is valid.

    Args:
        method: HTTP method to check.

    Returns:
        True if valid HTTP method.

    Examples:
        >>> http_is_method("GET")
        True
        >>> http_is_method("POST")
        True
        >>> http_is_method("INVALID")
        False

    Notes:
        Case-sensitive.
        Checks against standard HTTP methods.
    """
    return method.upper() in VALID_HTTP_METHODS


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["http_is_method", "VALID_HTTP_METHODS"]
