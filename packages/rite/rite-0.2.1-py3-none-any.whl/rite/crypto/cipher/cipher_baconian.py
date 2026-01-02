# =============================================================================
# Docstring
# =============================================================================

"""
Rite - Cryptography - Cipher - Baconian Cipher Module
=====================================================

Provides functionality to encode and decode text using the Baconian cipher.

The Baconian cipher encodes each letter of the alphabet using a unique
5-letter combination of 'a' and 'b'. It is a classical steganographic cipher.

References
----------
- https://en.wikipedia.org/wiki/Bacon%27s_cipher
- https://www.dcode.fr/bacon-cipher

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Constants
# =============================================================================

_BACON_DICT = {
    "a": "aaaaa",
    "b": "aaaab",
    "c": "aaaba",
    "d": "aaabb",
    "e": "aabaa",
    "f": "aabab",
    "g": "aabba",
    "h": "aabbb",
    "i": "abaaa",
    "j": "abaab",
    "k": "ababa",
    "l": "ababb",
    "m": "abbaa",
    "n": "abbab",
    "o": "abbba",
    "p": "abbbb",
    "q": "baaaa",
    "r": "baaab",
    "s": "baaba",
    "t": "baabb",
    "u": "babaa",
    "v": "babab",
    "w": "babba",
    "x": "babbb",
    "y": "bbaaa",
    "z": "bbaab",
}

# Inverted for decoding
_REVERSE_BACON_DICT = {v: k for k, v in _BACON_DICT.items()}

# =============================================================================
# Functions
# =============================================================================


def encode_baconian_cipher(
    text: str,
) -> str:
    """
    Encode plaintext using the Baconian cipher.

    Non-alphabetic characters are ignored. All letters are converted
    to lowercase.

    Args:
        text: Input text to encode.

    Returns:
        A string of 'a' and 'b' representing the encoded text.
    """
    return "".join(
        _BACON_DICT[char.lower()] for char in text if char.isalpha()
    )


# =============================================================================


def decode_baconian_cipher(encoded_text: str) -> str:
    """
    Decode Baconian-encoded text (a/b) back into plaintext.

    Ignores incomplete final segments and assumes input is clean (only 'a' and 'b').

    Args:
        encoded_text: A string of 'a' and 'b' characters, in chunks of 5.

    Returns:
        Decoded plaintext.
    """
    return "".join(
        _REVERSE_BACON_DICT.get(encoded_text[i : i + 5], "?")
        for i in range(0, len(encoded_text), 5)
        if len(encoded_text[i : i + 5]) == 5
    )


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "decode_baconian_cipher",
    "encode_baconian_cipher",
]
