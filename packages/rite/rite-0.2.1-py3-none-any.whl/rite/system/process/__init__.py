# =============================================================================
# Docstring
# =============================================================================

"""
Process Module
==============

Process and subprocess management.

This submodule provides utilities for executing system commands
and managing subprocess operations.

Examples
--------
>>> from rite.system.process import process_run
>>> code, out, err = process_run(["ls"], Path.cwd())

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .process_call import process_call
from .process_check_output import process_check_output
from .process_run import process_run

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "process_run",
    "process_check_output",
    "process_call",
]
