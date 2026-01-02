# =============================================================================
# Docstring
# =============================================================================

"""
LFU Cache
=========

Least Frequently Used (LFU) cache implementation.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections import defaultdict
from typing import Any

# =============================================================================
# Classes
# =============================================================================


class LFUCache:
    """
    LFUCache Class
    ==============

    A Least Frequently Used (LFU) cache with fixed capacity.

    Parameters
    ----------
    capacity : int
        Maximum number of items to store in cache.

    """

    def __init__(self, capacity: int) -> None:
        """
        Initialize an LFU cache.

        Args:
        ----
            capacity: Maximum cache size.

        """
        if capacity < 1:
            raise ValueError("Capacity must be at least 1")

        self.capacity = capacity
        self._cache: dict[Any, Any] = {}
        self._freq: dict[Any, int] = {}
        self._min_freq = 0
        self._freq_lists: dict[int, list[Any]] = defaultdict(list)

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

        # Increment frequency
        self._increment_freq(key)
        return self._cache[key]

    def put(self, key: Any, value: Any) -> None:
        """
        Add or update a key-value pair in cache.

        Args:
        ----
            key: The key to store.
            value: The value to store.

        """
        if self.capacity == 0:
            return

        if key in self._cache:
            # Update existing key
            self._cache[key] = value
            self._increment_freq(key)
        else:
            # Add new key
            if len(self._cache) >= self.capacity:
                # Evict least frequently used
                self._evict()

            self._cache[key] = value
            self._freq[key] = 1
            self._freq_lists[1].append(key)
            self._min_freq = 1

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
        if key not in self._cache:
            return False

        del self._cache[key]
        freq = self._freq[key]
        del self._freq[key]
        self._freq_lists[freq].remove(key)
        return True

    def clear(self) -> None:
        """Clear all items from cache."""
        self._cache.clear()
        self._freq.clear()
        self._freq_lists.clear()
        self._min_freq = 0

    def _increment_freq(self, key: Any) -> None:
        """Increment the frequency of a key."""
        freq = self._freq[key]
        self._freq[key] = freq + 1

        # Remove from old frequency list
        self._freq_lists[freq].remove(key)
        if len(self._freq_lists[freq]) == 0 and freq == self._min_freq:
            self._min_freq += 1

        # Add to new frequency list
        self._freq_lists[freq + 1].append(key)

    def _evict(self) -> None:
        """Evict the least frequently used item."""
        # Get key from minimum frequency list
        key_to_evict = self._freq_lists[self._min_freq][0]
        self._freq_lists[self._min_freq].pop(0)

        # Remove from cache
        del self._cache[key_to_evict]
        del self._freq[key_to_evict]

    def __len__(self) -> int:
        """Return number of items in cache."""
        return len(self._cache)

    def __contains__(self, key: Any) -> bool:
        """Check if key is in cache."""
        return key in self._cache

    def __repr__(self) -> str:
        """Return string representation."""
        return f"LFUCache(capacity={self.capacity}, size={len(self._cache)})"


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "LFUCache",
]
