

# =============================================================================
# Docstring
# =============================================================================

"""
GZIP Compression Settings Module
==================================

Provides configurable settings for GZIP compression operations.

"""


# =============================================================================
# Classes
# =============================================================================


class GzipCompressionSettings:
    """
    Configuration settings for GZIP compression operations.

    Attributes
    ----------
    TMP_FILE_MAX_SIZE : int
        Maximum size in bytes before spooling to disk (default: 5MB).
    TMP_FILE_READ_SIZE : int
        Chunk size in bytes for file I/O operations (default: 1MB).
    TMP_DIR : None | str
        Temporary directory path (None uses system default).

    """

    TMP_FILE_MAX_SIZE: int = 5 * 1024 * 1024  # 5MB default
    TMP_FILE_READ_SIZE: int = 1024 * 1024  # 1MB chunks
    TMP_DIR: None | str = None


# =============================================================================
# Module Variables
# =============================================================================

settings: GzipCompressionSettings = GzipCompressionSettings()


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "GzipCompressionSettings",
    "settings",
]
