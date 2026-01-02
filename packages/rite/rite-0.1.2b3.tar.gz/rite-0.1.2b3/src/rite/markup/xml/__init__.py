# =============================================================================
# Docstring
# =============================================================================

"""
XML Module
==========

XML processing utilities.

This submodule provides utilities for escaping, unescaping,
and formatting XML content.

Examples
--------
>>> from rite.markup.xml import (
...     xml_escape,
...     xml_unescape
... )
>>> xml_escape("<tag>value</tag>")
'&lt;tag&gt;value&lt;/tag&gt;'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .xml_escape import xml_escape
from .xml_format import xml_format
from .xml_unescape import xml_unescape

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "xml_escape",
    "xml_unescape",
    "xml_format",
]
