# =============================================================================
# Docstring
# =============================================================================

"""
Rite - Cryptography - Cipher - Transposition Cipher Module
==========================================================

Provides functionality to encode and decode text using a columnar
transposition cipher.

The transposition cipher rearranges the characters of the plaintext
based on a fixed number of columns (key).

References
----------
- https://en.wikipedia.org/wiki/Transposition_cipher
- https://www.dcode.fr/transposition-cipher

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def encode_transposition_cipher(text: str, key: int) -> str:
    """
    Encode text using a simple columnar transposition cipher.

    Args:
        text: The plaintext to encode.
        key: The number of columns (i.e., transposition key).

    Returns:
        The encoded (scrambled) text.
    """
    if key < 1:
        raise ValueError("Key must be a positive integer.")

    # Pad text to ensure even columns
    remainder = len(text) % key
    if remainder:
        text += " " * (key - remainder)

    return "".join(text[i::key] for i in range(key))


def decode_transposition_cipher(
    encoded_text: str, key: int, strip_padding: bool = True
) -> str:
    """
    Decode text from a simple columnar transposition cipher.

    Args:
        encoded_text: The transposed text to decode.
        key: The number of columns used in encoding.
        strip_padding: Whether to strip trailing padding spaces (default: True).

    Returns:
        The decoded (original) text.
    """
    if key < 1:
        raise ValueError("Key must be a positive integer.")

    full_rows = len(encoded_text) // key
    extra_chars = len(encoded_text) % key

    col_lengths = [
        full_rows + 1 if i < extra_chars else full_rows for i in range(key)
    ]

    columns = []
    index = 0
    for length in col_lengths:
        columns.append(encoded_text[index : index + length])
        index += length

    result = []
    for row in range(max(col_lengths)):
        for col in columns:
            if row < len(col):
                result.append(col[row])

    decoded = "".join(result)
    return decoded.rstrip() if strip_padding else decoded


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "decode_transposition_cipher",
    "encode_transposition_cipher",
]
