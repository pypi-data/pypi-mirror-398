# =============================================================================
# Docstring
# =============================================================================

"""
Reflection Module
=================

Comprehensive runtime introspection utilities.

This module provides utilities organized into semantic submodules:
- importing: Dynamic imports (load_class, load_module, load_function)
- inspection: Object inspection (get_members, get_methods, get_source)
- attributes: Attribute manipulation (has_attr, get_attr, set_attr)
- types: Type checking (is_class, is_function, is_method)
- signature: Signature inspection (get_signature, get_parameters)
- documentation: Documentation access (get_docstring, get_file)

Examples
--------
>>> from rite.reflection import (
...     importing_load_class,
...     inspection_get_members
... )
>>> OrderedDict = importing_load_class("collections.OrderedDict")
>>> import json
>>> members = inspection_get_members(json)
>>> len(members) > 0
True

Legacy Functions
----------------
>>> from rite.reflection import load_class
>>> MyClass = load_class("collections.OrderedDict")

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
# Import | Attributes Utilities
from .attributes import (
    attributes_del_attr,
    attributes_get_attr,
    attributes_has_attr,
    attributes_set_attr,
)

# Import | Documentation Utilities
from .documentation import (
    documentation_get_comments,
    documentation_get_docstring,
    documentation_get_file,
)

# Import | Importing Utilities
from .importing import (
    ClassImportError,
    importing_load_class,
    importing_load_function,
    importing_load_module,
)

# Import | Inspection Utilities
from .inspection import (
    inspection_get_functions,
    inspection_get_members,
    inspection_get_methods,
    inspection_get_source,
)

# Import | Signature Utilities
from .signature import (
    signature_get_parameters,
    signature_get_return_annotation,
    signature_get_signature,
)

# Import | Types Utilities
from .types import (
    types_is_class,
    types_is_function,
    types_is_method,
    types_is_module,
)

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    # Legacy
    "ClassImportError",
    # Importing Utilities
    "importing_load_class",
    "importing_load_module",
    "importing_load_function",
    # Inspection Utilities
    "inspection_get_members",
    "inspection_get_methods",
    "inspection_get_functions",
    "inspection_get_source",
    # Attributes Utilities
    "attributes_has_attr",
    "attributes_get_attr",
    "attributes_set_attr",
    "attributes_del_attr",
    # Types Utilities
    "types_is_class",
    "types_is_function",
    "types_is_method",
    "types_is_module",
    # Signature Utilities
    "signature_get_signature",
    "signature_get_parameters",
    "signature_get_return_annotation",
    # Documentation Utilities
    "documentation_get_docstring",
    "documentation_get_comments",
    "documentation_get_file",
]
