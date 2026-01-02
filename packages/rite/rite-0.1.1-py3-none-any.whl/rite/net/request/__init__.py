# =============================================================================
# Docstring
# =============================================================================

"""
Request Module
==============

HTTP request utilities.

This submodule provides utilities for making HTTP GET and POST
requests using standard library.

Examples
--------
>>> from rite.net.request import request_get
>>> response = request_get("http://example.com")  # doctest: +SKIP

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .request_get import request_get
from .request_post import request_post

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "request_get",
    "request_post",
]
