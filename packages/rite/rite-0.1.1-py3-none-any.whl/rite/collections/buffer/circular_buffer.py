# =============================================================================
# Docstring
# =============================================================================

"""
Circular Buffer
===============

A circular buffer (ring buffer) implementation that overwrites the oldest
entries when the buffer reaches its maximum capacity.

Classes:
--------
- CircularBuffer: A fixed-size buffer with circular indexing.

Features:
---------
- Append new elements, overwriting the oldest if the buffer is full.
- Retrieve all elements in the correct order.
- Check if the buffer is empty or full.

Usage:
------
    buffer = CircularBuffer(size=5)
    buffer.append(1)
    buffer.append(2)
    print(buffer.get_all())  # Outputs: [1, 2]
    buffer.append(3)
    buffer.append(4)
    buffer.append(5)
    print(buffer.get_all())  # Outputs: [1, 2, 3, 4, 5]
    buffer.append(6)
    print(buffer.get_all())  # Outputs: [6, 2, 3, 4, 5]

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


class CircularBuffer:
    """
    CircularBuffer Class
    ====================

    A fixed-size buffer that overwrites the oldest data when full.

    Attributes
    ----------
    size : int
        The maximum number of elements the buffer can hold.
    buffer : list[Any | None]
        The internal list storing buffer elements.
    index : int
        The current index for the next write operation.
    full : bool
        Indicates if the buffer has reached its maximum capacity.

    Methods
    -------
    append(value: Any) -> None:
        Adds a value to the buffer, overwriting the oldest element if full.
    get_all() -> list[Any | None]:
        Retrieves all elements in the buffer in the correct order.
    is_empty() -> bool:
        Checks if the buffer is empty.
    is_full() -> bool:
        Checks if the buffer is full.
    """

    def __init__(self, size: int) -> None:
        """
        Initializes a CircularBuffer instance.

        Parameters:
        -----------
        size : int
            The maximum number of elements the buffer can hold.
        """
        if size <= 0:
            raise ValueError("Capacity must be at least 1")
        self.capacity = size
        self.buffer: list[Any | None] = [None] * size
        self.index = 0
        self._count = 0

    def __repr__(self) -> str:
        """
        Returns a string representation of the CircularBuffer.

        Returns
        -------
        str:
            A string describing the buffer contents and state.
        """
        return (
            f"CircularBuffer(capacity={self.capacity}, "
            f"size={len(self)}, "
            f"buffer={self.get_all()})"
        )

    def append(self, value: Any) -> None:
        """
        Adds a value to the buffer. Overwrites the oldest element if the
        buffer is full.

        Parameters:
        -----------
        value : Any
            The value to add to the buffer.
        """
        self.buffer[self.index] = value
        self.index = (self.index + 1) % self.capacity
        if self._count < self.capacity:
            self._count += 1

    def get_all(self) -> list[Any | None]:
        """
        Retrieves all elements in the buffer in the correct order.

        Returns
        -------
        list[Any | None]:
            A list of elements in the buffer, ordered from the oldest to the
            newest.
        """
        if self.is_full():
            return self.buffer[self.index :] + self.buffer[: self.index]
        return self.buffer[: self.index]

    def get(self, index: int) -> Any | None:
        """Return item at index or None if out of bounds."""
        items = self.get_all()
        if 0 <= index < len(items):
            return items[index]
        return None

    def is_empty(self) -> bool:
        """
        Checks if the buffer is empty.

        Returns
        -------
        bool:
            True if the buffer is empty, False otherwise.
        """
        return self._count == 0

    def is_full(self) -> bool:
        """
        Checks if the buffer is full.

        Returns
        -------
        bool:
            True if the buffer is full, False otherwise.
        """
        return self._count >= self.capacity

    def clear(self) -> None:
        """Clear the buffer."""
        self.buffer = [None] * self.capacity
        self.index = 0
        self._count = 0

    def __len__(self) -> int:
        """Return number of elements currently stored."""
        return self._count

    def __iter__(self):
        """Iterate over items in logical order."""
        return iter(self.get_all())

    def __contains__(self, item: Any) -> bool:
        """Return True if item present in buffer."""
        return item in self.get_all()


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "CircularBuffer",
]


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    # Create a circular buffer with a size of 5
    buffer = CircularBuffer(size=5)

    # Append values and display the buffer contents
    buffer.append(1)
    buffer.append(2)
    print(buffer.get_all())  # Outputs: [1, 2]

    buffer.append(3)
    buffer.append(4)
    buffer.append(5)
    print(buffer.get_all())  # Outputs: [1, 2, 3, 4, 5]

    # Overwrite the oldest values
    buffer.append(6)
    buffer.append(7)
    print(buffer.get_all())  # Outputs: [6, 7, 3, 4, 5]

    # Check buffer state
    print("Is buffer full?", buffer.is_full())  # Outputs: True
    print("Is buffer empty?", buffer.is_empty())  # Outputs: False
