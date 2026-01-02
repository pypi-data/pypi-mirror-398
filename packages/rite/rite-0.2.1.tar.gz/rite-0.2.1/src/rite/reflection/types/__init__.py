# =============================================================================
# Docstring
# =============================================================================

"""
Types Module
============

Type checking utilities.

This submodule provides utilities for checking object types
at runtime.

Examples
--------
>>> from rite.reflection.types import (
...     types_is_class,
...     types_is_function
... )
>>> types_is_class(str)
True
>>> types_is_function(lambda x: x)
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .types_is_class import types_is_class
from .types_is_function import types_is_function
from .types_is_method import types_is_method
from .types_is_module import types_is_module

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "types_is_class",
    "types_is_function",
    "types_is_method",
    "types_is_module",
]
