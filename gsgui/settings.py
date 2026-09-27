"""Persistent user settings."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from gsgui.models import (
    ColorMode,
    Compatibility,
    ConversionOptions,
    ImagePdfMode,
    Orientation,
    OutputLocation,
    OverwritePolicy,
    PaperSize,
    PdfSettings,
)


def settings_path() -> Path:
    return Path.home() / ".gsgui" / "settings.json"


@dataclass
class AppSettings:
    ghostscript_path: str = ""
    pdf_settings: str = PdfSettings.EBOOK.value
    compatibility: str = Compatibility.PDF_1_7.value
    color_mode: str = ColorMode.KEEP.value
    resolution_dpi: int = 150
    jpeg_quality: int = 85
    page_range: str = ""
    paper_size: str = PaperSize.FIT.value
    orientation: str = Orientation.AUTO.value
    image_pdf_mode: str = ImagePdfMode.ONE_PER_FILE.value
    output_location: str = OutputLocation.SAME_AS_SOURCE.value
    custom_output_dir: str = ""
    overwrite_policy: str = OverwritePolicy.OVERWRITE.value
    # Tk geometry string (see theme.WINDOW_DEFAULT_GEOMETRY)
    window_geometry: str = ""
    # Scale preset remembered while GS既定 is checked
    last_scale_preset: str = PdfSettings.EBOOK.value
    # UI language: "en" (default) or "ja"
    ui_language: str = "en"

    @classmethod
    def from_options(
        cls,
        options: ConversionOptions,
        ghostscript_path: str = "",
        window_geometry: str = "",
        last_scale_preset: str = PdfSettings.EBOOK.value,
        ui_language: str = "en",
    ) -> AppSettings:
        return cls(
            ghostscript_path=ghostscript_path,
            pdf_settings=options.pdf_settings.value,
            compatibility=options.compatibility.value,
            color_mode=options.color_mode.value,
            resolution_dpi=options.resolution_dpi,
            jpeg_quality=options.jpeg_quality,
            page_range=options.page_range,
            paper_size=options.paper_size.value,
            orientation=options.orientation.value,
            image_pdf_mode=options.image_pdf_mode.value,
            output_location=options.output_location.value,
            custom_output_dir=options.custom_output_dir,
            overwrite_policy=options.overwrite_policy.value,
            window_geometry=window_geometry,
            last_scale_preset=last_scale_preset,
            ui_language=ui_language,
        )


def load_settings() -> AppSettings:
    path = settings_path()
    if not path.exists():
        return AppSettings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        known = {f.name for f in AppSettings.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        return AppSettings(**filtered)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return AppSettings()


def save_settings(settings: AppSettings) -> bool:
    """Persist settings. Returns False on I/O failure (does not raise)."""
    path = settings_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(asdict(settings), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return True
    except OSError:
        return False
