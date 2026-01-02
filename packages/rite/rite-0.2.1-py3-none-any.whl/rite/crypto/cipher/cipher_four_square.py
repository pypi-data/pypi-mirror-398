# =============================================================================
# Docstring
# =============================================================================

"""
Rite - Cryptography - Cipher - Four-Square Cipher Module
========================================================

Provides functionality to encode and decode text using the Four-Square cipher.

This classical cipher uses four 5x5 matrices to encode letter pairs.

References
----------
- https://en.wikipedia.org/wiki/Four-square_cipher
- https://www.dcode.fr/four-square-cipher

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def generate_square(key: str) -> list[list[str]]:
    """
    Generate a 5x5 matrix for the Four-Square cipher using a key.

    Args:
        key: Keyword to populate the matrix.

    Returns:
        A 5x5 list of characters (J is merged with I).
    """
    key = key.upper().replace("J", "I")
    alphabet = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
    seen = set()
    ordered_chars = []

    for char in key + alphabet:
        if char not in seen and char in alphabet:
            seen.add(char)
            ordered_chars.append(char)

    return [ordered_chars[i : i + 5] for i in range(0, 25, 5)]


def find_position(
    letter: str,
    square: list[list[str]],
) -> tuple[int, int]:
    """
    Find the (row, col) position of a letter in a 5x5 matrix.

    Args:
        letter: The letter to locate.
        square: A 5x5 matrix.

    Returns:
        (row_index, col_index) of the letter.
    """
    for row_idx, row in enumerate(square):
        if letter in row:
            return row_idx, row.index(letter)
    raise ValueError(f"Letter '{letter}' not found in square.")


def four_square_cipher_pair(
    pair: str,
    square_tl: list[list[str]],
    square_tr: list[list[str]],
    square_bl: list[list[str]],
    square_br: list[list[str]],
    mode: str = "encode",
) -> str:
    """
    Encode or decode a letter pair using the Four-Square cipher.

    Args:
        pair: A two-character string.
        square_tl: Top-left square (standard).
        square_tr: Top-right square (key 1).
        square_bl: Bottom-left square (key 2).
        square_br: Bottom-right square (standard).
        mode: 'encode' or 'decode'.

    Returns:
        Encoded or decoded letter pair.
    """
    if len(pair) != 2:
        raise ValueError("Pair must be exactly two alphabetic characters.")

    a, b = pair

    if mode == "encode":
        r1, c1 = find_position(a, square_tl)
        r2, c2 = find_position(b, square_br)
        return square_tr[r1][c2] + square_bl[r2][c1]
    elif mode == "decode":
        r1, c2 = find_position(a, square_tr)
        r2, c1 = find_position(b, square_bl)
        return square_tl[r1][c1] + square_br[r2][c2]
    else:
        raise ValueError("Mode must be 'encode' or 'decode'.")


def encode_four_square_cipher(
    text: str,
    key1: str,
    key2: str,
) -> str:
    """
    Encode text using the Four-Square cipher.

    Args:
        text: The plaintext to encode.
        key1: Key for the top-right square.
        key2: Key for the bottom-left square.

    Returns:
        The encoded ciphertext.
    """
    text = text.upper().replace("J", "I")
    text = "".join(filter(str.isalpha, text))
    if len(text) % 2 != 0:
        text += "X"  # Pad odd length with X

    square_tl = generate_square("")  # Standard square
    square_tr = generate_square(key1)
    square_bl = generate_square(key2)
    square_br = generate_square("")  # Standard square

    result = []
    for i in range(0, len(text), 2):
        pair = text[i : i + 2]
        result.append(
            four_square_cipher_pair(
                pair,
                square_tl,
                square_tr,
                square_bl,
                square_br,
                mode="encode",
            )
        )

    return "".join(result)


def decode_four_square_cipher(
    encoded_text: str,
    key1: str,
    key2: str,
) -> str:
    """
    Decode ciphertext encoded with the Four-Square cipher.

    Args:
        encoded_text: The encrypted message to decode.
        key1: Key used for the top-right square.
        key2: Key used for the bottom-left square.

    Returns:
        The decoded plaintext.
    """
    encoded_text = encoded_text.upper().replace("J", "I")
    encoded_text = "".join(filter(str.isalpha, encoded_text))

    square_tl = generate_square("")  # Standard square
    square_tr = generate_square(key1)
    square_bl = generate_square(key2)
    square_br = generate_square("")  # Standard square

    result = []
    for i in range(0, len(encoded_text), 2):
        pair = encoded_text[i : i + 2]
        result.append(
            four_square_cipher_pair(
                pair,
                square_tl,
                square_tr,
                square_bl,
                square_br,
                mode="decode",
            )
        )

    return "".join(result)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "four_square_cipher_pair",
    "encode_four_square_cipher",
    "decode_four_square_cipher",
]
