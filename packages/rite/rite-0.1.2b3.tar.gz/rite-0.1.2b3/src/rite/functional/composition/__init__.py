# =============================================================================
# Docstring
# =============================================================================

"""
Composition Module
==================

Function composition and piping utilities.

This submodule provides utilities for composing functions,
piping values through functions, and chainable operations.

Examples
--------
>>> from rite.functional.composition import (
...     composition_compose,
...     composition_pipe,
...     composition_chain
... )
>>> f = composition_pipe(lambda x: x + 1, lambda x: x * 2)
>>> f(3)
8

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .composition_chain import composition_chain
from .composition_compose import composition_compose
from .composition_pipe import composition_pipe

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "composition_compose",
    "composition_pipe",
    "composition_chain",
]
