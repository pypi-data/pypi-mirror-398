# =============================================================================
# Docstring
# =============================================================================

"""
File Read Bytes
===============

Read a file and return its contents as bytes.

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


def file_read_bytes(path: str | Path) -> bytes:
    """Read a file and return its contents as bytes.

    Args
    ----
        path: File path.

    Returns
    -------
        bytes: File content.

    """
    path_object = Path(path)
    return path_object.read_bytes()


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "file_read_bytes",
]
