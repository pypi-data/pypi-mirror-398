# =============================================================================
# Docstring
# =============================================================================

"""
Path Leaf Extraction
===================

Get the leaf (final component) of a path.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from pathlib import Path

# Import | Libraries

# Import | Local Modules


# =============================================================================
# Functions
# =============================================================================


def path_leaf(path: str) -> str:
    """
    Return the last part (leaf) of a given file path.

    Args:
        path: The input file path

    Returns:
        The leaf name (file or folder name) of the path

    Example:
        >>> path_leaf("/some/folder/file.txt")
        'file.txt'
        >>> path_leaf("Documents/project")
        'project'
    """
    return Path(path).name


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "path_leaf",
]
