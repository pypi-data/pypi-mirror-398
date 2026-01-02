# =============================================================================
# Docstring
# =============================================================================

"""
Rite - Cryptography - Cipher - XOR Cipher Module
================================================

Provides functionality to encode and decode text using the XOR cipher.

The XOR cipher is a symmetric key encryption technique that uses the XOR
(bitwise exclusive OR) operation between the plaintext and a repeating key.

References
----------
- https://en.wikipedia.org/wiki/XOR_cipher
- https://www.dcode.fr/xor-cipher

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def encode_xor_cipher(
    text: str,
    key: str,
) -> str:
    """
    Encode or decode text using the XOR cipher.

    Since XOR is symmetric, this function performs both encryption and decryption.

    Args:
        text: The plaintext or ciphertext string.
        key: The encryption key.

    Returns:
        A string with the result of XOR encryption/decryption.
        Note: Non-printable characters may be present in the result.
    """
    return "".join(
        chr(ord(char) ^ ord(key[i % len(key)])) for i, char in enumerate(text)
    )


def decode_xor_cipher(
    text: str,
    key: str,
) -> str:
    """
    Decode XOR-encoded text using the same key.

    This function is equivalent to encode_xor_cipher().

    Args:
        text: The XOR-encoded string.
        key: The encryption key used for encoding.

    Returns:
        The decoded plaintext string.
    """
    return encode_xor_cipher(text, key)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "decode_xor_cipher",
    "encode_xor_cipher",
]
