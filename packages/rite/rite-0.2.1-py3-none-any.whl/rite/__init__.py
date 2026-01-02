# =============================================================================
# Docstring
# =============================================================================

"""
Rite - Python Utility Library
==============================

A pure Python utility library with stdlib-mirroring module structure.

Modules:
    text: Text and string processing
    numeric: Numeric operations and conversions
    temporal: Time and date operations
    filesystem: File and path utilities
    collections: Data structures and utilities
    serialization: Data serialization formats
    conversion: Type conversions
    crypto: Cryptographic operations
    net: Network utilities
    markup: Markup language handling
    system: System-level operations
    diagnostics: Logging and error handling
    functional: Functional programming utilities
    reflection: Runtime introspection

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from . import (
    collections,
    conversion,
    crypto,
    diagnostics,
    filesystem,
    functional,
    markup,
    net,
    numeric,
    reflection,
    serialization,
    system,
    temporal,
    text,
)

# =============================================================================
# Information
# =============================================================================

__author__ = "Lars van Vianen"
__copyright__ = "Copyright 2022, Scape Agency"
__credits__ = [
    "Lars van Vianen",
]
__license__ = "MIT License"
__version__ = "0.1.2"
__maintainer__ = "Scape Agency"
__email__ = "info@scape.agency"
__status__ = "Alpha"


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "text",
    "numeric",
    "temporal",
    "filesystem",
    "collections",
    "serialization",
    "conversion",
    "crypto",
    "net",
    "markup",
    "system",
    "diagnostics",
    "functional",
    "reflection",
]
