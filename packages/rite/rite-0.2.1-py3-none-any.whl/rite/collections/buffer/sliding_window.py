# =============================================================================
# Docstring
# =============================================================================

"""
Sliding Window
==============

A sliding window data structure for stream processing and moving calculations.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections import deque
from collections.abc import Callable
from typing import Any

# =============================================================================
# Classes
# =============================================================================


class SlidingWindow:
    """
    SlidingWindow Class
    ===================

    A fixed-size window that slides over a data stream, useful for moving
    averages, rolling calculations, and stream processing.

    Parameters
    ----------
    size : int
        The size of the sliding window.
    aggregation_func : Callable | None
        Optional function to apply to window contents.

    """

    def __init__(
        self,
        size: int,
        aggregation_func: Callable[[list[Any]], Any] | None = None,
    ) -> None:
        """
        Initialize the sliding window.

        Args:
        ----
            size: Window size (number of elements).
            aggregation_func: Optional function to aggregate window data.

        """
        if size < 1:
            raise ValueError("Size must be at least 1")

        self.size = size
        self.aggregation_func = aggregation_func
        self._window: deque[Any] = deque(maxlen=size)

    def add(self, value: Any) -> Any | None:
        """
        Add a value to the window and return aggregated result.

        Args:
        ----
            value: The value to add to the window.

        Returns:
        -------
            Any | None: Aggregated result if aggregation_func is set.

        """
        self._window.append(value)

        if self.aggregation_func and self.is_full():
            return self.aggregation_func(list(self._window))
        return None

    def get_window(self) -> list[Any]:
        """
        Get current window contents.

        Returns:
        -------
            list[Any]: Current window values in order.

        """
        return list(self._window)

    def get_aggregate(self) -> Any | None:
        """
        Get aggregated value of current window.

        Returns:
        -------
            Any | None: Aggregated result or None if no aggregation function.

        """
        if self.aggregation_func and len(self._window) > 0:
            return self.aggregation_func(list(self._window))
        return None

    def is_full(self) -> bool:
        """
        Check if window is full.

        Returns:
        -------
            bool: True if window has reached its size.

        """
        return len(self._window) >= self.size

    def is_empty(self) -> bool:
        """
        Check if window is empty.

        Returns:
        -------
            bool: True if window contains no elements.

        """
        return len(self._window) == 0

    def clear(self) -> None:
        """Clear all elements from window."""
        self._window.clear()

    def moving_average(self) -> float | None:
        """
        Calculate moving average of numeric window.

        Returns:
        -------
            float | None: Average of window values or None if empty.

        """
        if not self._window:
            return None
        return sum(self._window) / len(self._window)

    def moving_sum(self) -> float | None:
        """
        Calculate moving sum of numeric window.

        Returns:
        -------
            float | None: Sum of window values or None if empty.

        """
        if not self._window:
            return None
        return sum(self._window)

    def moving_max(self) -> Any | None:
        """
        Get maximum value in window.

        Returns:
        -------
            Any | None: Maximum value or None if empty.

        """
        return max(self._window) if self._window else None

    def moving_min(self) -> Any | None:
        """
        Get minimum value in window.

        Returns:
        -------
            Any | None: Minimum value or None if empty.

        """
        return min(self._window) if self._window else None

    def __iter__(self):
        """Iterate over current window contents."""
        return iter(self._window)

    def __len__(self) -> int:
        """Return current number of elements in window."""
        return len(self._window)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"SlidingWindow(size={self.size}, current={len(self._window)})"


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "SlidingWindow",
]
