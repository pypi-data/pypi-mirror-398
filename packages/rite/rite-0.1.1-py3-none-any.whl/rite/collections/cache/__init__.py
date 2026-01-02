

# =============================================================================
# Docstring
# =============================================================================

"""
Cache Collections Module
=========================

Provides caching data structures with various eviction policies.

Classes:
--------
- LRUCache: Least Recently Used cache
- LFUCache: Least Frequently Used cache
- TTLCache: Time-To-Live cache

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

from .lfu_cache import LFUCache

# Import | Local
from .lru_cache import LRUCache
from .ttl_cache import TTLCache

# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "LRUCache",
    "LFUCache",
    "TTLCache",
]
