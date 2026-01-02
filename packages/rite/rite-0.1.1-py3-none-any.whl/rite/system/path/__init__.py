# =============================================================================
# Docstring
# =============================================================================

"""
Path Module
===========

Path operation utilities.

This submodule provides utilities for path operations and queries
using pathlib.

Examples
--------
>>> from rite.system.path import path_exists, path_join
>>> path_exists("/tmp")
True
>>> path_join("/tmp", "file.txt")
'/tmp/file.txt'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .path_absolute import path_absolute
from .path_exists import path_exists
from .path_is_dir import path_is_dir
from .path_is_file import path_is_file
from .path_join import path_join

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "path_exists",
    "path_is_file",
    "path_is_dir",
    "path_absolute",
    "path_join",
]
