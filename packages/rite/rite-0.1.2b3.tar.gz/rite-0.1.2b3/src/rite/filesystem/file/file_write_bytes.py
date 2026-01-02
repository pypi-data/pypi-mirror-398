# =============================================================================
# Docstring
# =============================================================================

"""
File Write Bytes
================

Write bytes to a file, creating parent directories if needed.

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


def file_write_bytes(path: str | Path, data: bytes) -> None:
    """Write bytes to a file, creating parent directories if needed.

    Args
    ----
        path: File path.
        data: Bytes content to write.

    """
    path_object = Path(path)
    path_object.parent.mkdir(parents=True, exist_ok=True)
    path_object.write_bytes(data)


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "file_write_bytes",
]
