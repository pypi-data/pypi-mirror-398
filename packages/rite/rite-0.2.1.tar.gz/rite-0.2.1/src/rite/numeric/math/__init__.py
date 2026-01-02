# =============================================================================
# Docstring
# =============================================================================

"""
Math Module
===========

Basic mathematical operations.

This submodule provides utilities for basic math operations like
clamping, absolute value, sign, and power.

Examples
--------
>>> from rite.numeric.math import math_clamp, math_sign
>>> math_clamp(5, 0, 10)
5
>>> math_sign(-5)
-1

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .math_abs import math_abs
from .math_clamp import math_clamp
from .math_pow import math_pow
from .math_sign import math_sign

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "math_clamp",
    "math_abs",
    "math_sign",
    "math_pow",
]
