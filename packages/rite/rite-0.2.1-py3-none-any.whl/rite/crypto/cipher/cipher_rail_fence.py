# =============================================================================
# Docstring
# =============================================================================

"""
Rite - Cryptography - Cipher - Rail Fence Cipher Module
=======================================================

Provides functionality to encode and decode text using the Rail Fence cipher.

The Rail Fence cipher is a transposition cipher that rearranges characters
in a zigzag pattern across a fixed number of rails (rows).

References
----------
- https://en.wikipedia.org/wiki/Rail_fence_cipher
- https://www.dcode.fr/rail-fence-cipher

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def encode_rail_fence_cipher(text: str, num_rails: int) -> str:
    """
    Encode text using the Rail Fence cipher.

    Args:
        text: The plaintext to encode.
        num_rails: Number of rails (rows) to use in the zigzag pattern.

    Returns:
        Encoded ciphertext string.
    """
    if num_rails < 2 or num_rails >= len(text):
        return text  # Nothing to encode

    # Create empty rails
    fence: list[list[str]] = [[] for _ in range(num_rails)]
    rail = 0
    direction = 1

    for char in text:
        fence[rail].append(char)
        rail += direction

        if rail == 0 or rail == num_rails - 1:
            direction *= -1  # Zigzag

    # Flatten the rails
    return "".join("".join(row) for row in fence)


# =============================================================================


def decode_rail_fence_cipher(encoded_text: str, num_rails: int) -> str:
    """
    Decode a Rail Fence-encoded string.

    Args:
        encoded_text: The encoded string to decode.
        num_rails: Number of rails used during encoding.

    Returns:
        The original decoded plaintext string.
    """
    if num_rails < 2 or num_rails >= len(encoded_text):
        return encoded_text

    # Step 1: determine number of characters per rail
    rail_lengths = [0] * num_rails
    rail = 0
    direction = 1

    for _ in encoded_text:
        rail_lengths[rail] += 1
        rail += direction
        if rail == 0 or rail == num_rails - 1:
            direction *= -1

    # Step 2: fill rails with corresponding characters
    fence: list[list[str]] = []
    index = 0
    for length in rail_lengths:
        fence.append(list(encoded_text[index : index + length]))
        index += length

    # Step 3: reconstruct the original text
    result = []
    rail = 0
    direction = 1
    for _ in range(len(encoded_text)):
        result.append(fence[rail].pop(0))
        rail += direction
        if rail == 0 or rail == num_rails - 1:
            direction *= -1

    return "".join(result)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "decode_rail_fence_cipher",
    "encode_rail_fence_cipher",
]
