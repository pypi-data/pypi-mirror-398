# =============================================================================
# Docstring
# =============================================================================

"""
Histogram Metric
================

Histogram to track distribution of values.

Examples
--------
>>> from rite.diagnostics.metrics import metrics_histogram
>>> hist = metrics_histogram("response_time")
>>> hist.observe(0.5)
>>> hist.count
1

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import statistics

# =============================================================================
# Classes
# =============================================================================


class metrics_histogram:
    """
    Histogram metric for value distributions.

    Attributes:
        name: Metric name.
        count: Number of observations.
        sum: Sum of all values.

    Examples:
        >>> hist = metrics_histogram("latency")
        >>> hist.observe(1.0)
        >>> hist.observe(2.0)
        >>> hist.observe(3.0)
        >>> hist.mean
        2.0
    """

    def __init__(self, name: str) -> None:
        """
        Initialize histogram.

        Args:
            name: Metric name.
        """
        self.name = name
        self._values: list[float] = []

    @property
    def count(self) -> int:
        """Get number of observations."""
        return len(self._values)

    @property
    def sum(self) -> float:
        """Get sum of all values."""
        return sum(self._values)

    @property
    def mean(self) -> float:
        """Get mean of values."""
        if not self._values:
            return 0.0
        return statistics.mean(self._values)

    @property
    def median(self) -> float:
        """Get median of values."""
        if not self._values:
            return 0.0
        return statistics.median(self._values)

    def observe(self, value: float) -> None:
        """
        Record observation.

        Args:
            value: Value to observe.

        Examples:
            >>> hist = metrics_histogram("size")
            >>> hist.observe(100)
            >>> hist.observe(200)
            >>> hist.count
            2
        """
        self._values.append(value)

    def percentile(self, p: float) -> float:
        """
        Calculate percentile.

        Args:
            p: Percentile (0-100).

        Returns:
            Value at percentile.

        Examples:
            >>> hist = metrics_histogram("values")
            >>> for i in range(100):
            ...     hist.observe(i)
            >>> hist.percentile(50)  # doctest: +SKIP
            49.5
        """
        if not self._values:
            return 0.0
        return statistics.quantiles(self._values, n=100)[int(p) - 1]

    def reset(self) -> None:
        """Clear all observations."""
        self._values.clear()

    def __repr__(self) -> str:
        """Return string representation."""
        return f"{self.name}: count={self.count}, " f"mean={self.mean:.2f}"


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["metrics_histogram"]
