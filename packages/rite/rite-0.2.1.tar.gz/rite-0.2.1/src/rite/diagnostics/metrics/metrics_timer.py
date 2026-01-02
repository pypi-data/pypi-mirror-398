# =============================================================================
# Docstring
# =============================================================================

"""
Timer Metric
============

Timer to measure durations as context manager.

Examples
--------
>>> from rite.diagnostics.metrics import metrics_timer
>>> timer = metrics_timer("operation")
>>> with timer:
...     pass
>>> timer.count
1

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import time

# =============================================================================
# Classes
# =============================================================================


class metrics_timer:
    """
    Timer metric using context manager.

    Attributes:
        name: Metric name.
        count: Number of timing measurements.
        total: Total time measured.

    Examples:
        >>> timer = metrics_timer("request")
        >>> with timer:
        ...     time.sleep(0.01)
        >>> timer.count
        1
        >>> timer.total > 0
        True
    """

    def __init__(self, name: str) -> None:
        """
        Initialize timer.

        Args:
            name: Metric name.
        """
        self.name = name
        self._count: int = 0
        self._total: float = 0.0
        self._start: float = 0.0

    @property
    def count(self) -> int:
        """Get number of measurements."""
        return self._count

    @property
    def total(self) -> float:
        """Get total time in seconds."""
        return self._total

    @property
    def average(self) -> float:
        """Get average time per measurement."""
        if self._count == 0:
            return 0.0
        return self._total / self._count

    def __enter__(self) -> metrics_timer:
        """Start timing."""
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: object) -> None:
        """Stop timing and record."""
        elapsed = time.perf_counter() - self._start
        self._total += elapsed
        self._count += 1

    def reset(self) -> None:
        """Reset timer statistics."""
        self._count = 0
        self._total = 0.0

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"{self.name}: count={self._count}, "
            f"total={self._total:.4f}s, avg={self.average:.4f}s"
        )


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["metrics_timer"]
