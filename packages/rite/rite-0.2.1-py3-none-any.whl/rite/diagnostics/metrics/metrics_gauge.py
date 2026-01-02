# =============================================================================
# Docstring
# =============================================================================

"""
Gauge Metric
============

Gauge that can increase or decrease.

Examples
--------
>>> from rite.diagnostics.metrics import metrics_gauge
>>> gauge = metrics_gauge("temperature")
>>> gauge.set(25.0)
>>> gauge.value
25.0

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# =============================================================================
# Classes
# =============================================================================


class metrics_gauge:
    """
    Gauge metric that can go up or down.

    Attributes:
        name: Metric name.
        value: Current gauge value.

    Examples:
        >>> gauge = metrics_gauge("memory_usage")
        >>> gauge.set(100)
        >>> gauge.increment(50)
        >>> gauge.decrement(25)
        >>> gauge.value
        125.0
    """

    def __init__(self, name: str, initial_value: float = 0.0) -> None:
        """
        Initialize gauge.

        Args:
            name: Metric name.
            initial_value: Starting value.
        """
        self.name = name
        self._value: float = initial_value

    @property
    def value(self) -> float:
        """Get current value."""
        return self._value

    def set(self, value: float) -> None:
        """
        Set gauge to specific value.

        Args:
            value: New value.

        Examples:
            >>> gauge = metrics_gauge("cpu")
            >>> gauge.set(75.5)
            >>> gauge.value
            75.5
        """
        self._value = value

    def increment(self, amount: float = 1.0) -> None:
        """
        Increase gauge value.

        Args:
            amount: Amount to add.
        """
        self._value += amount

    def decrement(self, amount: float = 1.0) -> None:
        """
        Decrease gauge value.

        Args:
            amount: Amount to subtract.
        """
        self._value -= amount

    def reset(self) -> None:
        """Reset gauge to zero."""
        self._value = 0.0

    def __repr__(self) -> str:
        """Return string representation."""
        return f"{self.name}={self._value}"


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["metrics_gauge"]
