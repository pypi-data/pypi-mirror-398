# =============================================================================
# Docstring
# =============================================================================

"""
HTTP Module
===========

HTTP protocol utilities.

This submodule provides utilities for HTTP status codes, methods,
and header parsing.

Examples
--------
>>> from rite.net.http import (
...     http_status_code,
...     http_is_method
... )
>>> http_status_code(200)
'OK'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .http_is_method import http_is_method, VALID_HTTP_METHODS
from .http_parse_headers import http_parse_headers
from .http_status_code import http_status_code

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "http_status_code",
    "http_is_method",
    "http_parse_headers",
    "VALID_HTTP_METHODS",
]
