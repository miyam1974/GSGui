"""File metadata helpers for the queue."""

from __future__ import annotations

from pathlib import Path

from gsgui.ghostscript import find_ghostscript, probe_pdf_page_count
from gsgui.models import (
    SUPPORTED_EXTENSIONS,
    FileKind,
    QueueItem,
    classify_path,
)
from gsgui.textutil import nfc, normalize_path


def collect_files(paths: list[Path]) -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()
    for raw in paths:
        path = normalize_path(Path(raw))
        try:
            is_dir = path.is_dir()
            is_file = path.is_file()
        except OSError:
            continue
        if is_dir:
            for child in sorted(path.rglob("*")):
                try:
                    if not child.is_file():
                        continue
                except OSError:
                    continue
                if child.suffix.lower() in SUPPORTED_EXTENSIONS:
                    child = normalize_path(child)
                    try:
                        resolved = child.resolve()
                    except OSError:
                        resolved = child
                    if resolved not in seen:
                        seen.add(resolved)
                        found.append(child)
        elif is_file and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                resolved = path.resolve()
            except OSError:
                resolved = path
            if resolved not in seen:
                seen.add(resolved)
                found.append(path)
    return found


def build_queue_item(path: Path) -> QueueItem:
    """Build a queue row quickly. PDF page counts are filled later via enrich_pdf_meta."""
    path = normalize_path(path)
    kind = classify_path(path)
    try:
        size = path.stat().st_size if path.exists() else 0
    except OSError:
        size = 0
    meta = ""

    if kind == FileKind.IMAGE:
        try:
            from PIL import Image, UnidentifiedImageError

            with Image.open(path) as img:
                meta = f"{img.width}×{img.height}"
        except (OSError, UnidentifiedImageError, ValueError):
            meta = "画像"
    elif kind == FileKind.PDF:
        meta = "PDF"
    elif kind == FileKind.POSTSCRIPT:
        meta = "PostScript"
    else:
        meta = "不明"

    return QueueItem(
        path=path,
        kind=kind,
        size_bytes=size,
        meta=meta,
    )


def enrich_pdf_meta(item: QueueItem, gs_path: Path | None = None) -> str | None:
    """Probe page count for a PDF item. Returns new meta text, or None if unchanged."""
    if item.kind != FileKind.PDF:
        return None
    executable = gs_path or find_ghostscript()
    if not executable:
        return None
    pages = probe_pdf_page_count(executable, item.path)
    if not pages:
        return None
    return f"{pages} ページ"


def display_name(path: Path) -> str:
    """Show composed dakuten in the UI without changing the on-disk path."""
    return nfc(path.name)
