# =============================================================================
# Docstring
# =============================================================================

"""
CSV Module
==========

CSV file operations.

This submodule provides utilities for reading and writing CSV files
with automatic delimiter detection.

Examples
--------
>>> from rite.serialization.csv import csv_read, csv_write
>>> data = csv_read("input.csv")
>>> csv_write("output.csv", data)

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .csv_detect_delimiter import csv_detect_delimiter
from .csv_read import csv_read
from .csv_write import csv_write

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "csv_read",
    "csv_write",
    "csv_detect_delimiter",
]
