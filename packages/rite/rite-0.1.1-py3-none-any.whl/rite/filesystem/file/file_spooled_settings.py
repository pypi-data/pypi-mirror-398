

# =============================================================================
# Docstring
# =============================================================================

"""
Spooled File Settings Module
============================

Configuration settings for spooled temporary file operations.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Classes
# =============================================================================


class SpooledFileSettings:
    """Configuration for spooled temporary file operations."""

    TMP_FILE_MAX_SIZE = 5 * 1024 * 1024  # 5MB default
    TMP_FILE_READ_SIZE = 1024 * 1024  # 1MB chunks
    TMP_DIR = None


# Global settings instance
settings = SpooledFileSettings()


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "SpooledFileSettings",
    "settings",
]
