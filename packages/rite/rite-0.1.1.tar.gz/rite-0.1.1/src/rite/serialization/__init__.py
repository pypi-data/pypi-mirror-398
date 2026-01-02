# =============================================================================
# Docstring
# =============================================================================

"""
Serialization Module
====================

Data serialization and deserialization utilities.

This module provides comprehensive utilities for working with various
data formats including JSON, CSV, INI, Pickle, and TOML using only
Python's standard library.

Submodules
----------
- json: JSON file and string operations
- csv: CSV file operations with delimiter detection
- ini: INI/config file operations
- pickle: Python object serialization
- toml: TOML file operations (Python 3.11+)

Examples
--------
>>> from rite.serialization import json_load, csv_read
>>> data = json_load("data.json")
>>> rows = csv_read("data.csv")

Notes
-----
Legacy classes JSONHandler, INIHandler, and detect_delimiter
are still available for backward compatibility.
"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .csv import csv_detect_delimiter, csv_read, csv_write
from .csv_utils import detect_delimiter
from .ini import ini_get, ini_read, ini_set, ini_write
from .ini_utils import INIHandler
from .json import (
    json_dump,
    json_dumps,
    json_load,
    json_loads,
    json_validate,
)
from .json_utils import JSONHandler
from .pickle import pickle_dump, pickle_dumps, pickle_load, pickle_loads
from .toml import toml_load, toml_loads

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    # JSON
    "json_load",
    "json_dump",
    "json_loads",
    "json_dumps",
    "json_validate",
    # CSV
    "csv_read",
    "csv_write",
    "csv_detect_delimiter",
    # INI
    "ini_read",
    "ini_write",
    "ini_get",
    "ini_set",
    # Pickle
    "pickle_dump",
    "pickle_load",
    "pickle_dumps",
    "pickle_loads",
    # TOML
    "toml_load",
    "toml_loads",
    # Legacy
    "JSONHandler",
    "INIHandler",
    "detect_delimiter",
]
