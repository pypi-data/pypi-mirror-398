# =============================================================================
# Docstring
# =============================================================================

"""
Inspection Module
=================

Object inspection utilities.

This submodule provides utilities for inspecting objects,
classes, and modules at runtime.

Examples
--------
>>> from rite.reflection.inspection import (
...     inspection_get_members,
...     inspection_get_methods
... )
>>> import json
>>> members = inspection_get_members(json)
>>> len(members) > 0
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .inspection_get_functions import inspection_get_functions
from .inspection_get_members import inspection_get_members
from .inspection_get_methods import inspection_get_methods
from .inspection_get_source import inspection_get_source

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "inspection_get_members",
    "inspection_get_methods",
    "inspection_get_functions",
    "inspection_get_source",
]
