# Import | Future
from __future__ import annotations

# Import | Local Modules
from .morse_decode import morse_decode
from .morse_encode import morse_encode

__all__: list[str] = ["morse_encode", "morse_decode"]
