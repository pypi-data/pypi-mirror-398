# =============================================================================
# Docstring
# =============================================================================

"""
INI Module
==========

INI configuration file operations.

This submodule provides utilities for reading and writing INI/config
files with section and key-value operations.

Examples
--------
>>> from rite.serialization.ini import ini_read, ini_write
>>> config = ini_read("config.ini")
>>> ini_write("output.ini", config)

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .ini_get import ini_get
from .ini_read import ini_read
from .ini_set import ini_set
from .ini_write import ini_write

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "ini_read",
    "ini_write",
    "ini_get",
    "ini_set",
]
