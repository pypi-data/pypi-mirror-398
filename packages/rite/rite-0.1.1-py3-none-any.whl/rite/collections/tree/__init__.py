

# =============================================================================
# Docstring
# =============================================================================

"""
Tree Collections Module
========================

Provides tree data structures and hierarchical data management.

Classes:
--------
- NestedSetStructure: Hierarchical parent-child relationship manager
- TreeNode: Generic tree node with children
- BinaryTreeNode: Binary tree node implementation
- Trie: Prefix tree for string operations

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

from .binary_tree_node import BinaryTreeNode

# Import | Local
from .nested_set import NestedSetStructure
from .tree_node import TreeNode
from .trie import Trie

# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "NestedSetStructure",
    "TreeNode",
    "BinaryTreeNode",
    "Trie",
]
