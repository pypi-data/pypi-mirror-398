# =============================================================================
# Docstring
# =============================================================================

"""
Folder Size To String
=====================

Compute the total size of a folder and return a human-readable string.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from pathlib import Path

# Import | Local Modules
from ..file.file_size_to_string import file_size_to_string
from .folder_list_files import folder_list_files

# =============================================================================
# Internal helpers
# =============================================================================


class _TotalSize:
    """Lightweight wrapper exposing a ``size`` attribute for reuse.

    The :func:`rite.filesystem.file.file_size_to_string` helper expects
    a file-like object with a ``size`` attribute when available. This
    wrapper allows us to reuse that logic for aggregate folder sizes.

    """

    def __init__(self, byte_count: int) -> None:
        self.size = byte_count

    def tell(self, *_args, **_kwargs) -> int:  # type: ignore[override]
        """Return the current position; for this wrapper, the total size.

        This satisfies the ``_SizedStream`` protocol used by
        :func:`file_size_to_string` without affecting behavior, since the
        helper reads the ``size`` attribute directly.
        """

        return int(self.size)

    def seek(self, *_args, **_kwargs) -> int:  # type: ignore[override]
        """Dummy ``seek`` implementation for protocol compatibility."""

        return int(self.size)


# =============================================================================
# Functions
# =============================================================================


def folder_size_to_string(path: str | Path, recursive: bool = True) -> str:
    """Return the total size of a folder as a human-readable string.

    This walks the folder, summing file sizes using ``Path.stat`` and then
    formatting the aggregate size via :func:`file_size_to_string`.

    Args
    ----
        path: Folder path.
        recursive: If ``True``, walk subfolders recursively.

    Returns
    -------
        str: Human-readable size such as ``"12.3 MB"``.

    """
    total_bytes = 0
    for file_path in folder_list_files(path=path, recursive=recursive):
        try:
            total_bytes += file_path.stat().st_size
        except OSError:
            # Skip files that cannot be stat'd (e.g., permissions issues).
            continue

    return file_size_to_string(_TotalSize(total_bytes))


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "folder_size_to_string",
]
