# =============================================================================
# Docstring
# =============================================================================

"""
Statistics Module
=================

Statistical calculation utilities.

This submodule provides utilities for statistical operations like
mean, median, sum, min, and max.

Examples
--------
>>> from rite.numeric.statistics import (
...     statistics_mean,
...     statistics_median
... )
>>> statistics_mean([1, 2, 3, 4, 5])
3.0
>>> statistics_median([1, 2, 3, 4, 5])
3

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .statistics_mean import statistics_mean
from .statistics_median import statistics_median
from .statistics_min_max import statistics_max, statistics_min
from .statistics_sum import statistics_sum

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "statistics_mean",
    "statistics_median",
    "statistics_sum",
    "statistics_min",
    "statistics_max",
]
