# =============================================================================
# Docstring
# =============================================================================

"""
Debugging Module
================

Debugging and inspection utilities.

This submodule provides utilities for inspecting objects,
tracing function calls, and dumping variable states.

Examples
--------
>>> from rite.diagnostics.debugging import (
...     debugging_inspect,
...     debugging_trace,
...     debugging_dump
... )
>>> @debugging_trace()
... def example():
...     pass

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .debugging_dump import debugging_dump
from .debugging_inspect import debugging_inspect
from .debugging_locals import debugging_locals
from .debugging_trace import debugging_trace

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "debugging_inspect",
    "debugging_trace",
    "debugging_dump",
    "debugging_locals",
]
