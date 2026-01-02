# =============================================================================
# Docstring
# =============================================================================

"""
Path Is Directory
=================

Check if path is a directory.

Examples
--------
>>> from rite.system.path import path_is_dir
>>> path_is_dir("/tmp")
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


def path_is_dir(path: str | Path) -> bool:
    """
    Check if path is a directory.

    Args:
        path: Path to check.

    Returns:
        True if directory, False otherwise.

    Examples:
        >>> path_is_dir("/tmp")
        True
        >>> path_is_dir("/etc/hosts")
        False

    Notes:
        Returns False if path doesn't exist.
    """
    return Path(path).is_dir()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["path_is_dir"]
