# =============================================================================
# Docstring
# =============================================================================

"""
Path Cleaning Module
====================

Provides path normalization and cleaning utilities.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Functions
# =============================================================================


def path_clean(path: str) -> str:
    """
    Clean a path by normalizing slashes.

    Ensures path has exactly one leading slash and no trailing slash.

    Args:
    ----
        path: Path string to clean.

    Returns:
    -------
        str: Cleaned path with single leading slash.

    Example:
    -------
        >>> path_clean("//path/to/file//")
        '/path/to/file'
        >>> path_clean("path/to/file")
        '/path/to/file'

    """
    return f"/{path.strip('/')}"


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "path_clean",
]
