# =============================================================================
# Docstring
# =============================================================================

"""
SHA-256 Hash
============

Compute SHA-256 hash and HMAC.

Examples
--------
>>> from rite.crypto.hash import hash_sha256
>>> len(hash_sha256("hello"))
64
>>> hash_sha256_hmac("key", "message")[:16]
'6e40a5e7a8b7'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import hashlib
import hmac

# =============================================================================
# Functions
# =============================================================================


def hash_sha256(data: str | bytes, encoding: str = "utf-8") -> str:
    """
    Compute SHA-256 hash of data.

    Args:
        data: String or bytes to hash.
        encoding: Text encoding if data is string.

    Returns:
        Hexadecimal SHA-256 hash string (64 characters).

    Examples:
        >>> len(hash_sha256("hello"))
        64
        >>> hash_sha256(b"hello")[:16]
        '2cf24dba5fb0a30e'
    """
    if isinstance(data, str):
        data = data.encode(encoding)

    return hashlib.sha256(data).hexdigest()


def hash_sha256_hmac(
    key: str | bytes,
    msg: str | bytes,
    encoding: str = "utf-8",
) -> str:
    """
    Compute SHA-256 HMAC of message with key.

    Args:
        key: Secret key for HMAC.
        msg: Message to authenticate.
        encoding: Text encoding if inputs are strings.

    Returns:
        Hexadecimal HMAC-SHA-256 string.

    Examples:
        >>> hmac_result = hash_sha256_hmac("secret", "message")
        >>> len(hmac_result)
        64
    """
    if isinstance(key, str):
        key = key.encode(encoding)
    if isinstance(msg, str):
        msg = msg.encode(encoding)

    return hmac.new(key=key, msg=msg, digestmod=hashlib.sha256).hexdigest()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "hash_sha256",
    "hash_sha256_hmac",
]
