# =============================================================================
# Docstring
# =============================================================================

"""
Environment Module
==================

Environment variable operations.

This submodule provides utilities for reading and modifying
environment variables.

Examples
--------
>>> from rite.system.environment import env_get, env_set
>>> env_set("MY_VAR", "value")
>>> env_get("MY_VAR")
'value'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .env_delete import env_delete
from .env_get import env_get
from .env_list import env_list
from .env_set import env_set

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "env_get",
    "env_set",
    "env_delete",
    "env_list",
]
