# =============================================================================
# Docstring
# =============================================================================

"""
Format Conversion Utilities
============================

Encoding and decoding utilities for various formats.

This submodule provides utilities for converting data between different
formats: JSON, Base64, Hexadecimal, URL encoding, etc.

Examples
--------
>>> from rite.conversion.formats import (
...     formats_json_encode,
...     formats_base64_encode,
...     formats_hex_encode
... )
>>> formats_json_encode({"key": "value"})
'{"key": "value"}'
>>> formats_base64_encode(b"hello")
'aGVsbG8='
>>> formats_hex_encode(b"hello")
'68656c6c6f'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .formats_base64_decode import formats_base64_decode
from .formats_base64_encode import formats_base64_encode
from .formats_hex_decode import formats_hex_decode
from .formats_hex_encode import formats_hex_encode
from .formats_json_decode import formats_json_decode
from .formats_json_encode import formats_json_encode
from .formats_url_decode import formats_url_decode
from .formats_url_encode import formats_url_encode

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    # JSON
    "formats_json_encode",
    "formats_json_decode",
    # Base64
    "formats_base64_encode",
    "formats_base64_decode",
    # Hexadecimal
    "formats_hex_encode",
    "formats_hex_decode",
    # URL
    "formats_url_encode",
    "formats_url_decode",
]
