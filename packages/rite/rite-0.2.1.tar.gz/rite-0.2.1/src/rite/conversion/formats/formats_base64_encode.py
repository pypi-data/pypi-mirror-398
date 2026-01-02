# =============================================================================
# Docstring
# =============================================================================

"""
Base64 Encoding
===============

Convert bytes to base64 string representation.

Examples
--------
>>> from rite.conversion.formats import formats_base64_encode
>>> formats_base64_encode(b"hello")
'aGVsbG8='
>>> formats_base64_encode("hello")
'aGVsbG8='

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


def formats_base64_encode(data: bytes | str, encoding: str = "utf-8") -> str:
    """
    Encode bytes to base64 string.

    Args:
        data: Data to encode (bytes or string).
        encoding: String encoding if data is string.

    Returns:
        Base64 encoded string.

    Examples:
        >>> formats_base64_encode(b"hello")
        'aGVsbG8='
        >>> formats_base64_encode("hello")
        'aGVsbG8='
        >>> formats_base64_encode("世界")
        '5LiW55WM'
    """
    if isinstance(data, str):
        data = data.encode(encoding)

    encoded = base64.b64encode(data)
    return encoded.decode("ascii")


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["formats_base64_encode"]
