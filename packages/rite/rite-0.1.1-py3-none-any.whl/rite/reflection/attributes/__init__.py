# =============================================================================
# Docstring
# =============================================================================

"""
Attributes Module
=================

Attribute manipulation utilities.

This submodule provides utilities for working with object
attributes dynamically.

Examples
--------
>>> from rite.reflection.attributes import (
...     attributes_has_attr,
...     attributes_get_attr
... )
>>> attributes_has_attr("hello", "upper")
True
>>> attributes_get_attr("hello", "upper")
<built-in method upper of str object at 0x...>

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .attributes_del_attr import attributes_del_attr
from .attributes_get_attr import attributes_get_attr
from .attributes_has_attr import attributes_has_attr
from .attributes_set_attr import attributes_set_attr

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "attributes_has_attr",
    "attributes_get_attr",
    "attributes_set_attr",
    "attributes_del_attr",
]
