# =============================================================================
# Docstring
# =============================================================================

"""
URL Sanitizer
=============

Sanitize and validate URLs.

Examples
--------
>>> from rite.markup.sanitize import sanitize_url
>>> sanitize_url("javascript:alert('xss')")
''

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from urllib.parse import urlparse

# =============================================================================
# Functions
# =============================================================================


def sanitize_url(url: str, allowed_schemes: list[str] | None = None) -> str:
    """
    Sanitize URL by checking scheme.

    Args:
        url: URL to sanitize.
        allowed_schemes: Allowed URL schemes (default: http, https).

    Returns:
        Sanitized URL or empty string if invalid.

    Examples:
        >>> sanitize_url("https://example.com")
        'https://example.com'
        >>> sanitize_url("javascript:void(0)")
        ''
        >>> sanitize_url("ftp://server.com", ["ftp"])
        'ftp://server.com'

    Notes:
        Blocks dangerous schemes like javascript:.
        Returns empty string for invalid URLs.
    """
    if allowed_schemes is None:
        allowed_schemes = ["http", "https"]

    # Normalize allowed schemes to lowercase for case-insensitive comparison
    allowed_schemes_lower = [s.lower() for s in allowed_schemes]

    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() in allowed_schemes_lower:
            return url
    except Exception:
        pass

    return ""


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["sanitize_url"]
