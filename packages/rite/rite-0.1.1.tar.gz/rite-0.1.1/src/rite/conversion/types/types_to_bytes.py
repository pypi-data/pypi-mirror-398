# =============================================================================
# Docstring
# =============================================================================

"""
Bytes Conversion Module
=======================

Convert various types to bytes representation.

Examples
--------
>>> from rite.conversion.types import types_to_bytes
>>> types_to_bytes("hello")
b'hello'
>>> types_to_bytes(42)
b'42'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import os
from typing import Any

# =============================================================================
# Constants
# =============================================================================

PROTECTED_TYPES = (
    type(None),
    int,
    float,
    bool,
)

# =============================================================================
# Functions
# =============================================================================


def types_to_bytes(
    content: Any,
    *,
    encoding: str = "utf-8",
    errors: str = "strict",
    strings_only: bool = False,
) -> bytes | bytearray | Any:
    """
    Convert content to a byte representation.

    Args:
        content: Content to convert to bytes.
        encoding: Character encoding to use.
        errors: Error handling scheme.
        strings_only: If True, leave protected types unconverted.

    Returns:
        Byte representation or original if protected.

    Examples:
        >>> types_to_bytes("hello")
        b'hello'
        >>> types_to_bytes(42, strings_only=True)
        42
        >>> types_to_bytes(42, strings_only=False)
        b'42'
        >>> types_to_bytes(b"bytes")
        b'bytes'

    Notes:
        Behavior:
        - bytes/bytearray: returned as-is
        - memoryview: converted to bytes
        - objects with __bytes__: bytes(obj)
        - os.PathLike: os.fspath(obj) encoded
        - str: encoded with encoding/errors
        - everything else: str(obj).encode()

        If strings_only=True, protected types (None, numbers)
        are returned unmodified.
    """
    # Fast paths
    if isinstance(content, (bytes, bytearray)):
        return content

    # Protected types
    if strings_only and isinstance(content, PROTECTED_TYPES):
        return content

    # Memory view
    if isinstance(content, memoryview):
        return bytes(content)

    # Objects with __bytes__
    if hasattr(content, "__bytes__"):
        return bytes(content)

    # Path-like objects
    if isinstance(content, os.PathLike):
        path_str = os.fspath(content)
        return path_str.encode(encoding, errors)

    # Strings
    if isinstance(content, str):
        return content.encode(encoding, errors)

    # Everything else
    return str(content).encode(encoding, errors)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["types_to_bytes", "PROTECTED_TYPES"]
