"""UI label <-> enum value maps (per language)."""

from __future__ import annotations

from gsgui.i18n import Lang
from gsgui.models import (
    ColorMode,
    ImagePdfMode,
    Orientation,
    OutputLocation,
    OverwritePolicy,
    PaperSize,
)

# value -> label
_COLOR: dict[Lang, dict[str, str]] = {
    Lang.EN: {
        ColorMode.KEEP.value: "Keep",
        ColorMode.GRAY.value: "Gray",
        ColorMode.RGB.value: "RGB",
        ColorMode.CMYK.value: "CMYK",
    },
    Lang.JA: {
        ColorMode.KEEP.value: "そのまま",
        ColorMode.GRAY.value: "グレー",
        ColorMode.RGB.value: "RGB",
        ColorMode.CMYK.value: "CMYK",
    },
}

_PAPER: dict[Lang, dict[str, str]] = {
    Lang.EN: {
        PaperSize.FIT.value: "Fit",
        PaperSize.A4.value: "A4",
        PaperSize.LETTER.value: "Letter",
    },
    Lang.JA: {
        PaperSize.FIT.value: "合わせる",
        PaperSize.A4.value: "A4",
        PaperSize.LETTER.value: "Letter",
    },
}

_ORIENT: dict[Lang, dict[str, str]] = {
    Lang.EN: {
        Orientation.AUTO.value: "Auto",
        Orientation.PORTRAIT.value: "Portrait",
        Orientation.LANDSCAPE.value: "Landscape",
    },
    Lang.JA: {
        Orientation.AUTO.value: "自動",
        Orientation.PORTRAIT.value: "縦",
        Orientation.LANDSCAPE.value: "横",
    },
}

_OUT: dict[Lang, dict[str, str]] = {
    Lang.EN: {
        OutputLocation.SAME_AS_SOURCE.value: "Same folder",
        OutputLocation.CUSTOM.value: "Folder…",
    },
    Lang.JA: {
        OutputLocation.SAME_AS_SOURCE.value: "元と同じ",
        OutputLocation.CUSTOM.value: "フォルダ指定",
    },
}

_OVERWRITE: dict[Lang, dict[str, str]] = {
    Lang.EN: {
        OverwritePolicy.OVERWRITE.value: "Overwrite",
        OverwritePolicy.NUMBERED.value: "Numbered",
    },
    Lang.JA: {
        OverwritePolicy.OVERWRITE.value: "上書き",
        OverwritePolicy.NUMBERED.value: "連番",
    },
}

_IMG: dict[Lang, dict[str, str]] = {
    Lang.EN: {
        ImagePdfMode.ONE_PER_FILE.value: "Per file",
        ImagePdfMode.MERGE.value: "Merge one",
    },
    Lang.JA: {
        ImagePdfMode.ONE_PER_FILE.value: "ファイルごと",
        ImagePdfMode.MERGE.value: "まとめて1つ",
    },
}


def _label_to_value(value_to_label: dict[str, str]) -> dict[str, str]:
    return {label: value for value, label in value_to_label.items()}


def color_value_to_label(lang: Lang) -> dict[str, str]:
    return _COLOR[lang]


def color_label_to_value(lang: Lang) -> dict[str, str]:
    return _label_to_value(_COLOR[lang])


def paper_value_to_label(lang: Lang) -> dict[str, str]:
    return _PAPER[lang]


def paper_label_to_value(lang: Lang) -> dict[str, str]:
    return _label_to_value(_PAPER[lang])


def orient_value_to_label(lang: Lang) -> dict[str, str]:
    return _ORIENT[lang]


def orient_label_to_value(lang: Lang) -> dict[str, str]:
    return _label_to_value(_ORIENT[lang])


def out_value_to_label(lang: Lang) -> dict[str, str]:
    return _OUT[lang]


def out_label_to_value(lang: Lang) -> dict[str, str]:
    return _label_to_value(_OUT[lang])


def overwrite_value_to_label(lang: Lang) -> dict[str, str]:
    return _OVERWRITE[lang]


def overwrite_label_to_value(lang: Lang) -> dict[str, str]:
    return _label_to_value(_OVERWRITE[lang])


def img_value_to_label(lang: Lang) -> dict[str, str]:
    return _IMG[lang]


def img_label_to_value(lang: Lang) -> dict[str, str]:
    return _label_to_value(_IMG[lang])


DPI_PRESETS: tuple[str, ...] = ("72", "150", "300")

# Back-compat aliases used by older imports / tests (Japanese maps).
COLOR_LABEL_TO_VALUE = color_label_to_value(Lang.JA)
COLOR_VALUE_TO_LABEL = color_value_to_label(Lang.JA)
PAPER_LABEL_TO_VALUE = paper_label_to_value(Lang.JA)
PAPER_VALUE_TO_LABEL = paper_value_to_label(Lang.JA)
ORIENT_LABEL_TO_VALUE = orient_label_to_value(Lang.JA)
ORIENT_VALUE_TO_LABEL = orient_value_to_label(Lang.JA)
OUT_LABEL_TO_VALUE = out_label_to_value(Lang.JA)
OUT_VALUE_TO_LABEL = out_value_to_label(Lang.JA)
OVERWRITE_LABEL_TO_VALUE = overwrite_label_to_value(Lang.JA)
OVERWRITE_VALUE_TO_LABEL = overwrite_value_to_label(Lang.JA)
IMG_LABEL_TO_VALUE = img_label_to_value(Lang.JA)
IMG_VALUE_TO_LABEL = img_value_to_label(Lang.JA)
