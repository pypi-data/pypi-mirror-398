# =============================================================================
# Docstring
# =============================================================================

"""
File Rename Module
==================

Provides utilities for renaming files within directories.

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


def rename_file(
    directory_path: str,
    old_file_name: str,
    new_file_name: str,
) -> None:
    """Rename a file within the specified directory.

    Args:
    ----
        directory_path: The path to the directory containing the file.
        old_file_name: The current name of the file.
        new_file_name: The new name for the file.

    Raises:
    ------
        FileNotFoundError: If the file to rename does not exist.
        OSError: If the rename operation fails.

    """
    dir_path = Path(directory_path)
    old_file = dir_path / old_file_name
    new_file = dir_path / new_file_name

    if not old_file.is_file():
        raise FileNotFoundError(f"File not found: {old_file}")

    old_file.rename(new_file)


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "rename_file",
]
