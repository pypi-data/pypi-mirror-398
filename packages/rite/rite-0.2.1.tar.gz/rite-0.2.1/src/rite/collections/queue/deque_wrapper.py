# =============================================================================
# Docstring
# =============================================================================

"""
Deque Wrapper
=============

Enhanced deque wrapper with additional functionality.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections import deque
from typing import Any

# =============================================================================
# Classes
# =============================================================================


class DequeWrapper:
    """
    DequeWrapper Class
    ==================

    A wrapper around collections.deque with additional utilities.

    """

    def __init__(self, max_size: int | None = None) -> None:
        """
        Initialize a deque wrapper.

        Args:
        ----
            max_size: Maximum length of the deque.

        """
        self.max_size = max_size
        self._deque: deque[Any] = deque(maxlen=max_size)

    def push_left(self, item: Any) -> None:
        """Add item to the left end."""
        self._deque.appendleft(item)

    def push_right(self, item: Any) -> None:
        """Add item to the right end."""
        self._deque.append(item)

    def pop_left(self) -> Any:
        """Remove and return item from left end."""
        if not self._deque:
            return None
        return self._deque.popleft()

    def pop_right(self) -> Any:
        """Remove and return item from right end."""
        if not self._deque:
            return None
        return self._deque.pop()

    def peek_left(self) -> Any:
        """Return item at left end without removing."""
        if not self._deque:
            return None
        return self._deque[0]

    def peek_right(self) -> Any:
        """Return item at right end without removing."""
        if not self._deque:
            return None
        return self._deque[-1]

    def rotate(self, n: int = 1) -> None:
        """
        Rotate deque n steps to the right.

        Args:
        ----
            n: Number of steps to rotate (negative for left rotation).

        """
        self._deque.rotate(n)

    def clear(self) -> None:
        """Remove all items."""
        self._deque.clear()

    def is_empty(self) -> bool:
        """Check if deque is empty."""
        return len(self._deque) == 0

    def to_list(self) -> list[Any]:
        """Convert to list."""
        return list(self._deque)

    def __len__(self) -> int:
        """Return number of items."""
        return len(self._deque)

    def __iter__(self):
        """Iterate over items."""
        return iter(self._deque)

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"DequeWrapper(size={len(self._deque)}, "
            f"max_size={self.max_size})"
        )


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "DequeWrapper",
]
