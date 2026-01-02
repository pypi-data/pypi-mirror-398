# =============================================================================
# Docstring
# =============================================================================

"""
Hexadecimal Decoding
====================

Convert hexadecimal strings to bytes.

Examples
--------
>>> from rite.conversion.formats import formats_hex_decode
>>> formats_hex_decode('68656c6c6f')
b'hello'
>>> formats_hex_decode('invalid')

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def formats_hex_decode(s: str, default: bytes | None = None) -> bytes | None:
    """
    Decode hexadecimal string to bytes.

    Args:
        s: Hexadecimal string (with or without spaces).
        default: Value to return if decoding fails.

    Returns:
        Decoded bytes or default if decoding fails.

    Examples:
        >>> formats_hex_decode('68656c6c6f')
        b'hello'
        >>> formats_hex_decode('68 65 6c 6c 6f')
        b'hello'
        >>> formats_hex_decode('invalid')

        >>> formats_hex_decode('invalid', b'')
        b''
    """
    try:
        # Remove spaces
        s = s.replace(" ", "")
        return bytes.fromhex(s)
    except (ValueError, TypeError):
        return default


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["formats_hex_decode"]
