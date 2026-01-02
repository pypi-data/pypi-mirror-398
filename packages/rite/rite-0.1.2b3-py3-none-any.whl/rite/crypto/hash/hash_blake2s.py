# =============================================================================
# Docstring
# =============================================================================

"""
BLAKE2s Hash
============

Compute BLAKE2s hash (optimized for 8-32 bit platforms).

Examples
--------
>>> from rite.crypto.hash import hash_blake2s
>>> len(hash_blake2s("hello"))
64

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


def hash_blake2s(
    data: str | bytes,
    digest_size: int = 32,
    encoding: str = "utf-8",
) -> str:
    """
    Compute BLAKE2s hash of data.

    Args:
        data: String or bytes to hash.
        digest_size: Hash size in bytes (1-32).
        encoding: Text encoding if data is string.

    Returns:
        Hexadecimal BLAKE2s hash string.

    Examples:
        >>> len(hash_blake2s("hello"))
        64
        >>> len(hash_blake2s("hello", digest_size=16))
        32
        >>> hash_blake2s("test")[:16]
        '6b5935c36085c006'

    Notes:
        BLAKE2s is optimized for 8-32 bit platforms and
        produces smaller hashes than BLAKE2b.
    """
    if isinstance(data, str):
        data = data.encode(encoding)

    return hashlib.blake2s(data, digest_size=digest_size).hexdigest()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["hash_blake2s"]
