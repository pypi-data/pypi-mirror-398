# =============================================================================
# Docstring
# =============================================================================

"""
Identity Module
===============

This module provides unique identifier generation similar to
Python's uuid module.

Functions will include:
- UUID generation and utilities

Example:
    >>> from rite.identity import generate_uuid
    >>> generate_uuid()
    'a1b2c3d4-e5f6-...'

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .uuid_from_name import from_name as uuid_from_name
from .uuid_get_version import get_version as uuid_get_version
from .uuid_hex import uuid_hex
from .uuid_is_random import is_random_uuid as uuid_is_random
from .uuid_is_valid import is_valid_uuid
from .uuid_random import uuid_random
from .uuid_string import uuid_string

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "is_valid_uuid",
    "uuid_from_name",
    "uuid_get_version",
    "uuid_hex",
    "uuid_is_random",
    "uuid_random",
    "uuid_string",
]
