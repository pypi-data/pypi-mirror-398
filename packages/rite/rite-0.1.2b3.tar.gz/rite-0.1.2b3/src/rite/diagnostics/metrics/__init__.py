# =============================================================================
# Docstring
# =============================================================================

"""
Metrics Module
==============

Performance and monitoring metrics.

This submodule provides metric classes for counters, gauges,
histograms, and timers.

Examples
--------
>>> from rite.diagnostics.metrics import (
...     metrics_counter,
...     metrics_gauge,
...     metrics_histogram,
...     metrics_timer
... )
>>> counter = metrics_counter("requests")
>>> counter.increment()

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .metrics_counter import metrics_counter
from .metrics_gauge import metrics_gauge
from .metrics_histogram import metrics_histogram
from .metrics_timer import metrics_timer

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "metrics_counter",
    "metrics_gauge",
    "metrics_histogram",
    "metrics_timer",
]
