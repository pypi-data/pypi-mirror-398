# =============================================================================
# Docstring
# =============================================================================

"""
Type Conversion Utilities
==========================

Basic Python type conversions.

This submodule provides utilities for converting between Python's
built-in types: int, float, str, bool, bytes, list, dict, set, tuple.

Examples
--------
>>> from rite.conversion.types import (
...     types_to_int,
...     types_to_bool,
...     types_to_list
... )
>>> types_to_int("42")
42
>>> types_to_bool("yes")
True
>>> types_to_list((1, 2, 3))
[1, 2, 3]

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .types_to_bool import FALSY, TRUTHY, types_to_bool
from .types_to_bytes import PROTECTED_TYPES, types_to_bytes
from .types_to_dict import types_to_dict
from .types_to_float import types_to_float
from .types_to_int import types_to_int
from .types_to_list import types_to_list
from .types_to_number import types_to_number
from .types_to_percentage import types_to_percentage
from .types_to_set import types_to_set
from .types_to_str import types_to_str
from .types_to_tuple import types_to_tuple

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    # Boolean
    "types_to_bool",
    "TRUTHY",
    "FALSY",
    # Bytes
    "types_to_bytes",
    "PROTECTED_TYPES",
    # Numeric
    "types_to_int",
    "types_to_float",
    "types_to_number",
    "types_to_percentage",
    # String
    "types_to_str",
    # Collections
    "types_to_list",
    "types_to_dict",
    "types_to_set",
    "types_to_tuple",
]
