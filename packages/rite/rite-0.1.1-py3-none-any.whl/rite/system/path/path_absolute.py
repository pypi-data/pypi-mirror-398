# =============================================================================
# Docstring
# =============================================================================

"""
Path Absolute
=============

Get absolute path.

Examples
--------
>>> from rite.system.path import path_absolute
>>> path_absolute(".")
'/current/working/directory'

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


def path_absolute(path: str | Path) -> str:
    """
    Get absolute path as string.

    Args:
        path: Relative or absolute path.

    Returns:
        Absolute path string.

    Examples:
        >>> path_absolute(".")
        '/current/working/directory'
        >>> path_absolute("../parent")
        '/parent/directory'

    Notes:
        Resolves symlinks and relative paths.
    """
    result: str = str(Path(path).resolve())
    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["path_absolute"]
