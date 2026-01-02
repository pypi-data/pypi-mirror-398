# =============================================================================
# Docstring
# =============================================================================

"""
Duration Module
===============

Time duration operations.

This submodule provides utilities for creating and manipulating
time durations using timedelta objects.

Examples
--------
>>> from rite.temporal.duration import duration_from_hours
>>> from rite.temporal.duration import duration_to_seconds
>>> dur = duration_from_hours(2)
>>> duration_to_seconds(dur)
7200.0

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .duration_from_days import duration_from_days
from .duration_from_hours import duration_from_hours
from .duration_from_minutes import duration_from_minutes
from .duration_from_seconds import duration_from_seconds
from .duration_to_seconds import duration_to_seconds

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "duration_from_seconds",
    "duration_from_minutes",
    "duration_from_hours",
    "duration_from_days",
    "duration_to_seconds",
]
