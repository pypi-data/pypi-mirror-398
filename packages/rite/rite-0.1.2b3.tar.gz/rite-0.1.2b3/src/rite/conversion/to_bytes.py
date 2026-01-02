# =============================================================================
# Docstring
# =============================================================================

"""
Bytes Conversion Module
=======================

Provides utilities for converting various types to bytes.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import os
from typing import Any

# Import | Local Modules
# Import | Local
from .is_protected_type import is_protected_type

# =============================================================================
# Functions
# =============================================================================


def to_bytes(
    content: Any,
    *,
    encoding: str = "utf-8",
    errors: str = "strict",
    strings_only: bool = False,
) -> bytes | bytearray | Any:
    """
    Convert content to a byte representation.

    Args:
    ----
        content: Content to convert to bytes.
        encoding: Character encoding to use.
        errors: Error handling scheme.
        strings_only: If True, leave protected types unconverted.

    Returns:
    -------
        bytes | bytearray | Any: Byte representation or original if protected.

    Example:
    -------
        >>> to_bytes("hello")
        b'hello'
        >>> to_bytes(42, strings_only=True)
        42
        >>> to_bytes(42, strings_only=False)
        b'42'

    Notes:
    -----
        Behavior:
        - bytes/bytearray: returned as-is
        - memoryview: converted to bytes
        - objects with __bytes__: bytes(obj)
        - os.PathLike: os.fspath(obj) encoded with encoding
        - str: encoded with encoding/errors
        - everything else: str(obj).encode(encoding, errors)

        If strings_only=True, protected types (None, numbers, dates, etc.)
        are returned unmodified.

    """
    # Fast paths
    if isinstance(content, (bytes, bytearray)):
        return content
    if isinstance(content, memoryview):
        return bytes(content)

    if strings_only and is_protected_type(content):
        return content

    # Respect custom binary conversion if provided
    to_b = getattr(content, "__bytes__", None)
    if callable(to_b):
        return to_b()

    # Paths: handle before str() to avoid repr-like encodings
    try:
        fspath = os.fspath(content)
        if isinstance(fspath, bytes):
            return fspath
        if isinstance(fspath, str):
            return fspath.encode(encoding, errors)
    except TypeError:
        # not PathLike; continue
        pass

    # Strings & general objects
    if isinstance(content, str):
        return content.encode(encoding, errors)

    return str(content).encode(encoding, errors)


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "to_bytes",
]
