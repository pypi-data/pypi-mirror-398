# =============================================================================
# Docstring
# =============================================================================

"""
Collections Module
==================

Comprehensive data structures and utilities for common programming
patterns, organized into semantic submodules.

Submodules
----------
- list: List manipulation (unique, flatten, chunk, group, partition)
- dict: Dictionary operations (merge, filter, invert, deep access)
- set: Set operations (union, intersection, difference)
- buffer: Ring buffers, circular buffers, and sliding windows
- cache: LRU, LFU, and TTL caches
- queue: Priority queues, circular queues, and deque wrappers
- tree: Tree nodes, binary trees, tries, and nested sets
- pattern: Design patterns (singleton, observer, object pool)

Examples
--------
>>> from rite.collections import list_unique, dict_merge
>>> list_unique([1, 2, 2, 3])
[1, 2, 3]
>>> dict_merge({"a": 1}, {"b": 2})
{'a': 1, 'b': 2}

>>> from rite.collections import CircularBuffer, LRUCache
>>> buf = CircularBuffer(5)
>>> cache = LRUCache(100)
"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from typing import List

# Import | Local Modules
# Import | Local | Buffer
from .buffer import BoundedBuffer, CircularBuffer, RingBuffer, SlidingWindow

# Import | Local | Cache
from .cache import LFUCache, LRUCache, TTLCache

# Import | Local | Dict Operations
from .dict import (
    dict_deep_get,
    dict_deep_set,
    dict_filter,
    dict_invert,
    dict_merge,
)

# Import | Local | List Operations
from .list import (
    list_chunk,
    list_flatten,
    list_group_by,
    list_interleave,
    list_partition,
    list_unique,
)

# Import | Local | Pattern
from .pattern import ObjectPool, Observable, Observer, SingletonMeta

# Import | Local | Queue
from .queue import CircularQueue, DequeWrapper, PriorityQueue

# Import | Local | Set Operations
from .set import (
    set_difference,
    set_intersection,
    set_symmetric_difference,
    set_union,
)

# Import | Local | Tree
from .tree import BinaryTreeNode, NestedSetStructure, TreeNode, Trie

# =============================================================================
# Exports
# =============================================================================

__all__: List[str] = [
    # List Operations
    "list_chunk",
    "list_flatten",
    "list_group_by",
    "list_interleave",
    "list_partition",
    "list_unique",
    # Dict Operations
    "dict_deep_get",
    "dict_deep_set",
    "dict_filter",
    "dict_invert",
    "dict_merge",
    # Set Operations
    "set_difference",
    "set_intersection",
    "set_symmetric_difference",
    "set_union",
    # Buffer
    "BoundedBuffer",
    "CircularBuffer",
    "RingBuffer",
    "SlidingWindow",
    # Cache
    "LFUCache",
    "LRUCache",
    "TTLCache",
    # Pattern
    "ObjectPool",
    "Observable",
    "Observer",
    "SingletonMeta",
    # Queue
    "CircularQueue",
    "DequeWrapper",
    "PriorityQueue",
    # Tree
    "BinaryTreeNode",
    "NestedSetStructure",
    "TreeNode",
    "Trie",
]
