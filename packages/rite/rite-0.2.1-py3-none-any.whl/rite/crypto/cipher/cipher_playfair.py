# =============================================================================
# Docstring
# =============================================================================

"""
Rite - Cryptography - Cipher - Playfair Cipher Module
=====================================================

Provides functionality to encode and decode text using the Playfair cipher.

This classical digraph cipher uses a 5x5 matrix to substitute pairs of letters.

References
----------
- https://en.wikipedia.org/wiki/Playfair_cipher
- https://www.dcode.fr/playfair-cipher

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def create_playfair_square(key: str) -> list[list[str]]:
    """
    Create a 5x5 Playfair square using the given key.

    J is omitted (merged with I), and duplicates are removed in order.

    Args:
        key: The keyword to use for square generation.

    Returns:
        A 5x5 list of characters.
    """
    alphabet = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
    seen = set()
    ordered_chars = []

    for char in key.upper().replace("J", "I") + alphabet:
        if char not in seen and char in alphabet:
            seen.add(char)
            ordered_chars.append(char)

    return [ordered_chars[i : i + 5] for i in range(0, 25, 5)]


def find_position(
    letter: str,
    square: list[list[str]],
) -> tuple[int, int]:
    """
    Find (row, col) of a letter in the Playfair square.

    Args:
        letter: The letter to locate.
        square: The 5x5 matrix.

    Returns:
        Tuple of (row_index, col_index)
    """
    for row_idx, row in enumerate(square):
        if letter in row:
            return row_idx, row.index(letter)
    raise ValueError(f"Letter '{letter}' not found in square.")


# =============================================================================


def playfair_cipher_pair(
    pair: str,
    square: list[list[str]],
    mode: str = "encode",
) -> str:
    """
    Encode or decode a digraph using the Playfair cipher.

    Args:
        pair: Two-letter string.
        square: The Playfair square.
        mode: 'encode' or 'decode'.

    Returns:
        Encoded or decoded two-letter string.
    """
    a, b = pair
    r1, c1 = find_position(a, square)
    r2, c2 = find_position(b, square)

    if r1 == r2:
        shift = 1 if mode == "encode" else -1
        return square[r1][(c1 + shift) % 5] + square[r2][(c2 + shift) % 5]
    elif c1 == c2:
        shift = 1 if mode == "encode" else -1
        return square[(r1 + shift) % 5][c1] + square[(r2 + shift) % 5][c2]
    else:
        return square[r1][c2] + square[r2][c1]


def prepare_text(text: str) -> str:
    """
    Prepare text for Playfair encoding.

    Replaces J with I, removes non-alphabetic characters, inserts 'X' between
    duplicate letters, and pads the end if necessary.

    Args:
        text: Raw input text.

    Returns:
        Cleaned and paired text ready for encoding.
    """
    text = "".join(filter(str.isalpha, text.upper())).replace("J", "I")
    result = []
    i = 0
    while i < len(text):
        a = text[i]
        b = text[i + 1] if i + 1 < len(text) else "X"
        if a == b:
            result.append(a + "X")
            i += 1
        else:
            result.append(a + b)
            i += 2
    if len(result[-1]) == 1:
        result[-1] += "X"
    return "".join(result)


# =============================================================================


def encode_playfair_cipher(text: str, key: str) -> str:
    """
    Encode plaintext using the Playfair cipher.

    Args:
        text: Input plaintext.
        key: Cipher key for generating the Playfair square.

    Returns:
        Encoded ciphertext.
    """
    square = create_playfair_square(key)
    prepared = prepare_text(text)
    return "".join(
        playfair_cipher_pair(prepared[i : i + 2], square, mode="encode")
        for i in range(0, len(prepared), 2)
    )


# =============================================================================


def decode_playfair_cipher(encoded_text: str, key: str) -> str:
    """
    Decode Playfair-encoded ciphertext.

    Args:
        encoded_text: The encoded string.
        key: Cipher key used during encoding.

    Returns:
        Decoded plaintext (not automatically de-padded).
    """
    encoded_text = "".join(filter(str.isalpha, encoded_text.upper())).replace(
        "J", "I"
    )
    square = create_playfair_square(key)
    return "".join(
        playfair_cipher_pair(encoded_text[i : i + 2], square, mode="decode")
        for i in range(0, len(encoded_text), 2)
    )


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "create_playfair_square",
    "prepare_text",
    "encode_playfair_cipher",
    "decode_playfair_cipher",
]
