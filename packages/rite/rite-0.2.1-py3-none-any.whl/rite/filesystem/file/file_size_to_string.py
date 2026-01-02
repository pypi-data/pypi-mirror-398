# =============================================================================
# Docstring
# =============================================================================

"""
File Size to String Converter Module
====================================

Provides functionality to convert file sizes to human-readable strings.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from typing import Any, BinaryIO, Protocol

# Implement local bytes-to-string conversion to avoid external dependency.

SIZE_UNITS: tuple[str, ...] = (
    "B",
    "KB",
    "MB",
    "GB",
    "TB",
    "PB",
)


def _convert_bytes_to_string(byte_count: int) -> str:
    if byte_count < 0:
        return "0 B"
    unit_index = 0
    size_in_units = float(byte_count)
    while size_in_units >= 1024 and unit_index < len(SIZE_UNITS) - 1:
        size_in_units /= 1024
        unit_index += 1
    if unit_index == 0:
        return f"{int(size_in_units)} {SIZE_UNITS[unit_index]}"
    return f"{size_in_units:.2f} {SIZE_UNITS[unit_index]}"


# =============================================================================
# Classes
# =============================================================================


class _SizedStream(Protocol):
    """Protocol for file-like objects with a size attribute."""

    size: int

    def tell(self, *args: Any, **kwargs: Any) -> int:
        """Return the current position in the file."""
        return 0

    def seek(self, *args: Any, **kwargs: Any) -> int:
        """Seek to a position in the file."""
        return 0


# =============================================================================
# Functions
# =============================================================================


def file_size_to_string(
    filehandle: BinaryIO | _SizedStream,
) -> str:
    """Return the size of a file in a human-readable string.

    Attempts to use filehandle.size if available (e.g. Django's UploadedFile),
    otherwise seeks to the end to determine size.

    Args:
    ----
        filehandle: A file-like object.

    Returns:
    -------
        str: A string representing the file size, e.g., '2.4 MB', '1 KB'.

    """
    if hasattr(filehandle, "size"):
        try:
            return _convert_bytes_to_string(int(filehandle.size))  # type: ignore[attr-defined]
        except (AttributeError, TypeError, ValueError):  # pragma: no cover
            pass

    try:
        current_position = filehandle.tell()
        filehandle.seek(0, 2)  # Move to end
        size = filehandle.tell()
        filehandle.seek(current_position)  # Reset to original position
        return _convert_bytes_to_string(int(size))
    except (AttributeError, OSError, TypeError, ValueError):
        return "Unknown size"


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "file_size_to_string",
]
