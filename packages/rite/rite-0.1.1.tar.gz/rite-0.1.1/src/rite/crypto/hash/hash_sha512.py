# =============================================================================
# Docstring
# =============================================================================

"""
SHA-512 Hash
============

Compute SHA-512 hash and HMAC.

Examples
--------
>>> from rite.crypto.hash import hash_sha512
>>> len(hash_sha512("hello"))
128
>>> hash_sha512_hmac("key", "message")[:16]
'b42af09057bac1e2'

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


def hash_sha512(data: str | bytes, encoding: str = "utf-8") -> str:
    """
    Compute SHA-512 hash of data.

    Args:
        data: String or bytes to hash.
        encoding: Text encoding if data is string.

    Returns:
        Hexadecimal SHA-512 hash string (128 characters).

    Examples:
        >>> len(hash_sha512("hello"))
        128
        >>> hash_sha512(b"hello")[:16]
        '9b71d224bd62f378'
    """
    if isinstance(data, str):
        data = data.encode(encoding)

    return hashlib.sha512(data).hexdigest()


def hash_sha512_hmac(
    key: str | bytes,
    msg: str | bytes,
    encoding: str = "utf-8",
) -> str:
    """
    Compute SHA-512 HMAC of message with key.

    Args:
        key: Secret key for HMAC.
        msg: Message to authenticate.
        encoding: Text encoding if inputs are strings.

    Returns:
        Hexadecimal HMAC-SHA-512 string.

    Examples:
        >>> hmac_result = hash_sha512_hmac("secret", "message")
        >>> len(hmac_result)
        128
    """
    if isinstance(key, str):
        key = key.encode(encoding)
    if isinstance(msg, str):
        msg = msg.encode(encoding)

    return hmac.new(key=key, msg=msg, digestmod=hashlib.sha512).hexdigest()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "hash_sha512",
    "hash_sha512_hmac",
]
