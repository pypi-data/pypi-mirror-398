# =============================================================================
# Docstring
# =============================================================================

"""
MD5 Hash
========

Compute MD5 hash (for non-cryptographic purposes).

Examples
--------
>>> from rite.crypto.hash import hash_md5
>>> hash_md5("hello")
'5d41402abc4b2a76b9719d911017c592'

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


def hash_md5(data: str | bytes, encoding: str = "utf-8") -> str:
    """
    Compute MD5 hash of data.

    Args:
        data: String or bytes to hash.
        encoding: Text encoding if data is string.

    Returns:
        Hexadecimal MD5 hash string.

    Examples:
        >>> hash_md5("hello")
        '5d41402abc4b2a76b9719d911017c592'
        >>> hash_md5(b"hello")
        '5d41402abc4b2a76b9719d911017c592'

    Warning:
        MD5 is cryptographically broken. Use only for checksums,
        not for security purposes.
    """
    if isinstance(data, str):
        data = data.encode(encoding)

    return hashlib.md5(data).hexdigest()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["hash_md5"]
