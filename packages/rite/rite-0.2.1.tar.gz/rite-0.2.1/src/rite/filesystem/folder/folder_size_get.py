# =============================================================================
# Docstring
# =============================================================================

"""
Folder Size Get Module
======================

Calculate the total size of all files in a folder recursively.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from pathlib import Path

# =============================================================================
# Functions
# =============================================================================


def get_folder_size(folder_path: Path) -> int:
    """
    Calculate the total size of all files in a folder recursively.

    Args:
        folder_path (Path): The path to the folder.

    Returns:
        int: Total size in bytes.
    """
    total_size = 0

    for path in folder_path.rglob("*"):
        if path.is_file():
            try:
                total_size += path.stat().st_size
            except (OSError, PermissionError):
                # Optionally log or ignore unreadable files
                continue

    return total_size


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "get_folder_size",
]
