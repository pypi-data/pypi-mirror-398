# =============================================================================
# Docstring
# =============================================================================

"""
Folder List Files
=================

Iterate over files contained in a directory.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from pathlib import Path
from typing import Iterator

# Import | Libraries

# Import | Local Modules


# =============================================================================
# Functions
# =============================================================================


def folder_list_files(
    path: str | Path,
    recursive: bool = False,
) -> Iterator[Path]:
    """
    Yield files in the given folder.

    Args
    ----
        path: Folder path.
        recursive: If ``True``, walk recursively using ``Path.rglob``.

    Yields
    ------
        pathlib.Path: File paths found under *path*.

    """
    base_path = Path(path)

    if not recursive:
        yield from (
            candidate
            for candidate in base_path.iterdir()
            if candidate.is_file()
        )
    else:
        for candidate in base_path.rglob("*"):
            if candidate.is_file():
                yield candidate


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "folder_list_files",
]
