# =============================================================================
# Docstring
# =============================================================================

"""
Storage Storage - Mimetype Utils Module
=======================================

This module groups functions related to MIME type (Multipurpose Internet Mail
Extensions) handling within the storage system. It provides utilities for
verifying the MIME type of files, which is crucial for validating file types,
ensuring compatibility, and enhancing security by preventing the processing
of unsupported or potentially malicious file formats.

Included Utilities:
- MIME Type Verification: Checks if a file's MIME type matches expected types,
  helping in enforcing content policies and security measures.

Future or Conditional Utilities:
- MIME Type Detection: (Commented out) Functionality for determining the
  MIME type of a file based on its content, which can be useful for content
  identification and handling.

These utilities assist in maintaining a robust and secure storage system by
ensuring that only files with appropriate MIME types are processed or stored.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Local Modules
from .mimetype_guess_from_path import mimetype_guess_from_path

# MIME Type Verification Functions
from .util_mimetype_verify import mimetype_verify

# MIME Type Detection Functions (Future or Conditional Use)
# from .util_mimetype_from_bytes import mimetype_from_bytes

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "mimetype_verify",
    "mimetype_guess_from_path",
    # "mimetype_from_bytes",
]
