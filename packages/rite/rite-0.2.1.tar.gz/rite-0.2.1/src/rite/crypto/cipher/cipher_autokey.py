# =============================================================================
# Docstring
# =============================================================================

"""
Rite - Cryptography - Cipher - Autokey Cipher Module
====================================================

Provides functionality to encode and decode text using the Autokey cipher.

The Autokey cipher is a polyalphabetic substitution cipher that extends the key
with the plaintext itself during encoding, and with the decoded text during
decoding.

References
----------
- https://en.wikipedia.org/wiki/Autokey_cipher
- https://www.dcode.fr/autokey-cipher

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def _shift_char(c: str, k: str, decode: bool = False) -> str:
    """
    Shift character `c` by character `k` using Caesar logic.
    Preserves case of `c`.

    Args:
        c: Character to shift.
        k: Key character to use for shift.
        decode: Whether to decode (subtract shift) instead of encode (add shift).

    Returns:
        Shifted character.
    """
    base = ord("A") if c.isupper() else ord("a")
    offset_c = ord(c) - base
    offset_k = ord(k.lower()) - ord("a")
    if decode:
        shifted = (offset_c - offset_k) % 26
    else:
        shifted = (offset_c + offset_k) % 26
    return chr(base + shifted)


# =============================================================================


def encode_autokey_cipher(
    text: str,
    key: str,
) -> str:
    """
    Encode text using the Autokey cipher.

    Args:
        text: The plaintext to encode.
        key: The cipher key (only letters are used).

    Returns:
        Encoded ciphertext.
    """
    key_stream = (key + text).replace(" ", "")
    result = []
    key_index = 0

    for char in text:
        if char.isalpha():
            result.append(_shift_char(char, key_stream[key_index]))
            key_index += 1
        else:
            result.append(char)

    return "".join(result)


# =============================================================================


def decode_autokey_cipher(
    encoded_text: str,
    key: str,
) -> str:
    """
    Decode text using the Autokey cipher.

    Args:
        encoded_text: The ciphertext to decode.
        key: The original cipher key.

    Returns:
        Decoded plaintext.
    """
    key_stream = key
    result = []

    for char in encoded_text:
        if char.isalpha():
            decoded_char = _shift_char(
                char, key_stream[len(result)], decode=True
            )
            result.append(decoded_char)
            key_stream += decoded_char  # extend key with decoded text
        else:
            result.append(char)

    return "".join(result)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "decode_autokey_cipher",
    "encode_autokey_cipher",
]
