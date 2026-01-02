"""Compression helpers for filesystem utilities."""

# Import | Local Modules
from .gzip_compress import compress_file
from .gzip_uncompress import uncompress_file

__all__ = [
    "compress_file",
    "uncompress_file",
]
