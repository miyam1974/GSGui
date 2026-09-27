"""Unicode helpers for display and path handling."""

from __future__ import annotations

import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlparse


def nfc(text: str) -> str:
    """Compose Unicode to NFC so dakuten render as single glyphs (display only)."""
    return unicodedata.normalize("NFC", text)


def nfd(text: str) -> str:
    return unicodedata.normalize("NFD", text)


def coerce_path_string(raw: str) -> str:
    """Clean a DnD / dialog path token without changing Unicode normalization.

    NFC must NOT be applied here: on Windows, an NFD filename (common for
    files from macOS) will fail Path.exists() after NFC conversion.
    """
    text = raw.strip().strip("\0").strip()
    if not text:
        return ""
    if len(text) >= 2 and text[0] == "{" and text[-1] == "}":
        text = text[1:-1].strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        text = text[1:-1].strip()

    lower = text.lower()
    if lower.startswith("file:"):
        parsed = urlparse(text)
        path_part = unquote(parsed.path or "")
        if parsed.netloc and parsed.netloc not in ("", "localhost"):
            path_part = f"//{parsed.netloc}{path_part}"
        if len(path_part) >= 3 and path_part[0] == "/" and path_part[2] == ":":
            path_part = path_part[1:]
        text = path_part or unquote(text[5:].lstrip("/"))

    return text


def _exists(path: Path) -> bool:
    try:
        return path.is_file() or path.is_dir()
    except OSError:
        return False


def normalize_path(path: Path) -> Path:
    """Return a Path that exists on disk, trying original / NFC / NFD forms."""
    cleaned = coerce_path_string(str(path)) or str(path)
    raw = Path(cleaned)

    candidates: list[Path] = [raw]
    # Alternate separators
    swapped = Path(cleaned.replace("/", "\\")) if "/" in cleaned else Path(cleaned.replace("\\", "/"))
    if swapped != raw:
        candidates.append(swapped)

    # Unicode normalization variants (parent stays as-is; only name remapped when needed)
    for norm in (nfc, nfd):
        try:
            alt = raw.with_name(norm(raw.name))
        except (ValueError, OSError):
            alt = Path(norm(str(raw)))
        if alt not in candidates:
            candidates.append(alt)
        # Full-string normalize as last resort
        full = Path(norm(str(raw)))
        if full not in candidates:
            candidates.append(full)

    for candidate in candidates:
        if _exists(candidate):
            return candidate

    try:
        expanded = raw.expanduser()
        if _exists(expanded):
            return expanded
    except OSError:
        pass

    # Keep original DnD string — do not force NFC when missing
    return raw
