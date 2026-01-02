# =============================================================================
# Docstring
# =============================================================================

"""
SHA-1 Hash
==========

Compute SHA-1 hash (for non-cryptographic purposes).

Examples
--------
>>> from rite.crypto.hash import hash_sha1
>>> hash_sha1("hello")
'aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import hashlib

# =============================================================================
# Functions
# =============================================================================


def hash_sha1(data: str | bytes, encoding: str = "utf-8") -> str:
    """
    Compute SHA-1 hash of data.

    Args:
        data: String or bytes to hash.
        encoding: Text encoding if data is string.

    Returns:
        Hexadecimal SHA-1 hash string.

    Examples:
        >>> hash_sha1("hello")
        'aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d'
        >>> hash_sha1(b"hello")
        'aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d'

    Warning:
        SHA-1 is deprecated for cryptographic use. Use SHA-256
        or SHA-512 for security purposes.
    """
    if isinstance(data, str):
        data = data.encode(encoding)

    return hashlib.sha1(data).hexdigest()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["hash_sha1"]
