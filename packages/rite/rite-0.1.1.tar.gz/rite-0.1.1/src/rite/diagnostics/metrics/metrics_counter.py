# =============================================================================
# Docstring
# =============================================================================

"""
Counter Metric
==============

Counter that can only increase.

Examples
--------
>>> from rite.diagnostics.metrics import metrics_counter
>>> counter = metrics_counter("requests")
>>> counter.increment()
>>> counter.value
1

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Classes
# =============================================================================


class metrics_counter:
    """
    Counter metric that only increases.

    Attributes:
        name: Metric name.
        value: Current counter value.

    Examples:
        >>> counter = metrics_counter("api_calls")
        >>> counter.increment()
        >>> counter.increment(5)
        >>> counter.value
        6
    """

    def __init__(self, name: str) -> None:
        """
        Initialize counter.

        Args:
            name: Metric name.
        """
        self.name = name
        self._value: float = 0.0

    @property
    def value(self) -> float:
        """Get current value."""
        return self._value

    def increment(self, amount: float = 1.0) -> None:
        """
        Increment counter.

        Args:
            amount: Amount to add (must be non-negative).

        Raises:
            ValueError: If amount is negative.

        Examples:
            >>> counter = metrics_counter("requests")
            >>> counter.increment()
            >>> counter.increment(10)
            >>> counter.value
            11.0
        """
        if amount < 0:
            raise ValueError("Counter can only increase")
        self._value += amount

    def reset(self) -> None:
        """Reset counter to zero."""
        self._value = 0.0

    def __repr__(self) -> str:
        """Return string representation."""
        return f"{self.name}={self._value}"


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["metrics_counter"]
