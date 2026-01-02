# =============================================================================
# Docstring
# =============================================================================

"""
SHA-384 Hash
============

Compute SHA-384 hash.

Examples
--------
>>> from rite.crypto.hash import hash_sha384
>>> len(hash_sha384("hello"))
96

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


def hash_sha384(data: str | bytes, encoding: str = "utf-8") -> str:
    """
    Compute SHA-384 hash of data.

    Args:
        data: String or bytes to hash.
        encoding: Text encoding if data is string.

    Returns:
        Hexadecimal SHA-384 hash string (96 characters).

    Examples:
        >>> hash_sha384("hello")[:32]
        '59e1748777448c69de6b800d7a33'
        >>> len(hash_sha384("test"))
        96
    """
    if isinstance(data, str):
        data = data.encode(encoding)

    return hashlib.sha384(data).hexdigest()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["hash_sha384"]
