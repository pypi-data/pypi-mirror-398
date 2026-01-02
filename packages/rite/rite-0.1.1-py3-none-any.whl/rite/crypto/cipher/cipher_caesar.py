# =============================================================================
# Docstring
# =============================================================================

"""
Rite - Cryptography - Cipher - Caesar Cipher Module
===================================================

Provides functionality to encode and decode text using the Caesar cipher.

The Caesar cipher is a substitution cipher that shifts characters by a
fixed offset.

References
----------
- https://en.wikipedia.org/wiki/Caesar_cipher
- https://www.dcode.fr/caesar-cipher

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def encode_caesar_cipher(
    text: str,
    shift: int,
) -> str:
    """
    Encode text using the Caesar cipher.

    Only alphabetic characters are shifted. Case is preserved. Other characters remain unchanged.

    Args:
        text: The plaintext string to encode.
        shift: The number of positions to shift (can be positive or negative).

    Returns:
        Encoded ciphertext string.
    """
    result = []
    for char in text:
        if char.isalpha():
            base = ord("A") if char.isupper() else ord("a")
            shifted = chr((ord(char) - base + shift) % 26 + base)
            result.append(shifted)
        else:
            result.append(char)
    return "".join(result)


# =============================================================================


def decode_caesar_cipher(
    encoded_text: str,
    shift: int,
) -> str:
    """
    Decode Caesar cipher text by reversing the shift.

    Args:
        encoded_text: The ciphertext to decode.
        shift: The original shift used during encoding.

    Returns:
        Decoded plaintext string.
    """
    return encode_caesar_cipher(encoded_text, -shift)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "decode_caesar_cipher",
    "encode_caesar_cipher",
]
