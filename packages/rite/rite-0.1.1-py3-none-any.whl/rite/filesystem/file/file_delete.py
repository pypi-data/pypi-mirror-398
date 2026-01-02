# =============================================================================
# Docstring
# =============================================================================

"""
File Deletion Module
====================

Provides utilities for deleting files safely.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from pathlib import Path

# Import | Libraries

# Import | Local Modules


# =============================================================================
# Functions
# =============================================================================


def delete_file(
    directory_path: str,
    file_name: str,
) -> None:
    """
    Delete a file within the specified directory.

    Args:
    ----
        directory_path: The path to the directory containing the file.
        file_name: The name of the file to delete.

    Raises:
    ------
        FileNotFoundError: If the file does not exist.
        OSError: If the file could not be deleted due to an OS error.

    """

    file_path = Path(directory_path) / file_name

    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_path.unlink()


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "delete_file",
]
