# =============================================================================
# Docstring
# =============================================================================

"""
Random URL-Safe String Generation
==================================

Generate cryptographically secure URL-safe random strings.

Examples
--------
>>> from rite.crypto.random import random_urlsafe
>>> len(random_urlsafe(16))
24
>>> len(random_urlsafe(32))
43

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import secrets

# =============================================================================
# Functions
# =============================================================================


def random_urlsafe(nbytes: int = 32) -> str:
    """
    Generate cryptographically secure URL-safe string.

    Args:
        nbytes: Number of random bytes (output length varies).

    Returns:
        Random URL-safe base64 string.

    Examples:
        >>> token = random_urlsafe()
        >>> len(token) > 40
        True
        >>> token = random_urlsafe(16)
        >>> '-' not in token or '_' not in token
        True

    Notes:
        Output uses base64url encoding (A-Z, a-z, 0-9, -, _).
        Length is approximately 4/3 of nbytes.
    """
    return secrets.token_urlsafe(nbytes)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["random_urlsafe"]
