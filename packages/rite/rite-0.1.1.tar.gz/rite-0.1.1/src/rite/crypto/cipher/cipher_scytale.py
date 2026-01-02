# =============================================================================
# Docstring
# =============================================================================

"""
Rite - Cryptography - Cipher - Scytale Cipher Module
====================================================

The Scytale cipher wraps text around a rod (cylinder) of fixed diameter,
writing along its length and reading across its circumference.

References
----------
- https://en.wikipedia.org/wiki/Scytale
- https://www.dcode.fr/scytale-cipher

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def encode_scytale_cipher(
    text: str,
    diameter: int,
) -> str:
    """
    Encode a string using the Scytale cipher.

    Args:
        text: The input plaintext.
        diameter: Number of columns (characters per wrap-around).

    Returns:
        Encoded ciphertext.
    """
    if diameter < 1:
        raise ValueError("Diameter must be a positive integer")

    # Pad to full block
    remainder = len(text) % diameter
    if remainder != 0:
        text += " " * (diameter - remainder)

    rows = len(text) // diameter
    encoded = []

    for col in range(diameter):
        for row in range(rows):
            idx = row * diameter + col
            encoded.append(text[idx])

    return "".join(encoded)


def decode_scytale_cipher(
    encoded_text: str,
    diameter: int,
) -> str:
    """
    Decode a Scytale-encoded string.

    Args:
        encoded_text: The ciphertext to decode.
        diameter: Number of columns used during encoding.

    Returns:
        Decoded plaintext string.
    """
    if diameter < 1:
        raise ValueError("Diameter must be a positive integer")

    rows = len(encoded_text) // diameter
    decoded = [""] * (rows * diameter)

    idx = 0
    for col in range(diameter):
        for row in range(rows):
            decoded[row * diameter + col] = encoded_text[idx]
            idx += 1

    return "".join(decoded).rstrip()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "decode_scytale_cipher",
    "encode_scytale_cipher",
]
