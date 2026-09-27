"""Preset descriptions and compact UI copy."""

from __future__ import annotations

from dataclasses import dataclass

from gsgui.models import Compatibility, PdfSettings

# Half-width spaces after 。 help Tk wrap at sentence boundaries
# (Japanese text otherwise wraps mid-phrase). Avoid spaces inside （…）.
PRESET_INFO: dict[str, tuple[str, str]] = {
    PdfSettings.SCREEN.value: (
        "画面",
        "Web・画面閲覧向け（目安72dpi）",
    ),
    PdfSettings.EBOOK.value: (
        "電子書籍",
        "推奨（初期値）。 メール添付やタブレット向け。 サイズと読みやすさの両立（目安150dpi）。",
    ),
    PdfSettings.PRINTER.value: (
        "プリンタ",
        "画質優先。 印刷向け（目安300dpi）。 ファイル大きめ。",
    ),
    PdfSettings.PREPRESS.value: (
        "印刷入稿",
        "圧縮段階の最高画質・ほぼ無圧縮。 入稿・アーカイブ向け。 サイズは大きくなりやすい。",
    ),
    PdfSettings.DEFAULT.value: (
        "GS既定",
        "Distillerプロファイルなし。 プリンタ相当。",
    ),
}


@dataclass(frozen=True)
class PresetAdvancedDefaults:
    """Values applied to 詳細設定 when a preset is chosen."""

    resolution_dpi: int
    jpeg_quality: int
    compatibility: str


# Align with Ghostscript / Distiller PDFSETTINGS typical targets.
PRESET_ADVANCED: dict[str, PresetAdvancedDefaults] = {
    PdfSettings.SCREEN.value: PresetAdvancedDefaults(72, 50, Compatibility.PDF_1_4.value),
    PdfSettings.EBOOK.value: PresetAdvancedDefaults(150, 85, Compatibility.PDF_1_7.value),
    PdfSettings.PRINTER.value: PresetAdvancedDefaults(300, 90, Compatibility.PDF_1_7.value),
    PdfSettings.PREPRESS.value: PresetAdvancedDefaults(300, 95, Compatibility.PDF_1_7.value),
    PdfSettings.DEFAULT.value: PresetAdvancedDefaults(300, 90, Compatibility.PDF_1_7.value),
}

# Scale presets shown as segmented buttons (GS既定 is a separate checkbox).
PRESET_SCALE_ORDER = [
    PdfSettings.SCREEN.value,
    PdfSettings.EBOOK.value,
    PdfSettings.PRINTER.value,
    PdfSettings.PREPRESS.value,
]

PRESET_ORDER = [*PRESET_SCALE_ORDER, PdfSettings.DEFAULT.value]

PRESET_LABEL_TO_VALUE = {PRESET_INFO[v][0]: v for v in PRESET_ORDER}
PRESET_VALUE_TO_LABEL = {v: PRESET_INFO[v][0] for v in PRESET_ORDER}

GS_DEFAULT_CHECK_LABEL = "GS既定"
