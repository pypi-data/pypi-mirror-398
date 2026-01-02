# =============================================================================
# Docstring
# =============================================================================

"""
Diagnostics Module
==================

Comprehensive diagnostics and monitoring utilities.

This module provides utilities for logging, error handling, profiling,
debugging, and metrics collection.

Submodules
----------
- logging: Structured logging, file/console output, contextual logging
- errors: Exception handling, retry logic, traceback formatting
- profiling: Timing, memory profiling, call counting
- debugging: Object inspection, function tracing, state dumping
- metrics: Counters, gauges, histograms, timers

Examples
--------
Logging:
    >>> from rite.diagnostics import logging_structured
    >>> logging_structured("INFO", "Application started", user="admin")

Error Handling:
    >>> from rite.diagnostics import errors_retry
    >>> @errors_retry(max_attempts=3)
    ... def api_call():
    ...     pass

Profiling:
    >>> from rite.diagnostics import profiling_timer
    >>> @profiling_timer()
    ... def slow_function():
    ...     pass

Debugging:
    >>> from rite.diagnostics import debugging_trace
    >>> @debugging_trace()
    ... def calculate(x, y):
    ...     return x + y

Metrics:
    >>> from rite.diagnostics import metrics_counter
    >>> counter = metrics_counter("requests")
    >>> counter.increment()

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .debugging import (
    debugging_dump,
    debugging_inspect,
    debugging_locals,
    debugging_trace,
)
from .error_handler import ErrorHandler
from .errors import (
    errors_catch,
    errors_format_traceback,
    errors_get_chain,
    errors_retry,
)
from .logger import Logger
from .logging import (
    logging_structured,
    logging_to_console,
    logging_to_file,
    logging_with_context,
)
from .metrics import (
    metrics_counter,
    metrics_gauge,
    metrics_histogram,
    metrics_timer,
)
from .profiling import (
    profiling_count_calls,
    profiling_memory,
    profiling_stopwatch,
    profiling_timer,
)

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    # Legacy classes
    "Logger",
    "ErrorHandler",
    # Logging utilities
    "logging_structured",
    "logging_to_file",
    "logging_to_console",
    "logging_with_context",
    # Error handling utilities
    "errors_retry",
    "errors_catch",
    "errors_format_traceback",
    "errors_get_chain",
    # Profiling utilities
    "profiling_timer",
    "profiling_stopwatch",
    "profiling_memory",
    "profiling_count_calls",
    # Debugging utilities
    "debugging_inspect",
    "debugging_trace",
    "debugging_dump",
    "debugging_locals",
    # Metrics
    "metrics_counter",
    "metrics_gauge",
    "metrics_histogram",
    "metrics_timer",
]
