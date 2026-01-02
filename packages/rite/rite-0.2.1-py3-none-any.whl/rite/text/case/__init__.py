# =============================================================================
# Docstring
# =============================================================================

"""
Case Conversion Module
=======================

Functions for converting text between different case formats.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .to_camel_case import to_camel_case
from .to_constant_case import to_constant_case
from .to_dot_case import to_dot_case
from .to_kebab_case import to_kebab_case
from .to_lower_case import to_lower_case
from .to_pascal_case import to_pascal_case
from .to_path_case import to_path_case
from .to_sentence_case import to_sentence_case
from .to_snake_case import to_snake_case
from .to_title_case import to_title_case
from .to_upper_case import to_upper_case

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "to_snake_case",
    "to_camel_case",
    "to_pascal_case",
    "to_kebab_case",
    "to_constant_case",
    "to_dot_case",
    "to_path_case",
    "to_title_case",
    "to_sentence_case",
    "to_lower_case",
    "to_upper_case",
]
