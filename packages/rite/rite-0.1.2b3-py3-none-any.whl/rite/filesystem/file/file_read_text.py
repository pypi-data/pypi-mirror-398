# =============================================================================
# Docstring
# =============================================================================

"""
File Read Text
==============

Read a file and return its contents as text.

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


def file_read_text(path: str | Path, encoding: str = "utf-8") -> str:
    """Read a file and return its contents as text.

    Args
    ----
        path: File path.
        encoding: Text encoding to use.

    Returns
    -------
        str: File content.

    """
    path_object = Path(path)
    return path_object.read_text(encoding=encoding)


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "file_read_text",
]
