# =============================================================================
# Docstring
# =============================================================================

"""
Cryptography Module
===================

Comprehensive cryptographic operations for hashing, encryption,
random generation, and UUIDs.

This module provides four main categories:

1. **Hashing** (hash submodule)
   - MD5, SHA-1, SHA-2 (256, 384, 512)
   - SHA-3 (256, 512)
   - BLAKE2b, BLAKE2s
   - HMAC message authentication

2. **Ciphers** (cipher submodule)
   - Classical ciphers: Caesar, Vigenère, Atbash, ROT13
   - Transposition ciphers: Rail Fence, Scytale
   - Substitution ciphers: Playfair, Four Square, Baconian
   - Modern: XOR, Autokey

3. **Random** (random submodule)
   - Cryptographically secure random bytes, hex, strings
   - Random integers and choices

4. **UUID** (uuid submodule)
   - UUID generation and validation
   - UUID version detection

Examples
--------
>>> from rite.crypto import hash_sha256, random_hex
>>> hash_sha256("hello")[:16]
'2cf24dba5fb0a30e'
>>> len(random_hex(16))
32

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
# Import | Local Modules - Ciphers
from .cipher import (
    decode_atbash_cipher,
    decode_autokey_cipher,
    decode_baconian_cipher,
    decode_caesar_cipher,
    decode_four_square_cipher,
    decode_playfair_cipher,
    decode_rail_fence_cipher,
    decode_rot13_cipher,
    decode_scytale_cipher,
    decode_transposition_cipher,
    decode_vigenere_cipher,
    decode_xor_cipher,
    encode_atbash_cipher,
    encode_autokey_cipher,
    encode_baconian_cipher,
    encode_caesar_cipher,
    encode_four_square_cipher,
    encode_playfair_cipher,
    encode_rail_fence_cipher,
    encode_rot13_cipher,
    encode_scytale_cipher,
    encode_transposition_cipher,
    encode_vigenere_cipher,
    encode_xor_cipher,
    four_square_cipher_pair,
)

# Import | Local Modules - Hashing
from .hash import (
    hash_blake2b,
    hash_blake2s,
    hash_md5,
    hash_sha1,
    hash_sha3_256,
    hash_sha3_512,
    hash_sha256,
    hash_sha256_hmac,
    hash_sha384,
    hash_sha512,
    hash_sha512_hmac,
)

# Import | Local Modules - Random
from .random import (
    random_bytes,
    random_choice,
    random_hex,
    random_int,
    random_urlsafe,
)

# Import | Local Modules - UUID
from .uuid import (
    is_valid_uuid,
    uuid_from_name,
    uuid_get_version,
    uuid_hex,
    uuid_is_random,
    uuid_random,
    uuid_string,
)

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    # Hashing - MD5
    "hash_md5",
    # Hashing - SHA-1
    "hash_sha1",
    # Hashing - SHA-2
    "hash_sha256",
    "hash_sha256_hmac",
    "hash_sha384",
    "hash_sha512",
    "hash_sha512_hmac",
    # Hashing - SHA-3
    "hash_sha3_256",
    "hash_sha3_512",
    # Hashing - BLAKE2
    "hash_blake2b",
    "hash_blake2s",
    # Random
    "random_bytes",
    "random_hex",
    "random_urlsafe",
    "random_int",
    "random_choice",
    # UUID
    "uuid_random",
    "uuid_hex",
    "uuid_string",
    "uuid_from_name",
    "uuid_get_version",
    "uuid_is_random",
    "is_valid_uuid",
    # Ciphers - Atbash
    "decode_atbash_cipher",
    "encode_atbash_cipher",
    # Ciphers - Autokey
    "decode_autokey_cipher",
    "encode_autokey_cipher",
    # Ciphers - Baconian
    "decode_baconian_cipher",
    "encode_baconian_cipher",
    # Ciphers - Caesar
    "decode_caesar_cipher",
    "encode_caesar_cipher",
    # Ciphers - Four Square
    "decode_four_square_cipher",
    "encode_four_square_cipher",
    "four_square_cipher_pair",
    # Ciphers - Playfair
    "decode_playfair_cipher",
    "encode_playfair_cipher",
    # Ciphers - Rail Fence
    "decode_rail_fence_cipher",
    "encode_rail_fence_cipher",
    # Ciphers - ROT13
    "decode_rot13_cipher",
    "encode_rot13_cipher",
    # Ciphers - Scytale
    "decode_scytale_cipher",
    "encode_scytale_cipher",
    # Ciphers - Transposition
    "decode_transposition_cipher",
    "encode_transposition_cipher",
    # Ciphers - Vigenère
    "decode_vigenere_cipher",
    "encode_vigenere_cipher",
    # Ciphers - XOR
    "decode_xor_cipher",
    "encode_xor_cipher",
]
