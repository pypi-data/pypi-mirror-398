# =============================================================================
# Docstring
# =============================================================================

"""
Rite - Cryptography - Cipher - Rot13 Cipher Module
==================================================

Provides functionality to encode and decode text using the Rot13 cipher.

The Rot13 cipher shifts each letter 13 places in the alphabet and is symmetric
(i.e., encoding and decoding are the same operation).

References
----------
- https://en.wikipedia.org/wiki/ROT13
- https://www.dcode.fr/rot-13-cipher

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Internal Constants
# =============================================================================

# Translation table for ROT13 (built once)
_ROT13_TRANS = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
)


# =============================================================================
# Functions
# =============================================================================


def encode_rot13_cipher(text: str) -> str:
    """
    Encode or decode text using the Rot13 cipher.

    Since Rot13 is symmetric, this function is used for both encoding and decoding.

    Args:
        text: The input text to encode or decode.

    Returns:
        The transformed text.
    """
    return text.translate(_ROT13_TRANS)


def decode_rot13_cipher(text: str) -> str:
    """
    Decode text using the Rot13 cipher.

    This is functionally identical to encoding, as Rot13 is symmetric.

    Args:
        text: The Rot13-encoded text.

    Returns:
        The decoded text.
    """
    return encode_rot13_cipher(text)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "decode_rot13_cipher",
    "encode_rot13_cipher",
]
