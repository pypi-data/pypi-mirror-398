# =============================================================================
# Docstring
# =============================================================================

"""
Path Join
=========

Join path components.

Examples
--------
>>> from rite.system.path import path_join
>>> path_join("/tmp", "file.txt")
'/tmp/file.txt'

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


def path_join(*parts: str) -> str:
    """
    Join path components into single path.

    Args:
        *parts: Path components to join.

    Returns:
        Joined path string.

    Examples:
        >>> path_join("/tmp", "dir", "file.txt")
        '/tmp/dir/file.txt'
        >>> path_join(".", "file.txt")
        './file.txt'

    Notes:
        Uses platform-specific separator.
    """
    result: str = str(Path(*parts))
    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["path_join"]
