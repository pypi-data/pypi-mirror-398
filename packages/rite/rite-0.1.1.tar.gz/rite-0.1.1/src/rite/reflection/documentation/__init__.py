# =============================================================================
# Docstring
# =============================================================================

"""
Documentation Module
====================

Documentation inspection utilities.

This submodule provides utilities for inspecting docstrings,
comments, and source file locations.

Examples
--------
>>> from rite.reflection.documentation import (
...     documentation_get_docstring
... )
>>> def func():
...     '''This is a docstring.'''
...     pass
>>> documentation_get_docstring(func)
'This is a docstring.'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .documentation_get_comments import documentation_get_comments
from .documentation_get_docstring import documentation_get_docstring
from .documentation_get_file import documentation_get_file

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "documentation_get_docstring",
    "documentation_get_comments",
    "documentation_get_file",
]
