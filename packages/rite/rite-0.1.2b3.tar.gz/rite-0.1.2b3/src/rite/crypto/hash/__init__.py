# =============================================================================
# Docstring
# =============================================================================

"""
Hash Module
===========

Cryptographic hash functions and message authentication.

This submodule provides hash functions including MD5, SHA family,
BLAKE2, and SHA-3, as well as HMAC message authentication.

Examples
--------
>>> from rite.crypto.hash import hash_sha256, hash_blake2b
>>> hash_sha256("hello")[:16]
'2cf24dba5fb0a30e'
>>> len(hash_blake2b("data"))
128

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .hash_blake2b import hash_blake2b
from .hash_blake2s import hash_blake2s
from .hash_md5 import hash_md5
from .hash_sha1 import hash_sha1
from .hash_sha3_256 import hash_sha3_256
from .hash_sha3_512 import hash_sha3_512
from .hash_sha256 import hash_sha256, hash_sha256_hmac
from .hash_sha384 import hash_sha384
from .hash_sha512 import hash_sha512, hash_sha512_hmac

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    # MD5 (non-cryptographic)
    "hash_md5",
    # SHA-1 (deprecated)
    "hash_sha1",
    # SHA-2 family
    "hash_sha256",
    "hash_sha256_hmac",
    "hash_sha384",
    "hash_sha512",
    "hash_sha512_hmac",
    # SHA-3 family
    "hash_sha3_256",
    "hash_sha3_512",
    # BLAKE2
    "hash_blake2b",
    "hash_blake2s",
]
