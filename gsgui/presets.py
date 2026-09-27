"""Preset descriptions and compact UI copy (per language)."""

from __future__ import annotations

from dataclasses import dataclass

from gsgui.i18n import Lang
from gsgui.models import Compatibility, PdfSettings

# value -> (short label, help text)
_PRESET_INFO: dict[Lang, dict[str, tuple[str, str]]] = {
    Lang.EN: {
        PdfSettings.SCREEN.value: (
            "Screen",
            "For web / on-screen viewing (~72 dpi).",
        ),
        PdfSettings.EBOOK.value: (
            "Ebook",
            "Recommended (default). Email and tablets. Balance of size and readability (~150 dpi).",
        ),
        PdfSettings.PRINTER.value: (
            "Printer",
            "Quality first. For printing (~300 dpi). Larger files.",
        ),
        PdfSettings.PREPRESS.value: (
            "Prepress",
            "Highest quality / almost no compression. For print submission and archives. Often large.",
        ),
        PdfSettings.DEFAULT.value: (
            "GS default",
            "No Distiller profile. Similar to Printer.",
        ),
    },
    Lang.JA: {
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
    },
}


@dataclass(frozen=True)
class PresetAdvancedDefaults:
    """Values applied to Advanced settings when a preset is chosen."""

    resolution_dpi: int
    jpeg_quality: int
    compatibility: str


PRESET_ADVANCED: dict[str, PresetAdvancedDefaults] = {
    PdfSettings.SCREEN.value: PresetAdvancedDefaults(72, 50, Compatibility.PDF_1_4.value),
    PdfSettings.EBOOK.value: PresetAdvancedDefaults(150, 85, Compatibility.PDF_1_7.value),
    PdfSettings.PRINTER.value: PresetAdvancedDefaults(300, 90, Compatibility.PDF_1_7.value),
    PdfSettings.PREPRESS.value: PresetAdvancedDefaults(300, 95, Compatibility.PDF_1_7.value),
    PdfSettings.DEFAULT.value: PresetAdvancedDefaults(300, 90, Compatibility.PDF_1_7.value),
}

PRESET_SCALE_ORDER = [
    PdfSettings.SCREEN.value,
    PdfSettings.EBOOK.value,
    PdfSettings.PRINTER.value,
    PdfSettings.PREPRESS.value,
]

PRESET_ORDER = [*PRESET_SCALE_ORDER, PdfSettings.DEFAULT.value]


def preset_info(lang: Lang) -> dict[str, tuple[str, str]]:
    return _PRESET_INFO[lang]


def preset_label_to_value(lang: Lang) -> dict[str, str]:
    info = _PRESET_INFO[lang]
    return {info[v][0]: v for v in PRESET_ORDER}


def preset_value_to_label(lang: Lang) -> dict[str, str]:
    info = _PRESET_INFO[lang]
    return {v: info[v][0] for v in PRESET_ORDER}


def gs_default_check_label(lang: Lang) -> str:
    return _PRESET_INFO[lang][PdfSettings.DEFAULT.value][0]


# Back-compat (Japanese)
PRESET_INFO = _PRESET_INFO[Lang.JA]
PRESET_LABEL_TO_VALUE = preset_label_to_value(Lang.JA)
PRESET_VALUE_TO_LABEL = preset_value_to_label(Lang.JA)
GS_DEFAULT_CHECK_LABEL = gs_default_check_label(Lang.JA)
