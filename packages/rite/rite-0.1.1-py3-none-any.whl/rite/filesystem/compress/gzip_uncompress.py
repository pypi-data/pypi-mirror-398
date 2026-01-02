

# =============================================================================
# Docstring
# =============================================================================

"""
Gzip Decompression Module
=========================

Provides gzip decompression functionality for file objects.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import gzip
import os
import tempfile
from typing import BinaryIO

# Import | Local Modules
from ..file.file_spooled import create_spooled_temporary_file

# =============================================================================
# Functions
# =============================================================================


def uncompress_file(
    input_file: BinaryIO,
    filename: str,
) -> tuple[tempfile.SpooledTemporaryFile, str]:
    """Decompress a gzip file and return the uncompressed output.

    Args:
    ----
        input_file: Gzip-compressed file-like object.
        filename: Original filename (used to derive uncompressed name).

    Returns:
    -------
        Tuple of (decompressed file object, filename without .gz extension).

    """
    gzip_file = gzip.GzipFile(fileobj=input_file, mode="rb")
    try:
        input_file.seek(0)
        output_file = create_spooled_temporary_file(fileobj=gzip_file)
    finally:
        gzip_file.close()
    new_basename = os.path.basename(filename).replace(".gz", "")
    return output_file, new_basename


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "uncompress_file",
]
