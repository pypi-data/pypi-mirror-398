# =============================================================================
# Docstring
# =============================================================================

"""
Rite - Cryptography - Cipher - Atbash Cipher Module
===================================================

Provides functionality to encode and decode text using the Atbash cipher.

The Atbash cipher is a classical substitution cipher that reverses the
alphabet (A ↔ Z, B ↔ Y, ..., a ↔ z).

References
----------
- https://en.wikipedia.org/wiki/Atbash
- https://www.dcode.fr/atbash-cipher

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Constants
# =============================================================================

_ATBASH_TRANS = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    "ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjihgfedcba",
)


# =============================================================================
# Functions
# =============================================================================


def encode_atbash_cipher(
    text: str,
) -> str:
    """
    Encode (or decode) text using the Atbash cipher.

    Since Atbash is symmetric, the same function can be used for encoding and decoding.

    Args:
        text: Input string to encode or decode.

    Returns:
        The Atbash-encoded/decoded string.
    """
    return text.translate(_ATBASH_TRANS)


def decode_atbash_cipher(
    text: str,
) -> str:
    """
    Decode text using the Atbash cipher.

    This is functionally identical to encoding, since Atbash is symmetric.

    Args:
        text: The Atbash-encoded string.

    Returns:
        The decoded string (same as encoding).
    """
    return encode_atbash_cipher(text)


# =============================================================================
# Aliases
# =============================================================================

encode = encode_atbash_cipher
decode = decode_atbash_cipher

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "encode_atbash_cipher",
    "decode_atbash_cipher",
    "encode",
    "decode",
]
