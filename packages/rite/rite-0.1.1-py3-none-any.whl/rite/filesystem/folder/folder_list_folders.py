# =============================================================================
# Docstring
# =============================================================================

"""
Folder List Folders Module
==========================

Lists all subdirectories inside a given directory.

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


def list_folders(
    rootdir: str | Path,
    pattern: str | None = None,
    recursive: bool = False,
) -> list[Path]:
    """
    Lists all subdirectories inside a given directory.

    Args:
        rootdir (str | Path): The directory to search.
        pattern (str | None): Optional glob pattern to filter directories (e.g., 'data*').
        recursive (bool): If True, searches recursively through all subfolders.

    Returns:
        list[Path]: A list of Path objects representing found directories.
    """

    root_path = Path(rootdir)

    if not root_path.exists():
        raise FileNotFoundError(f"Directory not found: {root_path}")

    if not root_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {root_path}")

    if recursive:
        dirs = [p for p in root_path.rglob("*") if p.is_dir()]

    else:
        dirs = [p for p in root_path.iterdir() if p.is_dir()]

    if pattern:
        dirs = [d for d in dirs if d.match(pattern)]

    return dirs


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "list_folders",
]
