"""Ghostscript discovery and command building / execution."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

from gsgui.models import (
    ColorMode,
    Compatibility,
    ConversionOptions,
    FileKind,
    ImagePdfMode,
    Orientation,
    OutputLocation,
    OverwritePolicy,
    PaperSize,
    PdfSettings,
    QueueItem,
)


PAGE_RANGE_RE = re.compile(r"^\d+(-\d+)?(,\d+(-\d+)?)*$")


def find_ghostscript(explicit: str | None = None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        if candidate.is_file():
            return candidate

    for name in ("gswin64c.exe", "gswin32c.exe", "gs"):
        found = shutil.which(name)
        if found:
            return Path(found)

    program_files = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
    ]
    for root in program_files:
        gs_root = root / "gs"
        if not gs_root.is_dir():
            continue
        versions = sorted(gs_root.glob("gs*"), reverse=True)
        for version_dir in versions:
            for exe_name in ("gswin64c.exe", "gswin32c.exe"):
                exe = version_dir / "bin" / exe_name
                if exe.is_file():
                    return exe
    return None


def validate_page_range(page_range: str) -> bool:
    text = page_range.strip()
    if not text:
        return True
    return bool(PAGE_RANGE_RE.match(text))


def resolve_output_path(
    source: Path,
    options: ConversionOptions,
    *,
    merge_name: str | None = None,
    create_dirs: bool = True,
) -> Path:
    """Resolve the output PDF path. Set create_dirs=False for dry-run / preview."""
    if options.output_location == OutputLocation.CUSTOM and options.custom_output_dir.strip():
        out_dir = Path(options.custom_output_dir)
    else:
        out_dir = source.parent
    if create_dirs:
        out_dir.mkdir(parents=True, exist_ok=True)

    stem = merge_name if merge_name else f"{source.stem}_gs"
    candidate = out_dir / f"{stem}.pdf"

    if options.overwrite_policy == OverwritePolicy.OVERWRITE or not candidate.exists():
        return candidate

    index = 1
    while True:
        numbered = out_dir / f"{stem}_{index}.pdf"
        if not numbered.exists():
            return numbered
        index += 1


def _color_args(color_mode: ColorMode) -> list[str]:
    if color_mode == ColorMode.GRAY:
        return ["-sColorConversionStrategy=Gray", "-dProcessColorModel=/DeviceGray"]
    if color_mode == ColorMode.RGB:
        return ["-sColorConversionStrategy=RGB", "-dProcessColorModel=/DeviceRGB"]
    if color_mode == ColorMode.CMYK:
        return ["-sColorConversionStrategy=CMYK", "-dProcessColorModel=/DeviceCMYK"]
    return ["-sColorConversionStrategy=LeaveColorUnchanged"]


def _compat_args(compat: Compatibility) -> list[str]:
    return [f"-dCompatibilityLevel={compat.value}"]


def _downsample_args(dpi: int, jpeg_quality: int) -> list[str]:
    return [
        "-dDownsampleColorImages=true",
        f"-dColorImageResolution={dpi}",
        "-dColorImageDownsampleType=/Bicubic",
        "-dDownsampleGrayImages=true",
        f"-dGrayImageResolution={dpi}",
        "-dGrayImageDownsampleType=/Bicubic",
        "-dDownsampleMonoImages=true",
        f"-dMonoImageResolution={dpi}",
        "-dMonoImageDownsampleType=/Subsample",
        "-dAutoFilterColorImages=false",
        "-dAutoFilterGrayImages=false",
        "-dColorImageFilter=/DCTEncode",
        "-dGrayImageFilter=/DCTEncode",
        f"-dJPEGQ={jpeg_quality}",
    ]


def _page_args(page_range: str, kind: FileKind) -> list[str]:
    text = page_range.strip()
    if not text or kind == FileKind.IMAGE:
        return []
    # Ghostscript accepts -dFirstPage/-dLastPage for contiguous ranges.
    # For simple "N-M" or "N" use those; otherwise fall back to -sPageList.
    if re.fullmatch(r"\d+", text):
        return [f"-dFirstPage={text}", f"-dLastPage={text}"]
    if re.fullmatch(r"\d+-\d+", text):
        first, last = text.split("-", 1)
        return [f"-dFirstPage={first}", f"-dLastPage={last}"]
    return [f"-sPageList={text}"]


def _paper_args(options: ConversionOptions) -> list[str]:
    if options.paper_size == PaperSize.FIT:
        return []
    args = ["-dFIXEDMEDIA", "-dPDFFitPage"]
    if options.paper_size == PaperSize.A4:
        args += ["-sPAPERSIZE=a4"]
    elif options.paper_size == PaperSize.LETTER:
        args += ["-sPAPERSIZE=letter"]
    if options.orientation == Orientation.LANDSCAPE:
        args += ["-dORIENT1=true"]
    elif options.orientation == Orientation.PORTRAIT:
        args += ["-dORIENT1=false"]
    return args


def _base_pdfwrite_args(gs_path: Path, options: ConversionOptions) -> list[str]:
    """Shared Ghostscript pdfwrite flags (device, preset, color, downsample)."""
    return [
        str(gs_path),
        "-dSAFER",
        "-dBATCH",
        "-dNOPAUSE",
        "-sDEVICE=pdfwrite",
        f"-dPDFSETTINGS=/{options.pdf_settings.value}",
        *_compat_args(options.compatibility),
        *_color_args(options.color_mode),
        *_downsample_args(options.resolution_dpi, options.jpeg_quality),
    ]


def build_pdf_or_ps_command(
    gs_path: Path,
    item: QueueItem,
    output: Path,
    options: ConversionOptions,
) -> list[str]:
    return [
        *_base_pdfwrite_args(gs_path, options),
        *_page_args(options.page_range, item.kind),
        f"-sOutputFile={output}",
        str(item.path),
    ]


def build_image_commands(
    gs_path: Path,
    items: list[QueueItem],
    options: ConversionOptions,
    *,
    create_dirs: bool = True,
) -> list[tuple[list[QueueItem], Path, list[str]]]:
    """Return list of (affected_items, output_path, command)."""
    results: list[tuple[list[QueueItem], Path, list[str]]] = []
    base = _base_pdfwrite_args(gs_path, options)
    paper = _paper_args(options)

    if options.image_pdf_mode == ImagePdfMode.MERGE and len(items) > 0:
        first = items[0]
        output = resolve_output_path(
            first.path, options, merge_name="images_merged_gs", create_dirs=create_dirs
        )
        cmd = [
            *base,
            *paper,
            f"-sOutputFile={output}",
            *[str(i.path) for i in items],
        ]
        results.append((items, output, cmd))
        return results

    for item in items:
        output = resolve_output_path(item.path, options, create_dirs=create_dirs)
        cmd = [
            *base,
            *paper,
            f"-sOutputFile={output}",
            str(item.path),
        ]
        results.append(([item], output, cmd))
    return results


def format_gs_command(cmd: list[str]) -> str:
    """Human-readable command line for logs / preview (NFC for display)."""
    from gsgui.textutil import nfc

    parts: list[str] = []
    for c in cmd:
        shown = nfc(c)
        if " " in shown or any(ord(ch) > 127 for ch in shown):
            parts.append(f'"{shown}"')
        else:
            parts.append(shown)
    return " ".join(parts)


def run_ghostscript(command: list[str], timeout: int | None = None) -> tuple[int, str]:
    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        creationflags=creationflags,
    )
    combined = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, combined.strip()


def probe_pdf_page_count(gs_path: Path, pdf_path: Path) -> int | None:
    cmd = [
        str(gs_path),
        "-dSAFER",
        "-dNODISPLAY",
        "-dBATCH",
        "-dNOPAUSE",
        "-q",
        "-c",
        f"({_escape_ps_path(pdf_path)}) (r) file runpdfbegin pdfpagecount = quit",
    ]
    try:
        code, output = run_ghostscript(cmd, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if code != 0:
        return None
    for line in reversed(output.splitlines()):
        line = line.strip()
        if line.isdigit():
            return int(line)
    return None


def _escape_ps_path(path: Path) -> str:
    text = str(path.resolve()).replace("\\", "/")
    return text.replace("(", "\\(").replace(")", "\\)")
