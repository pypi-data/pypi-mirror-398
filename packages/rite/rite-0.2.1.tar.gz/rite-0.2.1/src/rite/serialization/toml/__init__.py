# =============================================================================
# Docstring
# =============================================================================

"""
TOML Module
===========

TOML file operations.

This submodule provides utilities for reading TOML files using the
stdlib tomllib (Python 3.11+). Write operations are not supported
in stdlib.

Examples
--------
>>> from rite.serialization.toml import toml_load
>>> config = toml_load("config.toml")

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .toml_load import toml_load
from .toml_loads import toml_loads

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "toml_load",
    "toml_loads",
]
