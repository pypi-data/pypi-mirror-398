# =============================================================================
# Docstring
# =============================================================================

"""
Path Exists
===========

Check if path exists.

Examples
--------
>>> from rite.system.path import path_exists
>>> path_exists("/tmp")
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


def path_exists(path: str | Path) -> bool:
    """
    Check if path exists.

    Args:
        path: Path to check.

    Returns:
        True if exists, False otherwise.

    Examples:
        >>> path_exists("/tmp")
        True
        >>> path_exists("/nonexistent")
        False

    Notes:
        Works for files and directories.
    """
    return Path(path).exists()


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["path_exists"]
