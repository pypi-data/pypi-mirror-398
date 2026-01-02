# =============================================================================
# Docstring
# =============================================================================

"""
Random Module
=============

Cryptographically secure random generation.

This submodule provides secure random generation using Python's
secrets module for cryptographic purposes.

Examples
--------
>>> from rite.crypto.random import random_bytes, random_hex
>>> len(random_bytes(16))
16
>>> len(random_hex(16))
32

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .random_bytes import random_bytes
from .random_choice import random_choice
from .random_hex import random_hex
from .random_int import random_int
from .random_urlsafe import random_urlsafe

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "random_bytes",
    "random_hex",
    "random_urlsafe",
    "random_int",
    "random_choice",
]
