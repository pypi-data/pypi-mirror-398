# =============================================================================
# Docstring
# =============================================================================

"""
Memoization Module
==================

Function result caching utilities.

This submodule provides decorators for memoizing function results
with various caching strategies.

Examples
--------
>>> from rite.functional.memoization import (
...     memoization_memoize,
...     memoization_lru_cache
... )
>>> @memoization_memoize()
... def fibonacci(n):
...     if n <= 1:
...         return n
...     return fibonacci(n-1) + fibonacci(n-2)

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .memoization_lru_cache import memoization_lru_cache
from .memoization_memoize import memoization_memoize

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "memoization_memoize",
    "memoization_lru_cache",
]
