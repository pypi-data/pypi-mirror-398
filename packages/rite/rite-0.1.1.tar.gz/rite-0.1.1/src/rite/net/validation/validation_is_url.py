# =============================================================================
# Docstring
# =============================================================================

"""
URL Validator
=============

Validate URL format.

Examples
--------
>>> from rite.net.validation import validation_is_url
>>> validation_is_url("https://example.com")
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import re

# =============================================================================
# Functions
# =============================================================================


def validation_is_url(url: str, require_scheme: bool = True) -> bool:
    """
    Validate URL format.

    Args:
        url: URL string to validate.
        require_scheme: Require scheme (http://, https://).

    Returns:
        True if valid URL format.

    Examples:
        >>> validation_is_url("https://example.com")
        True
        >>> validation_is_url("not a url")
        False
        >>> validation_is_url("example.com", require_scheme=False)
        True

    Notes:
        Basic validation using regex.
        Checks format, not existence.
    """
    if require_scheme:
        pattern = re.compile(
            r"^https?://"  # Scheme
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"
            r"(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # Domain
            r"localhost|"  # localhost
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
            r"(?::\d+)?"  # Port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
    else:
        pattern = re.compile(
            r"^(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"
            r"(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

    return bool(pattern.match(url))


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["validation_is_url"]
