# =============================================================================
# Docstring
# =============================================================================

"""
Morse Code Decoder
==================

Convert Morse code to text.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================

MORSE_DECODE_DICT = {
    ".-": "A",
    "-...": "B",
    "-.-.": "C",
    "-..": "D",
    ".": "E",
    "..-.": "F",
    "--.": "G",
    "....": "H",
    "..": "I",
    ".---": "J",
    "-.-": "K",
    ".-..": "L",
    "--": "M",
    "-.": "N",
    "---": "O",
    ".--.": "P",
    "--.-": "Q",
    ".-.": "R",
    "...": "S",
    "-": "T",
    "..-": "U",
    "...-": "V",
    ".--": "W",
    "-..-": "X",
    "-.--": "Y",
    "--..": "Z",
    "-----": "0",
    ".----": "1",
    "..---": "2",
    "...--": "3",
    "....-": "4",
    ".....": "5",
    "-....": "6",
    "--...": "7",
    "---..": "8",
    "----.": "9",
    "/": " ",
}


def morse_decode(morse_code: str, separator: str = " ") -> str:
    """
    Convert Morse code to text.

    Args:
        morse_code: Morse code string to decode
        separator: Character separating Morse code symbols

    Returns:
        Decoded text string

    Raises:
        ValueError: If invalid Morse code sequence encountered

    Example:
        >>> morse_decode(".... . .-.. .-.. ---")
        'HELLO'
    """
    text = []
    for morse_char in morse_code.split(separator):
        if morse_char in MORSE_DECODE_DICT:
            text.append(MORSE_DECODE_DICT[morse_char])
        elif morse_char:
            raise ValueError(f"Invalid Morse code sequence: {morse_char}")
    return "".join(text)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "morse_decode",
]
