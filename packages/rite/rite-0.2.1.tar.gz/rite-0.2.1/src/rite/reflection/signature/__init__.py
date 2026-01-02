# =============================================================================
# Docstring
# =============================================================================

"""
Signature Module
================

Function signature inspection utilities.

This submodule provides utilities for inspecting function
signatures, parameters, and return annotations.

Examples
--------
>>> from rite.reflection.signature import (
...     signature_get_signature,
...     signature_get_parameters
... )
>>> def func(a: int, b: str = "default") -> str:
...     return f"{a}{b}"
>>> sig = signature_get_signature(func)
>>> len(sig.parameters)
2

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .signature_get_parameters import signature_get_parameters
from .signature_get_return_annotation import (
    signature_get_return_annotation,
)
from .signature_get_signature import signature_get_signature

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "signature_get_signature",
    "signature_get_parameters",
    "signature_get_return_annotation",
]
