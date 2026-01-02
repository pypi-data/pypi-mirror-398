# =============================================================================
# Docstring
# =============================================================================

"""
Path Is File
============

Check if path is a file.

Examples
--------
>>> from rite.system.path import path_is_file
>>> path_is_file("/etc/hosts")
True

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


def path_is_file(path: str | Path) -> bool:
    """
    Check if path is a file.

    Args:
        path: Path to check.

    Returns:
        True if file, False otherwise.

    Examples:
        >>> path_is_file("/etc/hosts")
        True
        >>> path_is_file("/tmp")
        False

    Notes:
        Returns False if path doesn't exist.
    """
    return Path(path).is_file()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["path_is_file"]
