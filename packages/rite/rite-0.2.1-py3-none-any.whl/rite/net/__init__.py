# =============================================================================
# Docstring
# =============================================================================

"""
Network Module
==============

Comprehensive networking utilities for HTTP, URLs, requests,
validation, and MIME types.

This module provides utilities organized into semantic submodules:
- http: HTTP utilities (status codes, methods, headers)
- url: URL manipulation (parse, build, encode/decode)
- request: HTTP requests (GET, POST)
- validation: Network validation (email, URL, IP, port)
- mime: MIME type utilities (guess type, parse)

Examples
--------
>>> from rite.net import http_status_code, url_parse
>>> http_status_code(200)
'OK'
>>> result = url_parse("https://example.com/path")
>>> result.scheme
'https'

Legacy Classes
--------------
>>> from rite.net import BaseHTTPServer, SQLiteServer
>>> server = BaseHTTPServer(port=8000)

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
# Import | HTTP Utilities
from .http import (
    http_is_method,
    http_parse_headers,
    http_status_code,
    VALID_HTTP_METHODS,
)

# Import | MIME Utilities
from .mime import (
    mime_guess_extension,
    mime_guess_type,
    mime_parse,
)

# Import | Request Utilities
from .request import request_get, request_post

# Import | Servers (Legacy)
from .servers.server_http import BaseHTTPServer
from .servers.server_sqlite import SQLiteServer

# Import | URL Utilities
from .url import (
    url_build,
    url_decode,
    url_encode,
    url_parse,
    url_parse_query,
)

# Import | Validation Utilities
from .validation import (
    validation_is_email,
    validation_is_ipv4,
    validation_is_port,
    validation_is_url,
)

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    # Legacy Classes
    "BaseHTTPServer",
    "SQLiteServer",
    # HTTP Utilities
    "http_status_code",
    "http_is_method",
    "http_parse_headers",
    "VALID_HTTP_METHODS",
    # URL Utilities
    "url_parse",
    "url_build",
    "url_encode",
    "url_decode",
    "url_parse_query",
    # Request Utilities
    "request_get",
    "request_post",
    # Validation Utilities
    "validation_is_url",
    "validation_is_email",
    "validation_is_ipv4",
    "validation_is_port",
    # MIME Utilities
    "mime_guess_type",
    "mime_guess_extension",
    "mime_parse",
]
