# =============================================================================
# Docstring
# =============================================================================

"""
Folder Create Module
====================

This module provides functions to create directories.

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


def create_directory(
    path: str | Path,
    mode: int = 0o777,
) -> Path:
    """
    Ensures the given directory exists and returns the Path object.

    Args:
        path (str | Path): The directory path to create.
        mode (int): Permissions mode (default: 0o777).

    Returns:
        Path: A pathlib.Path object representing the created or existing
            directory.

    """

    # Convert to Path object if a string is provided
    if isinstance(path, str):
        path = Path(path)

    # Create the directory if it doesn't exist with the specified mode
    path.mkdir(
        parents=True,
        exist_ok=True,
        mode=mode,
    )

    # Return the Path object
    return path


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "create_directory",
]
