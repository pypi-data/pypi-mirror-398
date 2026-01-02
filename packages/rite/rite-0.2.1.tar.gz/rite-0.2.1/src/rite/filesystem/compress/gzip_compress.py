# =============================================================================
# Docstring
# =============================================================================

"""
Gzip Compression Module
=======================

Provides gzip compression functionality for file objects.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import gzip
from shutil import copyfileobj
import tempfile
from typing import BinaryIO

# Import | Local Modules
from ..file.file_spooled import create_spooled_temporary_file
from .gzip_settings import settings

# =============================================================================
# Functions
# =============================================================================


def compress_file(
    input_file: BinaryIO,
    filename: str,
) -> tuple[tempfile.SpooledTemporaryFile, str]:
    """Compress a file using gzip and return the compressed output.

    Args:
    ----
        input_file: File-like object to compress.
        filename: Original filename (used as internal gzip metadata).

    Returns:
    -------
        Tuple of (compressed file object, new filename with .gz extension).

    """
    output_file = create_spooled_temporary_file()
    new_filename: str = f"{filename}.gz"
    gzip_file = gzip.GzipFile(
        filename=filename, fileobj=output_file, mode="wb"
    )
    try:
        input_file.seek(0)
        copyfileobj(input_file, gzip_file, settings.TMP_FILE_READ_SIZE)
    finally:
        gzip_file.close()
    return output_file, new_filename


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "compress_file",
]
