# =============================================================================
# Docstring
# =============================================================================

"""
SHA-3-256 Hash
==============

Compute SHA-3-256 hash.

Examples
--------
>>> from rite.crypto.hash import hash_sha3_256
>>> len(hash_sha3_256("hello"))
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


def hash_sha3_256(data: str | bytes, encoding: str = "utf-8") -> str:
    """
    Compute SHA-3-256 hash of data.

    Args:
        data: String or bytes to hash.
        encoding: Text encoding if data is string.

    Returns:
        Hexadecimal SHA-3-256 hash string (64 characters).

    Examples:
        >>> len(hash_sha3_256("hello"))
        64
        >>> hash_sha3_256("test")[:16]
        '36f028580bb02cc8'
    """
    if isinstance(data, str):
        data = data.encode(encoding)

    return hashlib.sha3_256(data).hexdigest()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["hash_sha3_256"]
