# =============================================================================
# Docstring
# =============================================================================

"""
List Operations Module
======================

Utilities for list manipulation and transformation.

Functions
---------
- list_unique: Remove duplicates while preserving order.
- list_flatten: Flatten nested lists recursively.
- list_chunk: Split list into chunks.
- list_group_by: Group items by key function or attribute.
- list_partition: Split list into two based on predicate.
- list_interleave: Interleave multiple lists.

Examples
--------
>>> from rite.collections.list import list_unique, list_chunk
>>> list_unique([1, 2, 2, 3])
[1, 2, 3]
>>> list_chunk([1, 2, 3, 4, 5], size=2)
[[1, 2], [3, 4], [5]]
"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .list_chunk import list_chunk
from .list_flatten import list_flatten
from .list_group_by import list_group_by
from .list_interleave import list_interleave
from .list_partition import list_partition
from .list_unique import list_unique

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "list_chunk",
    "list_flatten",
    "list_group_by",
    "list_interleave",
    "list_partition",
    "list_unique",
]
