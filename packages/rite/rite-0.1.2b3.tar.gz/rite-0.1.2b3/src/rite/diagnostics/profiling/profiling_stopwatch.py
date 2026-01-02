# =============================================================================
# Docstring
# =============================================================================

"""
Timer Context Manager
=====================

Context manager to measure elapsed time.

Examples
--------
>>> from rite.diagnostics.profiling import profiling_stopwatch
>>> with profiling_stopwatch("operation") as sw:
...     time.sleep(0.1)
>>> print(sw.elapsed)

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


class profiling_stopwatch:
    """
    Context manager to measure elapsed time.

    Attributes:
        name: Operation name.
        elapsed: Elapsed time in seconds.
        start_time: Start timestamp.
        end_time: End timestamp.

    Examples:
        >>> with profiling_stopwatch("task") as sw:
        ...     time.sleep(0.1)
        >>> sw.elapsed > 0.1
        True
    """

    def __init__(self, name: str = "operation") -> None:
        """
        Initialize stopwatch.

        Args:
            name: Operation name for display.
        """
        self.name = name
        self.elapsed: float = 0.0
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    def __enter__(self) -> profiling_stopwatch:
        """Start timing."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args: object) -> None:
        """Stop timing and calculate elapsed time."""
        self.end_time = time.perf_counter()
        self.elapsed = self.end_time - self.start_time

    def __str__(self) -> str:
        """Return formatted string."""
        return f"{self.name}: {self.elapsed:.6f} seconds"


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["profiling_stopwatch"]
