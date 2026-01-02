# =============================================================================
# Docstring
# =============================================================================

"""
Base64 Decoding
===============

Convert base64 strings to bytes.

Examples
--------
>>> from rite.conversion.formats import formats_base64_decode
>>> formats_base64_decode('aGVsbG8=')
b'hello'
>>> formats_base64_decode('invalid')

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import base64

# =============================================================================
# Functions
# =============================================================================


def formats_base64_decode(
    s: str, default: bytes | None = None
) -> bytes | None:
    """
    Decode base64 string to bytes.

    Args:
        s: Base64 encoded string.
        default: Value to return if decoding fails.

    Returns:
        Decoded bytes or default if decoding fails.

    Examples:
        >>> formats_base64_decode('aGVsbG8=')
        b'hello'
        >>> formats_base64_decode('invalid')

        >>> formats_base64_decode('invalid', b'')
        b''
        >>> formats_base64_decode('5LiW55WM')
        b'\\xe4\\xb8\\x96\\xe7\\x95\\x8c'
    """
    try:
        return base64.b64decode(s)
    except Exception:  # noqa: BLE001
        return default


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["formats_base64_decode"]
