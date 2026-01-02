# =============================================================================
# Docstring
# =============================================================================

"""
Validation Module
=================

Network validation utilities.

This submodule provides utilities for validating URLs, emails,
IP addresses, and port numbers.

Examples
--------
>>> from rite.net.validation import (
...     validation_is_url,
...     validation_is_email
... )
>>> validation_is_url("https://example.com")
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .validation_is_email import validation_is_email
from .validation_is_ipv4 import validation_is_ipv4
from .validation_is_port import validation_is_port
from .validation_is_url import validation_is_url

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "validation_is_url",
    "validation_is_email",
    "validation_is_ipv4",
    "validation_is_port",
]
