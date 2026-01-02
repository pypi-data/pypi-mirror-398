# =============================================================================
# Docstring
# =============================================================================

"""
Hexadecimal Encoding
====================

Convert bytes to hexadecimal string representation.

Examples
--------
>>> from rite.conversion.formats import formats_hex_encode
>>> formats_hex_encode(b"hello")
'68656c6c6f'
>>> formats_hex_encode("hello")
'68656c6c6f'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def formats_hex_encode(data: bytes | str, encoding: str = "utf-8") -> str:
    """
    Encode bytes to hexadecimal string.

    Args:
        data: Data to encode (bytes or string).
        encoding: String encoding if data is string.

    Returns:
        Hexadecimal string (lowercase).

    Examples:
        >>> formats_hex_encode(b"hello")
        '68656c6c6f'
        >>> formats_hex_encode("hello")
        '68656c6c6f'
        >>> formats_hex_encode(b"\\x00\\xff")
        '00ff'
    """
    if isinstance(data, str):
        data = data.encode(encoding)

    return data.hex()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["formats_hex_encode"]
