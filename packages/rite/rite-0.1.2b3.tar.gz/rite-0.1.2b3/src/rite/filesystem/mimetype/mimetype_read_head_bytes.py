# =============================================================================
# Docstring
# =============================================================================

"""
MIME Type Utility Module
==========================================

Module docstring placeholder added for standardized formatting.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import io
import os

# =============================================================================
# Types
# =============================================================================

BytesLike = bytes | bytearray | memoryview

# =============================================================================
# Functions
# =============================================================================


def read_head_bytes(obj: object, n: int = 8192) -> bytes | None:
    """
    Return up to the first `n` bytes from `obj` without consuming it,
    or None if that can't be done safely.

    Supports:
      - bytes / bytearray / memoryview
      - str / os.PathLike (opened in 'rb' and closed)
      - File-like objects with .peek(n)
      - File-like objects with .read(n) and seek/tell (position restored)

    If the object is a non-seekable stream without .peek(), returns None to
    avoid side effects (reading would consume data).
    """
    # Fast path: bytes-like
    if isinstance(obj, (bytes, bytearray, memoryview)):
        return bytes(obj[:n])

    # Path-like
    if isinstance(obj, (str, os.PathLike)):
        try:
            with open(obj, "rb") as f:
                return f.read(n)
        except (OSError, IOError, ValueError):
            return None

    # File-like with .peek()
    peek = getattr(obj, "peek", None)
    if callable(peek):
        try:
            data = peek(n)
            # Some peeks may return memoryview-like
            if isinstance(data, (bytes, bytearray, memoryview)):
                return bytes(data[:n])
        except (OSError, IOError, ValueError, AttributeError):
            pass  # fall through to safer read/seek

    # Generic file-like: try non-destructive read using seek/tell
    read = getattr(obj, "read", None)
    if callable(read):
        tell = getattr(obj, "tell", None)
        seek = getattr(obj, "seek", None)

        # If we can save/restore position, do it
        if callable(tell) and callable(seek):
            try:
                pos = tell()
                data = read(n)
                seek(pos, io.SEEK_SET)
                if isinstance(data, (bytes, bytearray)):
                    return bytes(data)
            except (OSError, IOError, ValueError):
                return None

        # Non-seekable and no peek -> don't consume it
        return None

    return None


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "read_head_bytes",
]
