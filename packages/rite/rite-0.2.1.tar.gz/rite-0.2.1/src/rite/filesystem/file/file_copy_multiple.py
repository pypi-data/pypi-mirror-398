# =============================================================================
# Docstring
# =============================================================================

"""
Multiple File Copy Module
=========================

Provides utilities for copying multiple files or entire directories.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from pathlib import Path
import shutil

# =============================================================================
# Functions
# =============================================================================


def copy_files(
    source_dir: Path,
    target_dir: Path,
    recursive: bool = False,
    overwrite: bool = True,
    preserve_metadata: bool = True,
) -> None:
    """
    Copy files from source directory to target directory.

    Args:
    ----
        source_dir: Path to the source directory.
        target_dir: Path to the destination directory.
        recursive: If True, copy all files recursively from subdirectories.
        overwrite: If True, overwrite files if they already exist.
        preserve_metadata: If True, preserve file metadata using copy2.

    Raises:
    ------
        FileNotFoundError: If the source directory does not exist.

    """
    if not source_dir.exists():
        raise FileNotFoundError(
            f"Source directory does not exist: {source_dir}"
        )

    target_dir.mkdir(parents=True, exist_ok=True)

    copy_fn = shutil.copy2 if preserve_metadata else shutil.copy

    if recursive:
        for path in source_dir.rglob("*"):
            if path.is_file():
                relative_path = path.relative_to(source_dir)
                dest_path = target_dir / relative_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                if not dest_path.exists() or overwrite:
                    copy_fn(path, dest_path)
    else:
        for path in source_dir.glob("*"):
            if path.is_file():
                dest_path = target_dir / path.name
                if not dest_path.exists() or overwrite:
                    copy_fn(path, dest_path)


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "copy_files",
]
