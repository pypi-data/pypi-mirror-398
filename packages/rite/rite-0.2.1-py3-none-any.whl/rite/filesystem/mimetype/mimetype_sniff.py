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

BytesLike = bytes | bytearray | memoryview


# =============================================================================
# Helper Functions
# =============================================================================


def _check_fixed_signatures(mv: memoryview) -> str | None:
    """Check fixed magic number signatures."""
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
        return "audio/mpeg"
    if mv[:4] == b"fLaC":
        return "audio/flac"
    return None


def _check_riff_container(mv: memoryview) -> str | None:
    """Check RIFF container format (WebP, WAV)."""
    if len(mv) >= 12 and mv[:4] == b"RIFF":
        if mv[8:12] == b"WEBP":
            return "image/webp"
        if mv[8:12] == b"WAVE":
            return "audio/wav"
    return None


def _check_ogg_container(mv: memoryview) -> str | None:
    """Check Ogg container format (Opus, Vorbis, Theora)."""
    if mv[:4] == b"OggS":
        tail = bytes(mv[:64])
        if b"OpusHead" in tail:
            return "audio/opus"
        if b"\x01vorbis" in tail:
            return "audio/vorbis"
        if b"\x80theora" in tail:
            return "video/theora"
        return "application/ogg"
    return None


def _check_iso_bmff(mv: memoryview) -> str | None:
    """Check ISO BMFF format (MP4, AVIF, HEIF) via ftyp brand."""
    if len(mv) >= 12 and mv[4:8] == b"ftyp":
        brand = bytes(mv[8:12])
        mp4_brands = {b"isom", b"iso2", b"mp41", b"mp42", b"MSNV", b"avc1"}
        if brand in mp4_brands:
            return "video/mp4"
        if brand in {b"avif", b"avis"}:
            return "image/avif"
        if brand in {b"heic", b"heix", b"hevc", b"hevx"}:
            return "image/heif"
        return "application/octet-stream"
    return None


# =============================================================================
# Functions
# =============================================================================


def mimetype_sniff(
    buf: BytesLike,
    *,
    max_probe: int = 512,
) -> str | None:
    """
    Best-effort MIME sniffing from magic numbers.

    Returns None if no known signature is found. Only inspects the first
    `max_probe` bytes (default 512). Supports common formats: PNG, JPEG,
    GIF, WebP, PDF, ZIP, GZIP, MP3/ID3, MP4 (ftyp brands), WAV,
    Ogg/Opus/Vorbis, FLAC, AVIF/HEIF.

    Args:
    ----
        buf: Bytes-like object to sniff.
        max_probe: Maximum bytes to inspect. Defaults to 512.

    Returns:
    -------
        str | None: MIME type string or None if unrecognized.
    """
    if not buf:
        return None

    mv = memoryview(buf)[:max_probe]

    result = _check_fixed_signatures(mv)
    if result:
        return result

    result = _check_riff_container(mv)
    if result:
        return result

    result = _check_ogg_container(mv)
    if result:
        return result

    result = _check_iso_bmff(mv)
    if result:
        return result

    return None


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["mimetype_sniff"]
