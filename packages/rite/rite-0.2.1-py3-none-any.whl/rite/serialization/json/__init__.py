# =============================================================================
# Docstring
# =============================================================================

"""
JSON Module
===========

JSON serialization utilities.

This submodule provides utilities for JSON operations like
loading, dumping, parsing, and validation.

Examples
--------
>>> from rite.serialization.json import json_load, json_dump
>>> data = json_load("input.json")
>>> json_dump("output.json", data)

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .json_dump import json_dump
from .json_dumps import json_dumps
from .json_load import json_load
from .json_loads import json_loads
from .json_validate import json_validate

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "json_load",
    "json_dump",
    "json_loads",
    "json_dumps",
    "json_validate",
]
