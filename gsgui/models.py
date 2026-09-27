"""Domain models and conversion options for GSGui."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".ps",
    ".eps",
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
POSTSCRIPT_EXTENSIONS = {".ps", ".eps"}


class FileKind(str, Enum):
    PDF = "pdf"
    POSTSCRIPT = "ps"
    IMAGE = "image"
    UNKNOWN = "unknown"


class PdfSettings(str, Enum):
    SCREEN = "screen"
    EBOOK = "ebook"
    PRINTER = "printer"
    PREPRESS = "prepress"
    DEFAULT = "default"


class ColorMode(str, Enum):
    KEEP = "keep"
    GRAY = "gray"
    RGB = "rgb"
    CMYK = "cmyk"


class Compatibility(str, Enum):
    PDF_1_4 = "1.4"
    PDF_1_7 = "1.7"
    PDF_2_0 = "2.0"


class PaperSize(str, Enum):
    FIT = "fit"
    A4 = "a4"
    LETTER = "letter"


class Orientation(str, Enum):
    AUTO = "auto"
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class OverwritePolicy(str, Enum):
    OVERWRITE = "overwrite"
    NUMBERED = "numbered"


class OutputLocation(str, Enum):
    SAME_AS_SOURCE = "same"
    CUSTOM = "custom"


class ImagePdfMode(str, Enum):
    ONE_PER_FILE = "one_per_file"
    MERGE = "merge"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


def classify_path(path: Path) -> FileKind:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return FileKind.PDF
    if ext in POSTSCRIPT_EXTENSIONS:
        return FileKind.POSTSCRIPT
    if ext in IMAGE_EXTENSIONS:
        return FileKind.IMAGE
    return FileKind.UNKNOWN


@dataclass
class ConversionOptions:
    pdf_settings: PdfSettings = PdfSettings.EBOOK
    compatibility: Compatibility = Compatibility.PDF_1_7
    color_mode: ColorMode = ColorMode.KEEP
    resolution_dpi: int = 150
    jpeg_quality: int = 85
    page_range: str = ""
    paper_size: PaperSize = PaperSize.FIT
    orientation: Orientation = Orientation.AUTO
    image_pdf_mode: ImagePdfMode = ImagePdfMode.ONE_PER_FILE
    output_location: OutputLocation = OutputLocation.SAME_AS_SOURCE
    custom_output_dir: str = ""
    overwrite_policy: OverwritePolicy = OverwritePolicy.OVERWRITE


@dataclass
class QueueItem:
    path: Path
    kind: FileKind
    size_bytes: int = 0
    meta: str = ""
    status: JobStatus = JobStatus.PENDING
    message: str = ""
    output_path: Path | None = None
    output_size_bytes: int | None = None
    command: list[str] = field(default_factory=list)

    @property
    def reduction_percent(self) -> float | None:
        if self.output_size_bytes is None or self.size_bytes <= 0:
            return None
        return (1.0 - (self.output_size_bytes / self.size_bytes)) * 100.0


def format_size(num_bytes: int | None) -> str:
    if num_bytes is None:
        return "—"
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024.0 or unit == "GB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{num_bytes} B"
