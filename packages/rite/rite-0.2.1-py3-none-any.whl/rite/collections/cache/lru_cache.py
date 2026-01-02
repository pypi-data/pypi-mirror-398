# =============================================================================
# Docstring
# =============================================================================

"""
LRU Cache
=========

Least Recently Used (LRU) cache implementation.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections import OrderedDict
from typing import Any

# =============================================================================
# Classes
# =============================================================================


class LRUCache:
    """
    LRUCache Class
    ==============

    A Least Recently Used (LRU) cache with fixed capacity.

    Parameters
    ----------
    capacity : int
        Maximum number of items to store in cache.

    """

    def __init__(self, capacity: int) -> None:
        """
        Initialize an LRU cache.

        Args:
        ----
            capacity: Maximum cache size.

        """
        if capacity < 1:
            raise ValueError("Capacity must be at least 1")

        self.capacity = capacity
        self._cache: OrderedDict[Any, Any] = OrderedDict()

    def get(self, key: Any) -> Any | None:
        """
        Get a value from cache.

        Args:
        ----
            key: The key to look up.

        Returns:
        -------
            Any | None: The value or None if not found.

        """
        if key not in self._cache:
            return None

        # Move to end (mark as recently used)
        self._cache.move_to_end(key)
        return self._cache[key]

    def put(self, key: Any, value: Any) -> None:
        """
        Add or update a key-value pair in cache.

        Args:
        ----
            key: The key to store.
            value: The value to store.

        """
        if key in self._cache:
            # Update existing key
            self._cache.move_to_end(key)
        else:
            # Add new key
            if len(self._cache) >= self.capacity:
                # Remove least recently used item (first item)
                self._cache.popitem(last=False)

        self._cache[key] = value

    def delete(self, key: Any) -> bool:
        """
        Delete a key from cache.

        Args:
        ----
            key: The key to delete.

        Returns:
        -------
            bool: True if key was deleted, False if not found.

        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all items from cache."""
        self._cache.clear()

    def keys(self) -> list[Any]:
        """
        Get all keys in cache.

        Returns:
        -------
            list[Any]: List of keys in order of use.

        """
        return list(self._cache.keys())

    def values(self) -> list[Any]:
        """
        Get all values in cache.

        Returns:
        -------
            list[Any]: List of values.

        """
        return list(self._cache.values())

    def items(self) -> list[tuple[Any, Any]]:
        """
        Get all key-value pairs.

        Returns:
        -------
            list[tuple[Any, Any]]: List of (key, value) tuples.

        """
        return list(self._cache.items())

    def __len__(self) -> int:
        """Return number of items in cache."""
        return len(self._cache)

    def __contains__(self, key: Any) -> bool:
        """Check if key is in cache."""
        return key in self._cache

    def __repr__(self) -> str:
        """Return string representation."""
        return f"LRUCache(capacity={self.capacity}, size={len(self._cache)})"


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "LRUCache",
]
