"""UI label <-> enum value maps (single source for display strings)."""

from __future__ import annotations

from gsgui.models import (
    ColorMode,
    ImagePdfMode,
    Orientation,
    OutputLocation,
    OverwritePolicy,
    PaperSize,
)

COLOR_LABEL_TO_VALUE: dict[str, str] = {
    "そのまま": ColorMode.KEEP.value,
    "グレー": ColorMode.GRAY.value,
    "RGB": ColorMode.RGB.value,
    "CMYK": ColorMode.CMYK.value,
}
COLOR_VALUE_TO_LABEL: dict[str, str] = {v: k for k, v in COLOR_LABEL_TO_VALUE.items()}

PAPER_LABEL_TO_VALUE: dict[str, str] = {
    "合わせる": PaperSize.FIT.value,
    "A4": PaperSize.A4.value,
    "Letter": PaperSize.LETTER.value,
}
PAPER_VALUE_TO_LABEL: dict[str, str] = {v: k for k, v in PAPER_LABEL_TO_VALUE.items()}

ORIENT_LABEL_TO_VALUE: dict[str, str] = {
    "自動": Orientation.AUTO.value,
    "縦": Orientation.PORTRAIT.value,
    "横": Orientation.LANDSCAPE.value,
}
ORIENT_VALUE_TO_LABEL: dict[str, str] = {v: k for k, v in ORIENT_LABEL_TO_VALUE.items()}

OUT_LABEL_TO_VALUE: dict[str, str] = {
    "元と同じ": OutputLocation.SAME_AS_SOURCE.value,
    "フォルダ指定": OutputLocation.CUSTOM.value,
}
OUT_VALUE_TO_LABEL: dict[str, str] = {v: k for k, v in OUT_LABEL_TO_VALUE.items()}

OVERWRITE_LABEL_TO_VALUE: dict[str, str] = {
    "上書き": OverwritePolicy.OVERWRITE.value,
    "連番": OverwritePolicy.NUMBERED.value,
}
OVERWRITE_VALUE_TO_LABEL: dict[str, str] = {v: k for k, v in OVERWRITE_LABEL_TO_VALUE.items()}

IMG_LABEL_TO_VALUE: dict[str, str] = {
    "ファイルごと": ImagePdfMode.ONE_PER_FILE.value,
    "まとめて1つ": ImagePdfMode.MERGE.value,
}
IMG_VALUE_TO_LABEL: dict[str, str] = {v: k for k, v in IMG_LABEL_TO_VALUE.items()}

DPI_PRESETS: tuple[str, ...] = ("72", "150", "300")
