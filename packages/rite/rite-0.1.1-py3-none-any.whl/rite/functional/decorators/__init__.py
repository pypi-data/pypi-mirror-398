# =============================================================================
# Docstring
# =============================================================================

"""
Decorators Module
=================

Function decorators for control flow and behavior.

This submodule provides decorators for debouncing, throttling,
one-time execution, and deprecation warnings.

Examples
--------
>>> from rite.functional.decorators import (
...     decorators_debounce,
...     decorators_throttle,
...     decorators_once
... )
>>> @decorators_once()
... def initialize():
...     return "ready"

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .decorators_debounce import decorators_debounce
from .decorators_deprecated import decorators_deprecated
from .decorators_once import decorators_once
from .decorators_throttle import decorators_throttle

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "decorators_debounce",
    "decorators_throttle",
    "decorators_once",
    "decorators_deprecated",
]
