# =============================================================================
# Docstring
# =============================================================================

"""
Pickle Module
=============

Pickle serialization operations.

This submodule provides utilities for serializing and deserializing
Python objects using the pickle protocol.

Examples
--------
>>> from rite.serialization.pickle import pickle_dump, pickle_load
>>> pickle_dump("data.pkl", {"key": "value"})
>>> data = pickle_load("data.pkl")

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .pickle_dump import pickle_dump
from .pickle_dumps import pickle_dumps
from .pickle_load import pickle_load
from .pickle_loads import pickle_loads

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "pickle_dump",
    "pickle_load",
    "pickle_dumps",
    "pickle_loads",
]
