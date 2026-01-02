

# =============================================================================
# Docstring
# =============================================================================

"""
Spooled Temporary File Creation Module
======================================

Provides utilities for creating spooled temporary files.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import tempfile
from pathlib import Path
from shutil import copyfileobj

# Import | Local Modules
from .file_spooled_settings import settings

# =============================================================================
# Functions
# =============================================================================


def create_spooled_temporary_file(
    filepath: str | Path | None = None,
    fileobj: object | None = None,
) -> tempfile.SpooledTemporaryFile:
    """Create a spooled temporary file optionally seeded from a path or file.

    If ``filepath`` or ``fileobj`` is provided, the content is copied into the
    new spooled file. Callers own the returned file object's lifecycle and
    should close it when finished.

    Args:
    ----
        filepath: Optional path to a file to copy into the spooled file.
        fileobj: Optional file-like object to copy into the spooled file.

    Returns:
    -------
        A spooled temporary file with the content copied if provided.

    """
    spooled_file = tempfile.SpooledTemporaryFile(
        max_size=settings.TMP_FILE_MAX_SIZE,
        dir=settings.TMP_DIR,
        mode="w+b",
    )
    if filepath:
        with open(file=filepath, mode="r+b") as input_file:
            input_file.seek(0)
            copyfileobj(
                fsrc=input_file,
                fdst=spooled_file,
                length=settings.TMP_FILE_READ_SIZE,
            )
    elif fileobj is not None:
        fileobj.seek(0)
        copyfileobj(
            fsrc=fileobj,
            fdst=spooled_file,
            length=settings.TMP_FILE_READ_SIZE,
        )

    spooled_file.seek(0)
    return spooled_file


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "create_spooled_temporary_file",
]
