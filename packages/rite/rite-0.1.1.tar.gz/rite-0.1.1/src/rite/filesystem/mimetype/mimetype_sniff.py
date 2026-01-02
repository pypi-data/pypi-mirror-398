# =============================================================================
# Docstring
# =============================================================================

"""
Mimetype Sniff Utility Module
===============================================

Best-effort magic-number based MIME type detection.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library

BytesLike = bytes | bytearray | memoryview


def mimetype_sniff(
    buf: BytesLike,
    *,
    max_probe: int = 512,
) -> str | None:
    """
    Best-effort MIME sniffing from magic numbers.
    Returns None if no known signature is found.

    Only inspects the first `max_probe` bytes (default 512).
    Supports common formats: PNG, JPEG, GIF, WebP, PDF, ZIP, GZIP,
    MP3/ID3, MP4 (ftyp brands), WAV, Ogg/Opus/Vorbis, FLAC, AVIF/HEIF.
    """
    if not buf:
        return None

    mv = memoryview(buf)[:max_probe]

    # ---- Fixed prefixes (fast-path) ----
    if mv[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if mv[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if mv[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if mv[:5] == b"%PDF-":
        return "application/pdf"
    if mv[:4] == b"PK\x03\x04":
        return "application/zip"
    if mv[:3] == b"\x1f\x8b\x08":
        return "application/gzip"
    if mv[:3] == b"ID3" or (
        len(mv) >= 2 and mv[0] == 0xFF and (mv[1] & 0xE0) == 0xE0
    ):
        # ID3 header or MPEG frame sync
        return "audio/mpeg"
    if mv[:4] == b"fLaC":
        return "audio/flac"

    # ---- RIFF containers (WebP, WAV) ----
    if len(mv) >= 12 and mv[:4] == b"RIFF":
        if mv[8:12] == b"WEBP":
            return "image/webp"
        if mv[8:12] == b"WAVE":
            return "audio/wav"

    # ---- Ogg container (Vorbis/Opus/Theora) ----
    if mv[:4] == b"OggS":
        # Peek codec marker at a typical offset (not guaranteed, but common)
        #  - "OpusHead" => audio/opus
        #  - "\x01vorbis" => audio/vorbis
        #  - "\x80theora" => video/theora
        tail = bytes(mv[:64])  # small copy to simplify scanning
        if b"OpusHead" in tail:
            return "audio/opus"
        if b"\x01vorbis" in tail:
            return "audio/vorbis"
        if b"\x80theora" in tail:
            return "video/theora"
        return "application/ogg"

    # ---- ISO BMFF (MP4/AVIF/HEIF, etc.) via 'ftyp' brand ----
    # Layout: size(4) 'ftyp'(4) major_brand(4) minor_version(4) compatible_brands...
    if len(mv) >= 12 and mv[4:8] == b"ftyp":
        brand = bytes(mv[8:12])
        # Common MP4/QuickTime brands
        mp4_brands = {b"isom", b"iso2", b"mp41", b"mp42", b"MSNV", b"avc1"}
        if brand in mp4_brands:
            return "video/mp4"

        # AVIF / HEIF family
        if brand in {b"avif", b"avis"}:
            return "image/avif"
        if brand in {b"heic", b"heix", b"hevc", b"hevx"}:
            return "image/heif"

        # Fallback for unrecognized ISO-BMFF brands (could be many types)
        return "application/octet-stream"

    return None


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["mimetype_sniff"]
