# =============================================================================
# Docstring
# =============================================================================

"""
Tree Node
=========

Generic tree node implementation with children and parent tracking.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from typing import Any, Self

# =============================================================================
# Classes
# =============================================================================


class TreeNode:
    """
    TreeNode Class
    ==============

    A generic tree node that can have multiple children.

    Parameters
    ----------
    value : Any
        The value stored in this node.
    children : list[TreeNode] | None
        Optional list of child nodes.

    """

    def __init__(
        self,
        value: Any,
        children: list[Self] | None = None,
    ) -> None:
        """
        Initialize a tree node.

        Args:
        ----
            value: The value to store in this node.
            children: Optional list of child nodes.

        """
        self.value = value
        self.children: list[Self] = children if children else []
        self.parent: Self | None = None

        # Set parent references for children
        for child in self.children:
            child.parent = self

    def add_child(self, child: Self) -> None:
        """
        Add a child node.

        Args:
        ----
            child: The child node to add.

        """
        self.children.append(child)
        child.parent = self

    def remove_child(self, child: Self) -> bool:
        """
        Remove a child node.

        Args:
        ----
            child: The child node to remove.

        Returns:
        -------
            bool: True if child was removed, False if not found.

        """
        try:
            self.children.remove(child)
            child.parent = None
            return True
        except ValueError:
            return False

    def is_leaf(self) -> bool:
        """
        Check if this node is a leaf (has no children).

        Returns:
        -------
            bool: True if node has no children.

        """
        return len(self.children) == 0

    def is_root(self) -> bool:
        """
        Check if this node is a root (has no parent).

        Returns:
        -------
            bool: True if node has no parent.

        """
        return self.parent is None

    def get_depth(self) -> int:
        """
        Get the depth of this node (distance from root).

        Returns:
        -------
            int: Depth of node (root is 0).

        """
        depth = 0
        current = self.parent
        while current is not None:
            depth += 1
            current = current.parent
        return depth

    def get_height(self) -> int:
        """
        Get the height of the subtree rooted at this node.

        Returns:
        -------
            int: Height of subtree (leaf is 0).

        """
        if self.is_leaf():
            return 0
        return 1 + max(child.get_height() for child in self.children)

    def get_siblings(self) -> list[Self]:
        """
        Get all sibling nodes (nodes with same parent).

        Returns:
        -------
            list[TreeNode]: List of sibling nodes.

        """
        if self.parent is None:
            return []
        return [child for child in self.parent.children if child is not self]

    def get_ancestors(self) -> list[Self]:
        """
        Get all ancestor nodes from parent to root.

        Returns:
        -------
            list[TreeNode]: List of ancestors in order (parent to root).

        """
        ancestors = []
        current = self.parent
        while current is not None:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def traverse_preorder(self) -> list[Self]:
        """
        Traverse tree in pre-order (root, then children).

        Returns:
        -------
            list[TreeNode]: Nodes in pre-order.

        """
        result: list[Self] = [self]
        for child in self.children:
            result.extend(child.traverse_preorder())
        return result

    def traverse_postorder(self) -> list[Self]:
        """
        Traverse tree in post-order (children, then root).

        Returns:
        -------
            list[TreeNode]: Nodes in post-order.

        """
        result: list[Self] = []
        for child in self.children:
            result.extend(child.traverse_postorder())
        result.append(self)
        return result

    def traverse_levelorder(self) -> list[Self]:
        """
        Traverse tree in level-order (breadth-first).

        Returns:
        -------
            list[TreeNode]: Nodes in level-order.

        """
        result: list[Self] = []
        queue = [self]
        while queue:
            node = queue.pop(0)
            result.append(node)
            queue.extend(node.children)
        return result

    def __repr__(self) -> str:
        """Return string representation."""
        return f"TreeNode(value={self.value}, children={len(self.children)})"


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "TreeNode",
]
