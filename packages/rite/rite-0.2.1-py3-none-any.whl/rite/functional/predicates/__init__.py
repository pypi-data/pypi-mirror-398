# =============================================================================
# Docstring
# =============================================================================

"""
Predicates Module
=================

Predicate and utility functions.

This submodule provides basic predicates and utility functions
for functional programming patterns.

Examples
--------
>>> from rite.functional.predicates import (
...     predicates_identity,
...     predicates_constant,
...     predicates_negate
... )
>>> predicates_identity(42)
42

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .predicates_constant import predicates_constant
from .predicates_identity import predicates_identity
from .predicates_negate import predicates_negate

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "predicates_identity",
    "predicates_constant",
    "predicates_negate",
]
