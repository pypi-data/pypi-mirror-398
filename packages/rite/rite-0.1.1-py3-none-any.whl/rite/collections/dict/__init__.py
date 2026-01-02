# =============================================================================
# Docstring
# =============================================================================

"""
Dictionary Operations Module
============================

Utilities for dictionary manipulation and transformation.

Functions
---------
- dict_merge: Merge multiple dictionaries.
- dict_filter: Filter dictionary by predicate.
- dict_invert: Swap keys and values.
- dict_deep_get: Get nested value safely.
- dict_deep_set: Set nested value, creating paths.

Examples
--------
>>> from rite.collections.dict import dict_merge, dict_filter
>>> dict_merge({"a": 1}, {"b": 2})
{'a': 1, 'b': 2}
>>> dict_filter({"a": 1, "b": 2}, lambda k, v: v > 1)
{'b': 2}
"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .dict_deep_get import dict_deep_get
from .dict_deep_set import dict_deep_set
from .dict_filter import dict_filter
from .dict_invert import dict_invert
from .dict_merge import dict_merge

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "dict_deep_get",
    "dict_deep_set",
    "dict_filter",
    "dict_invert",
    "dict_merge",
]
