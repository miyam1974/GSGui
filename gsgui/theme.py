"""UI theme: colors, fonts, and layout constants."""

from __future__ import annotations

import tkinter as tk
from typing import Any

import customtkinter as ctk

# Soft sky + coral: casual/pop settings vs action CTAs (avoid purple / cream AI defaults)
COLOR = {
    "bg": ("#F3F6FB", "#171A22"),
    "panel": ("#FFFFFF", "#222632"),
    "panel_alt": ("#EEF2F8", "#2C3140"),
    "drop": ("#E7F3FF", "#1C2838"),
    "drop_border": ("#6AADFF", "#5B9CF5"),
    # Settings / selection — deeper blue so white label text stays readable
    "accent": ("#2F6FE0", "#4B8AF5"),
    "accent_hover": ("#245CC4", "#6A9DFF"),
    "seg_on_text": ("#FFFFFF", "#FFFFFF"),
    "seg_off_text": ("#1C2230", "#E8EEF6"),
    # Preset chip muted selection while GS既定 is on
    "seg_muted_on": ("#A8C5F0", "#2A4A78"),
    "seg_muted_on_text": ("#1C2230", "#D8E4F8"),
    "seg_muted_off": ("#E8ECF2", "#252A36"),
    # Primary action — convert (coral)
    "cta": ("#FF6B5A", "#FF8576"),
    "cta_hover": ("#F05545", "#FF9A8D"),
    "cta_text": ("#FFFFFF", "#FFFFFF"),
    # Secondary action — cancel / interrupt (soft coral outline feel)
    "stop": ("#FFE9E5", "#3A2A2C"),
    "stop_hover": ("#FFD5CE", "#4A3538"),
    "stop_text": ("#D9483A", "#FF8F82"),
    "stop_disabled": ("#F0F2F6", "#2A2E3A"),
    "stop_disabled_text": ("#A8B0BE", "#6B7380"),
    "muted": ("#6A7282", "#9AA3B2"),
    "text": ("#1C2230", "#EEF1F6"),
    "success": ("#1FA971", "#3DDB96"),
    "danger": ("#E04545", "#F87171"),
    "row": ("#FFFFFF", "#1E2330"),
    # Selected row: stronger fill + border so selection reads at a glance
    "row_sel": ("#7EB6FF", "#1A3A66"),
    "row_sel_border": ("#1E5AD4", "#7EB6FF"),
    "header": ("#D9E0EB", "#3A4154"),
    "brand": ("#FF6B5A", "#FF8576"),
    "icon": ("#1E5AD4", "#8BB4FF"),
    "icon_muted": ("#C5CAD6", "#4A5160"),
}

# —— Window / panes ——
WINDOW_DEFAULT_GEOMETRY = "1140x680"
WINDOW_MIN_WIDTH = 960
WINDOW_FALLBACK_MIN_HEIGHT = 580
LEFT_PANE_MIN_WIDTH = 560
RIGHT_PANE_WIDTH = 300
RIGHT_SECTION_TITLE_WRAP = RIGHT_PANE_WIDTH - 28
RIGHT_HELP_WRAP = RIGHT_PANE_WIDTH - 40
ADVANCED_DIALOG_WIDTH = 480
ADVANCED_DIALOG_HEIGHT = 520
ADVANCED_HELP_WRAP = 420
ADVANCED_LABEL_WIDTH = 100

# Keep restored windows partially on-screen (title-bar slice)
GEOMETRY_EDGE_MARGIN = 80
GEOMETRY_TITLE_MARGIN = 40

# —— Queue table ——
QUEUE_COL_STATUS = 56
QUEUE_COL_META = 90
QUEUE_COL_SIZE = 64
QUEUE_COL_REDUCTION = 48
QUEUE_COL_OPEN = 64
QUEUE_COL_FILE_FALLBACK = 180
# Fixed columns + paddings used when computing filename wraplength
QUEUE_FIXED_COLS_WIDTH = (
    QUEUE_COL_STATUS
    + QUEUE_COL_META
    + QUEUE_COL_SIZE
    + QUEUE_COL_SIZE
    + QUEUE_COL_REDUCTION
    + QUEUE_COL_OPEN
    + 34
)  # ≈ 420
QUEUE_NAME_MIN_WRAP = 120
QUEUE_SCROLL_FALLBACK_WIDTH = 560
QUEUE_OPEN_BTN_WIDTH = 28
QUEUE_OPEN_BTN_HEIGHT = 24
QUEUE_DETAIL_WRAP_EXTRA = 200

QUEUE_COLUMNS: tuple[tuple[str, int], ...] = (
    ("状態", QUEUE_COL_STATUS),
    ("ファイル", 0),
    ("情報", QUEUE_COL_META),
    ("元", QUEUE_COL_SIZE),
    ("出力", QUEUE_COL_SIZE),
    ("削減", QUEUE_COL_REDUCTION),
    ("開く", QUEUE_COL_OPEN),
)

_FONT_CANDIDATES = (
    "Yu Gothic UI",
    "Meiryo UI",
    "Noto Sans JP",
    "Segoe UI",
)

_FAMILY = "Yu Gothic UI"


def init_fonts(root: Any) -> str:
    """Pick a clean JP UI font using an existing Tk root."""
    global _FAMILY
    try:
        families = {str(f) for f in root.tk.call("font", "families")}
    except tk.TclError:
        families = set()
    for name in _FONT_CANDIDATES:
        if name in families:
            _FAMILY = name
            break
    else:
        _FAMILY = "Segoe UI"
    return _FAMILY


def font(size: int = 13, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=_FAMILY, size=size, weight=weight)


def icon_font(size: int = 14) -> ctk.CTkFont:
    """Prefer an emoji-capable font for small action icons."""
    return ctk.CTkFont(family="Segoe UI Emoji", size=size)
