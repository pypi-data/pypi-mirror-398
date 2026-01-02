# =============================================================================
# Docstring
# =============================================================================

"""
BLAKE2b Hash
============

Compute BLAKE2b hash (fast, secure alternative to SHA).

Examples
--------
>>> from rite.crypto.hash import hash_blake2b
>>> len(hash_blake2b("hello"))
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


def hash_blake2b(
    data: str | bytes,
    digest_size: int = 64,
    encoding: str = "utf-8",
) -> str:
    """
    Compute BLAKE2b hash of data.

    Args:
        data: String or bytes to hash.
        digest_size: Hash size in bytes (1-64).
        encoding: Text encoding if data is string.

    Returns:
        Hexadecimal BLAKE2b hash string.

    Examples:
        >>> len(hash_blake2b("hello"))
        128
        >>> len(hash_blake2b("hello", digest_size=32))
        64
        >>> hash_blake2b("test")[:16]
        '928b20366943e2ae'

    Notes:
        BLAKE2b is faster than MD5, SHA-1, SHA-2, and SHA-3
        while being at least as secure as SHA-3.
    """
    if isinstance(data, str):
        data = data.encode(encoding)

    return hashlib.blake2b(data, digest_size=digest_size).hexdigest()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["hash_blake2b"]
