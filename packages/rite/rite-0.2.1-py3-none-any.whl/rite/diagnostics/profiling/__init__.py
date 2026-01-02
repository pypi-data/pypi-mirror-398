# =============================================================================
# Docstring
# =============================================================================

"""
Profiling Module
================

Performance profiling utilities.

This submodule provides utilities for measuring execution time,
memory usage, and function call counts.

Examples
--------
>>> from rite.diagnostics.profiling import (
...     profiling_timer,
...     profiling_stopwatch,
...     profiling_memory
... )
>>> @profiling_timer()
... def slow_function():
...     pass
>>> with profiling_stopwatch("task") as sw:
...     pass

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .profiling_count_calls import profiling_count_calls
from .profiling_memory import profiling_memory
from .profiling_stopwatch import profiling_stopwatch
from .profiling_timer import profiling_timer

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "profiling_timer",
    "profiling_stopwatch",
    "profiling_memory",
    "profiling_count_calls",
]
