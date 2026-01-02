# =============================================================================
# Docstring
# =============================================================================

"""
Mimetype Match Utility Module
===============================================

Simple helpers to match MIME types against wildcard or exact patterns.

"""


def mimetype_match(mime: str, pattern: str) -> bool:
    """
    Return True if a MIME type matches a pattern.

    Supports:
    - exact match: "image/png" == "image/png"
    - wildcard match: "image/*" matches "image/png", "image/jpeg", etc.
    """
    if not mime or not pattern:
        return False

    mime = str(mime).strip().lower()
    pattern = str(pattern).strip().lower()

    if pattern == mime:
        return True

    if pattern.endswith("/*"):
        return mime.split("/", 1)[0] == pattern[:-2]

    return False


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "mimetype_match",
]
