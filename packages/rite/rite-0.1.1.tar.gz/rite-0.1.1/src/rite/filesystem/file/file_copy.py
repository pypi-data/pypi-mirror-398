# =============================================================================
# Docstring
# =============================================================================

"""
File Copy Module
================

Provides utilities for copying files.

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


def copy_file(
    source_path: Path,
    destination_path: Path,
    overwrite: bool = True,
) -> None:
    """
    Copy a file from source to destination.

    Args
    ----
    source_path:
        Source file path.
    destination_path:
        Destination file path.
    overwrite:
        Whether to overwrite the destination if it exists.

    Raises
    ------
    FileNotFoundError
        If the source file does not exist.
    FileExistsError
        If the destination file exists and ``overwrite`` is ``False``.

    """
    if not source_path.is_file():
        raise FileNotFoundError(
            f"Source file does not exist: {source_path}",
        )

    if destination_path.exists() and not overwrite:
        raise FileExistsError(
            f"Destination file already exists: {destination_path}",
        )

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, destination_path)


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = ["copy_file"]
