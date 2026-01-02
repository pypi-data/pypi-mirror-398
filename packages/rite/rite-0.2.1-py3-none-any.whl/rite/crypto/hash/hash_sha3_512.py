# =============================================================================
# Docstring
# =============================================================================

"""
SHA-3-512 Hash
==============

Compute SHA-3-512 hash.

Examples
--------
>>> from rite.crypto.hash import hash_sha3_512
>>> len(hash_sha3_512("hello"))
128

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


def hash_sha3_512(data: str | bytes, encoding: str = "utf-8") -> str:
    """
    Compute SHA-3-512 hash of data.

    Args:
        data: String or bytes to hash.
        encoding: Text encoding if data is string.

    Returns:
        Hexadecimal SHA-3-512 hash string (128 characters).

    Examples:
        >>> len(hash_sha3_512("hello"))
        128
        >>> hash_sha3_512("test")[:16]
        '1e2e9fc2002b002d'
    """
    if isinstance(data, str):
        data = data.encode(encoding)

    return hashlib.sha3_512(data).hexdigest()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["hash_sha3_512"]
