# =============================================================================
# Docstring
# =============================================================================

"""
Folder Ensure Exists
====================

Create a folder (and parents) if it does not already exist.

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


def folder_ensure_exists(path: str | Path) -> None:
    """
    Ensure that *path* exists as a directory, creating parents as needed.
    """

    directory_path = Path(path)
    directory_path.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "folder_ensure_exists",
]
