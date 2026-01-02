# =============================================================================
# Docstring
# =============================================================================

"""
Circular Queue
==============

A circular queue with fixed capacity.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from typing import Any

# Import | Libraries

# Import | Local Modules


# =============================================================================
# Classes
# =============================================================================


class CircularQueue:
    """
    CircularQueue Class
    ===================

    A fixed-size circular queue (FIFO).

    """

    def __init__(self, capacity: int) -> None:
        """
        Initialize a circular queue.

        Args:
        ----
            capacity: Maximum capacity of the queue.

        """
        if capacity < 1:
            raise ValueError("Capacity must be at least 1")

        self.capacity = capacity
        self._data: list[Any | None] = [None] * capacity
        self._front = 0
        self._rear = -1
        self._size = 0

    def enqueue(self, item: Any) -> bool:
        """
        Add an item to the rear of the queue.

        Args:
        ----
            item: Item to add.

        """
        if self.is_full():
            raise OverflowError("Queue is full")

        self._rear = (self._rear + 1) % self.capacity
        self._data[self._rear] = item
        self._size += 1
        return True

    def dequeue(self) -> Any:
        """
        Remove and return item from front of queue.

        Returns:
        -------
            Any: The front item.

        """
        if self.is_empty():
            raise IndexError("Queue is empty")

        item = self._data[self._front]
        self._data[self._front] = None
        self._front = (self._front + 1) % self.capacity
        self._size -= 1
        return item

    def peek(self) -> Any:
        """
        Return front item without removing it.

        Returns:
        -------
            Any: The front item.

        """
        if self.is_empty():
            return None
        return self._data[self._front]

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self._size == 0

    def is_full(self) -> bool:
        """Check if queue is full."""
        return self._size == self.capacity

    def clear(self) -> None:
        """Clear all items from queue."""
        self._data = [None] * self.capacity
        self._front = 0
        self._rear = -1
        self._size = 0

    def __len__(self) -> int:
        """Return number of items in queue."""
        return self._size

    def __repr__(self) -> str:
        """Return string representation."""
        return f"CircularQueue(capacity={self.capacity}, size={self._size})"


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "CircularQueue",
]
