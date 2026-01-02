# =============================================================================
# Docstring
# =============================================================================

"""
File Move Module
================

Provides utilities for moving files between directories.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import shutil
from pathlib import Path

# Import | Libraries

# Import | Local Modules


# =============================================================================
# Functions
# =============================================================================


def move_file(
    directory_path: str,
    file_name: str,
    new_directory: str,
) -> None:
    """
    Move a file from the current directory to a specified new directory.

    Args:
    ----
        directory_path: The path of the current directory.
        file_name: The name of the file to be moved.
        new_directory: The destination directory.

    Raises:
    ------
        FileNotFoundError: If the file to move does not exist.
        OSError: If the file could not be moved.

    Note:
    ----
        If the destination directory doesn't exist, it will be created.

    """

    source_path = Path(directory_path) / file_name
    destination_directory_path = Path(new_directory)
    destination_path = destination_directory_path / file_name

    if not source_path.is_file():
        raise FileNotFoundError(f"File not found: {source_path}")

    destination_directory_path.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source_path), str(destination_path))


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "move_file",
]
