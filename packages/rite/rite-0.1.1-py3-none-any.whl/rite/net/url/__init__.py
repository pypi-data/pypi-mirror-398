# =============================================================================
# Docstring
# =============================================================================

"""
URL Module
==========

URL parsing and manipulation utilities.

This submodule provides utilities for parsing, building, encoding,
and decoding URLs.

Examples
--------
>>> from rite.net.url import (
...     url_parse,
...     url_encode,
...     url_decode
... )
>>> url_encode("hello world")
'hello%20world'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .url_build import url_build
from .url_decode import url_decode
from .url_encode import url_encode
from .url_parse import url_parse
from .url_parse_query import url_parse_query

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "url_parse",
    "url_build",
    "url_encode",
    "url_decode",
    "url_parse_query",
]
