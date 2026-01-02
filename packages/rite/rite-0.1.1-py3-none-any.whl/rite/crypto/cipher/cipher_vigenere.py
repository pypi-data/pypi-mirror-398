# =============================================================================
# Docstring
# =============================================================================

"""
Rite - Cryptography - Cipher - Vigenère Cipher Module
=====================================================

Provides functionality to encode and decode text using the Vigenère cipher.

The Vigenère cipher is a method of encrypting alphabetic text by using a
simple form of polyalphabetic substitution based on a keyword.

References
----------
- https://en.wikipedia.org/wiki/Vigen%C3%A8re_cipher
- https://www.dcode.fr/vigenere-cipher

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def encode_vigenere_cipher(text: str, key: str) -> str:
    """
    Encode text using the Vigenère cipher.

    Non-alphabet characters are preserved.

    Args:
        text: The plaintext to encode.
        key: The keyword used to perform letter shifts.

    Returns:
        The encoded ciphertext.
    """
    result = []
    key = key.lower()
    key_index = 0
    key_length = len(key)

    for char in text:
        if char.isalpha():
            shift = ord(key[key_index % key_length]) - ord("a")
            base = ord("A") if char.isupper() else ord("a")
            encoded_char = chr((ord(char) - base + shift) % 26 + base)
            result.append(encoded_char)
            key_index += 1
        else:
            result.append(char)

    return "".join(result)


def decode_vigenere_cipher(encoded_text: str, key: str) -> str:
    """
    Decode text from the Vigenère cipher.

    Non-alphabet characters are preserved.

    Args:
        encoded_text: The ciphertext to decode.
        key: The keyword originally used to encode.

    Returns:
        The decoded plaintext.
    """
    result = []
    key = key.lower()
    key_index = 0
    key_length = len(key)

    for char in encoded_text:
        if char.isalpha():
            shift = ord(key[key_index % key_length]) - ord("a")
            base = ord("A") if char.isupper() else ord("a")
            decoded_char = chr((ord(char) - base - shift + 26) % 26 + base)
            result.append(decoded_char)
            key_index += 1
        else:
            result.append(char)

    return "".join(result)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "decode_vigenere_cipher",
    "encode_vigenere_cipher",
]
