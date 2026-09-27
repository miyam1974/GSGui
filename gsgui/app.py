"""Main CustomTkinter application."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

from gsgui.advanced_dialog import AdvancedDialog
from gsgui.drop_paths import parse_drop_paths
from gsgui.files import build_queue_item, collect_files, enrich_pdf_meta, relocalize_item_meta
from gsgui.ghostscript import (
    build_image_commands,
    build_pdf_or_ps_command,
    find_ghostscript,
    format_gs_command,
    resolve_output_path,
    validate_page_range,
)
from gsgui.i18n import LANG_TOGGLE_LABELS, Lang, parse_lang, t
from gsgui.labels import (
    color_label_to_value,
    color_value_to_label,
    img_label_to_value,
    img_value_to_label,
    orient_label_to_value,
    orient_value_to_label,
    out_label_to_value,
    out_value_to_label,
    overwrite_label_to_value,
    overwrite_value_to_label,
    paper_label_to_value,
    paper_value_to_label,
)
from gsgui.models import (
    ColorMode,
    Compatibility,
    ConversionOptions,
    FileKind,
    ImagePdfMode,
    JobStatus,
    Orientation,
    OutputLocation,
    OverwritePolicy,
    PaperSize,
    PdfSettings,
    QueueItem,
)
from gsgui.presets import (
    PRESET_ADVANCED,
    PRESET_SCALE_ORDER,
    gs_default_check_label,
    preset_info,
    preset_label_to_value,
    preset_value_to_label,
)
from gsgui.queue_view import (
    apply_queue_row_data,
    build_queue_empty_label,
    build_queue_header,
    build_queue_row,
    paint_queue_row_selection,
    queue_name_wraplength,
)
from gsgui.segment_style import (
    make_segment,
    paint_preset_segment,
    paint_segment,
    tighten_segment,
)
from gsgui.settings import AppSettings, load_settings, save_settings
from gsgui.textutil import coerce_path_string, nfc, normalize_path
from gsgui.theme import (
    COLOR,
    GEOMETRY_EDGE_MARGIN,
    GEOMETRY_TITLE_MARGIN,
    LEFT_PANE_MIN_WIDTH,
    RIGHT_HELP_WRAP,
    RIGHT_PANE_WIDTH,
    RIGHT_SECTION_TITLE_WRAP,
    WINDOW_DEFAULT_GEOMETRY,
    WINDOW_FALLBACK_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    font,
    init_fonts,
)
from gsgui.worker import ConversionWorker


class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self) -> None:
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("GSGui")
        self.geometry(WINDOW_DEFAULT_GEOMETRY)
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_FALLBACK_MIN_HEIGHT)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=COLOR["bg"])
        init_fonts(self)

        self.settings = load_settings()
        self._lang = parse_lang(self.settings.ui_language)
        self._i18n_labels: dict[str, ctk.CTkLabel] = {}
        self.gs_path: Path | None = find_ghostscript(self.settings.ghostscript_path or None)
        self.queue: list[QueueItem] = []
        self.worker: ConversionWorker | None = None
        self._row_widgets: list[dict] = []
        self.selected_index: int | None = None
        self._advanced: AdvancedDialog | None = None
        self._persist_after_id: str | None = None
        self._last_drop_key: str = ""
        self._last_drop_at: float = 0.0

        self._build_ui()
        self._apply_settings_to_ui()
        self._refresh_gs_label()
        self._refresh_queue_view()
        self._update_preset_help()
        self._update_command_preview()
        self.after_idle(self._apply_window_minsize)

    def _apply_window_minsize(self) -> None:
        """Keep the window tall enough that the right pane controls stay visible."""
        self.update_idletasks()
        right_h = sum(child.winfo_reqheight() for child in self._right_pane.winfo_children())
        # Section gaps (pady) between right-pane blocks
        right_h += 4 * max(0, len(self._right_pane.winfo_children()) - 1)
        header_h = self._header.winfo_reqheight() + 10  # pady (8, 2)
        bottom_h = self._bottom.winfo_reqheight() + 8  # pady bottom
        # Outer chrome: right pady (2, 6) + small buffer
        min_h = header_h + right_h + bottom_h + 16
        min_w = WINDOW_MIN_WIDTH
        self.minsize(min_w, min_h)
        self._restore_window_geometry(min_w, min_h)

    def _capture_window_geometry(self) -> str:
        self.update_idletasks()
        return self.geometry()

    def _restore_window_geometry(self, min_w: int, min_h: int) -> None:
        raw = (self.settings.window_geometry or "").strip()
        if not raw:
            return
        match = re.fullmatch(r"(\d+)x(\d+)([+-]\d+)([+-]\d+)", raw)
        if not match:
            return
        width = max(min_w, int(match.group(1)))
        height = max(min_h, int(match.group(2)))
        x = int(match.group(3))
        y = int(match.group(4))
        # Keep a usable slice of the title bar on the virtual screen
        try:
            screen_w = self.winfo_vrootwidth()
            screen_h = self.winfo_vrootheight()
        except tk.TclError:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
        if x + width < GEOMETRY_EDGE_MARGIN:
            x = GEOMETRY_TITLE_MARGIN
        if y + GEOMETRY_TITLE_MARGIN < 0:
            y = GEOMETRY_TITLE_MARGIN
        if x > screen_w - GEOMETRY_EDGE_MARGIN:
            x = max(0, screen_w - min(width, screen_w))
        if y > screen_h - GEOMETRY_EDGE_MARGIN:
            y = max(0, screen_h - min(height, screen_h))
        x_part = f"+{x}" if x >= 0 else str(x)
        y_part = f"+{y}" if y >= 0 else str(y)
        self.geometry(f"{width}x{height}{x_part}{y_part}")

    def _t(self, key: str, **kwargs: object) -> str:
        return t(self._lang, key, **kwargs)

    def _preset_value_to_label(self) -> dict[str, str]:
        return preset_value_to_label(self._lang)

    def _preset_label_to_value(self) -> dict[str, str]:
        return preset_label_to_value(self._lang)

    def _remap_string_var(self, var: ctk.StringVar, old_lang: Lang, new_lang: Lang, kind: str) -> None:
        maps = {
            "color": (color_label_to_value, color_value_to_label),
            "paper": (paper_label_to_value, paper_value_to_label),
            "orient": (orient_label_to_value, orient_value_to_label),
            "out": (out_label_to_value, out_value_to_label),
            "overwrite": (overwrite_label_to_value, overwrite_value_to_label),
            "img": (img_label_to_value, img_value_to_label),
        }
        l2v_fn, v2l_fn = maps[kind]
        value = l2v_fn(old_lang).get(var.get())
        if value is not None:
            var.set(v2l_fn(new_lang).get(value, var.get()))

    def _rebuild_preset_segment(self) -> None:
        labels = [self._preset_value_to_label()[v] for v in PRESET_SCALE_ORDER]
        self.preset_seg.configure(values=labels)
        if self._gs_default_var.get():
            self.preset_seg.configure(state="disabled")
        else:
            self.preset_seg.configure(state="normal")
            current = self.preset_var.get()
            if current in PRESET_SCALE_ORDER:
                self.preset_seg.set(self._preset_value_to_label()[current])
        self._paint_preset_segment()

    def _rebuild_choice_segment(self, seg: ctk.CTkSegmentedButton, var: ctk.StringVar, labels: list[str]) -> None:
        seg.configure(values=labels)
        if var.get() in labels:
            seg.set(var.get())
        elif labels:
            var.set(labels[0])
            seg.set(labels[0])
        paint_segment(seg)

    def _refresh_i18n_static_texts(self) -> None:
        for key, widget in self._i18n_labels.items():
            try:
                if widget.winfo_exists():
                    widget.configure(text=self._t(key))
            except tk.TclError:
                pass
        self.gs_path_btn.configure(text=self._t("gs_path_button"))
        self.gs_default_check.configure(text=gs_default_check_label(self._lang))
        self.queue_scroll.configure(label_text=self._t("queue_title"))
        self.convert_btn.configure(text=self._t("btn_convert"))
        self.cancel_btn.configure(text=self._t("btn_cancel"))
        self.advanced_btn.configure(text=self._t("btn_advanced"))
        self.output_dir_entry.configure(placeholder_text=self._t("placeholder_output_dir"))
        for btn, key in self._bar_buttons:
            btn.configure(text=self._t(key))
        self._refresh_gs_label()

    def _set_language(self, lang: Lang, *, persist: bool = True) -> None:
        if lang == self._lang and persist:
            return
        old_lang = self._lang
        for kind in ("color", "paper", "orient", "out", "overwrite", "img"):
            self._remap_string_var(getattr(self, f"{kind}_label_var"), old_lang, lang, kind)

        self._lang = lang
        if self._lang_seg is not None:
            self._lang_seg.set(LANG_TOGGLE_LABELS[lang])
            paint_segment(self._lang_seg)

        self._rebuild_preset_segment()
        self._rebuild_choice_segment(
            self.out_seg, self.out_label_var, list(out_label_to_value(lang).keys())
        )
        self._rebuild_choice_segment(
            self.overwrite_seg,
            self.overwrite_label_var,
            list(overwrite_label_to_value(lang).keys()),
        )
        self._rebuild_choice_segment(
            self.unit_seg, self.img_label_var, list(img_label_to_value(lang).keys())
        )
        self._refresh_i18n_static_texts()
        self._update_output_path_enabled()
        self._update_preset_help()
        self._update_command_preview()
        for item in self.queue:
            relocalize_item_meta(item, lang)
        self._refresh_queue_view()
        if persist:
            self.settings.ui_language = lang.value
            self._schedule_persist()

    def _on_lang_toggle(self, label: str) -> None:
        for lang, toggle_label in LANG_TOGGLE_LABELS.items():
            if toggle_label == label:
                self._set_language(lang)
                break
        if self._lang_seg is not None:
            paint_segment(self._lang_seg)

    def _paint_preset_segment(self) -> None:
        pmap = self._preset_value_to_label()
        label = pmap.get(self._last_scale_preset, pmap[PdfSettings.EBOOK.value])
        paint_preset_segment(
            self.preset_seg,
            last_scale_label=label,
            gs_default_on=bool(self._gs_default_var.get()),
        )

    def _section(self, parent: ctk.CTkFrame | ctk.CTk, title_key: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=COLOR["panel"], corner_radius=8)
        title_lbl = ctk.CTkLabel(
            frame,
            text=self._t(title_key),
            font=font(12, "bold"),
            text_color=COLOR["text"],
            anchor="w",
            justify="left",
            wraplength=RIGHT_SECTION_TITLE_WRAP,
        )
        title_lbl.pack(anchor="w", padx=10, pady=(6, 2))
        self._i18n_labels[title_key] = title_lbl
        return frame

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1, minsize=LEFT_PANE_MIN_WIDTH)
        self.grid_columnconfigure(1, weight=0, minsize=RIGHT_PANE_WIDTH)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        header = ctk.CTkFrame(self, fg_color="transparent", height=36)
        self._header = header
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(8, 2))
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(header, text="GSGui", font=font(20, "bold"), text_color=COLOR["brand"]).grid(
            row=0, column=0, sticky="w"
        )
        tagline = ctk.CTkLabel(
            header, text=self._t("tagline"), font=font(12), text_color=COLOR["muted"]
        )
        tagline.grid(row=0, column=1, sticky="w", padx=(10, 0))
        self._i18n_labels["tagline"] = tagline
        self.gs_status = ctk.CTkLabel(
            header, text="", font=font(11), text_color=COLOR["muted"], anchor="e"
        )
        self.gs_status.grid(row=0, column=2, sticky="e")
        lang_values = [LANG_TOGGLE_LABELS[Lang.EN], LANG_TOGGLE_LABELS[Lang.JA]]
        self._lang_seg = make_segment(header, lang_values, self._on_lang_toggle, height=26)
        self._lang_seg.grid(row=0, column=3, padx=(6, 0))
        self._lang_seg.set(LANG_TOGGLE_LABELS[self._lang])
        paint_segment(self._lang_seg)
        tighten_segment(self._lang_seg)
        self.gs_path_btn = ctk.CTkButton(
            header,
            text=self._t("gs_path_button"),
            height=26,
            font=font(11, "bold"),
            fg_color=COLOR["accent"],
            text_color=COLOR["seg_on_text"],
            hover_color=COLOR["accent_hover"],
            command=self._browse_gs,
        )
        self.gs_path_btn.grid(row=0, column=4, padx=(6, 0))

        left = ctk.CTkFrame(self, fg_color=COLOR["panel"], corner_radius=10)
        left.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=(2, 6))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(2, weight=1)

        self.drop_frame = ctk.CTkFrame(
            left,
            fg_color=COLOR["drop"],
            corner_radius=8,
            border_width=1,
            border_color=COLOR["drop_border"],
        )
        self.drop_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        drop_title = ctk.CTkLabel(
            self.drop_frame,
            text=self._t("drop_title"),
            font=font(14, "bold"),
            text_color=COLOR["drop_border"],
        )
        drop_title.pack(pady=(8, 0))
        self._i18n_labels["drop_title"] = drop_title
        drop_hint = ctk.CTkLabel(
            self.drop_frame,
            text=self._t("drop_hint"),
            font=font(11),
            text_color=COLOR["muted"],
        )
        drop_hint.pack(pady=(0, 8))
        self._i18n_labels["drop_hint"] = drop_hint

        bar = ctk.CTkFrame(left, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", padx=8, pady=2)
        self._bar_buttons: list[tuple[ctk.CTkButton, str]] = []
        for key, cmd in (
            ("btn_add", self._add_files),
            ("btn_remove", self._remove_selected),
            ("btn_clear", self._clear_queue),
        ):
            btn = ctk.CTkButton(
                bar,
                text=self._t(key),
                width=68,
                height=26,
                font=font(11),
                fg_color=COLOR["panel_alt"],
                text_color=COLOR["text"],
                hover_color=COLOR["header"],
                command=cmd,
            )
            btn.pack(side="left", padx=(0, 4))
            self._bar_buttons.append((btn, key))

        self.queue_scroll = ctk.CTkScrollableFrame(
            left,
            fg_color=COLOR["panel_alt"],
            corner_radius=8,
            label_text=self._t("queue_title"),
            label_fg_color=COLOR["panel"],
            label_text_color=COLOR["muted"],
            label_font=font(11, "bold"),
        )
        self.queue_scroll.grid(row=2, column=0, sticky="nsew", padx=8, pady=(2, 8))
        self.queue_scroll.grid_columnconfigure(0, weight=1)
        self.queue_scroll.bind("<Configure>", self._on_queue_configure, add="+")
        self._name_labels: list[ctk.CTkLabel] = []

        right = ctk.CTkFrame(self, width=RIGHT_PANE_WIDTH, fg_color="transparent")
        self._right_pane = right
        right.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=(2, 6))
        right.grid_propagate(False)
        right.grid_columnconfigure(0, weight=1)
        # No spacer row needed after removing links
        right.grid_rowconfigure(5, weight=1)

        preset = self._section(right, "section_preset")
        preset.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.preset_var = ctk.StringVar(value=PdfSettings.EBOOK.value)
        self._gs_default_var = ctk.BooleanVar(value=False)
        self._last_scale_preset = PdfSettings.EBOOK.value
        pmap = self._preset_value_to_label()
        self.preset_seg = make_segment(
            preset,
            [pmap[v] for v in PRESET_SCALE_ORDER],
            self._on_preset_segment,
            height=26,
        )
        self.preset_seg.pack(anchor="w", padx=4, pady=(0, 2))
        tighten_segment(self.preset_seg)
        self.preset_seg.set(pmap[PdfSettings.EBOOK.value])
        self.gs_default_check = ctk.CTkCheckBox(
            preset,
            text=gs_default_check_label(self._lang),
            variable=self._gs_default_var,
            command=self._on_gs_default_toggle,
            font=font(11),
            text_color=COLOR["text"],
            fg_color=COLOR["accent"],
            hover_color=COLOR["accent_hover"],
            border_color=COLOR["header"],
            checkmark_color=COLOR["seg_on_text"],
        )
        self.gs_default_check.pack(anchor="w", padx=6, pady=(2, 4))

        help_shell = ctk.CTkFrame(preset, fg_color=COLOR["panel_alt"], corner_radius=6, height=40)
        help_shell.pack(fill="x", padx=6, pady=(0, 6))
        help_shell.pack_propagate(False)
        self.preset_help = ctk.CTkLabel(
            help_shell,
            text="",
            wraplength=RIGHT_HELP_WRAP,
            justify="left",
            anchor="nw",
            font=font(11),
            text_color=COLOR["muted"],
        )
        self.preset_help.pack(fill="both", expand=True, padx=6, pady=4)

        out = self._section(right, "section_output")
        out.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        out_body = ctk.CTkFrame(out, fg_color="transparent")
        out_body.pack(fill="x", padx=6, pady=(0, 4))
        out_body.grid_columnconfigure(1, weight=1)
        label_w = 48

        out_l2v = out_label_to_value(self._lang)
        self.out_label_var = ctk.StringVar(
            value=out_value_to_label(self._lang)[OutputLocation.SAME_AS_SOURCE.value]
        )
        out_loc_lbl = ctk.CTkLabel(
            out_body,
            text=self._t("label_location"),
            text_color=COLOR["muted"],
            width=label_w,
            anchor="w",
            font=font(11),
        )
        out_loc_lbl.grid(row=0, column=0, sticky="w", padx=(0, 4), pady=1)
        self._i18n_labels["label_location"] = out_loc_lbl
        self.out_seg = make_segment(
            out_body,
            list(out_l2v.keys()),
            self._on_out_loc_segment,
            height=26,
        )
        self.out_seg.grid(row=0, column=1, sticky="w", pady=1)
        self.out_seg.set(out_value_to_label(self._lang)[OutputLocation.SAME_AS_SOURCE.value])
        tighten_segment(self.out_seg)

        out_path_lbl = ctk.CTkLabel(
            out_body,
            text=self._t("label_path"),
            text_color=COLOR["muted"],
            width=label_w,
            anchor="w",
            font=font(11),
        )
        out_path_lbl.grid(row=1, column=0, sticky="w", padx=(0, 4), pady=1)
        self._i18n_labels["label_path"] = out_path_lbl
        dir_row = ctk.CTkFrame(out_body, fg_color="transparent")
        dir_row.grid(row=1, column=1, sticky="ew", pady=1)
        dir_row.grid_columnconfigure(0, weight=1)
        self.output_dir_entry = ctk.CTkEntry(
            dir_row,
            placeholder_text=self._t("placeholder_output_dir"),
            height=26,
            fg_color=COLOR["panel_alt"],
            font=font(11),
        )
        self.output_dir_entry.grid(row=0, column=0, sticky="ew")
        self.output_dir_entry.bind("<KeyRelease>", lambda _e: self._on_options_changed())
        self.output_dir_browse = ctk.CTkButton(
            dir_row,
            text="…",
            width=30,
            height=26,
            font=font(11),
            fg_color=COLOR["panel_alt"],
            text_color=COLOR["text"],
            hover_color=COLOR["header"],
            command=self._browse_output_dir,
        )
        self.output_dir_browse.grid(row=0, column=1, padx=(4, 0))
        self._update_output_path_enabled()

        ow_l2v = overwrite_label_to_value(self._lang)
        self.overwrite_label_var = ctk.StringVar(
            value=overwrite_value_to_label(self._lang)[OverwritePolicy.OVERWRITE.value]
        )
        ow_lbl = ctk.CTkLabel(
            out_body,
            text=self._t("label_overwrite"),
            text_color=COLOR["muted"],
            width=label_w,
            anchor="w",
            font=font(11),
        )
        ow_lbl.grid(row=2, column=0, sticky="w", padx=(0, 4), pady=1)
        self._i18n_labels["label_overwrite"] = ow_lbl
        self.overwrite_seg = make_segment(
            out_body,
            list(ow_l2v.keys()),
            self._on_overwrite_segment,
            height=26,
        )
        self.overwrite_seg.grid(row=2, column=1, sticky="w", pady=1)
        self.overwrite_seg.set(self.overwrite_label_var.get())
        tighten_segment(self.overwrite_seg)

        unit = self._section(right, "section_unit")
        unit.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        unit_body = ctk.CTkFrame(unit, fg_color="transparent")
        unit_body.pack(fill="x", padx=6, pady=(0, 4))
        self.img_label_var = ctk.StringVar(
            value=img_value_to_label(self._lang)[ImagePdfMode.ONE_PER_FILE.value]
        )
        unit_lbl = ctk.CTkLabel(
            unit_body,
            text=self._t("label_unit"),
            text_color=COLOR["muted"],
            width=label_w,
            anchor="w",
            font=font(11),
        )
        unit_lbl.grid(row=0, column=0, sticky="w", padx=(0, 4), pady=1)
        self._i18n_labels["label_unit"] = unit_lbl
        self.unit_seg = make_segment(
            unit_body,
            list(img_label_to_value(self._lang).keys()),
            self._on_image_mode_menu,
            height=26,
        )
        self.unit_seg.grid(row=0, column=1, sticky="w", pady=1)
        self.unit_seg.set(self.img_label_var.get())
        tighten_segment(self.unit_seg)

        tools = ctk.CTkFrame(right, fg_color="transparent")
        tools.grid(row=3, column=0, sticky="ew", pady=(0, 4))
        tools.grid_columnconfigure(0, weight=1)
        self.advanced_btn = ctk.CTkButton(
            tools,
            text=self._t("btn_advanced"),
            height=30,
            font=font(12, "bold"),
            fg_color=COLOR["accent"],
            hover_color=COLOR["accent_hover"],
            text_color=COLOR["seg_on_text"],
            command=self._open_advanced,
        )
        self.advanced_btn.grid(row=0, column=0, sticky="ew")
        self.adv_summary = ctk.CTkLabel(
            tools, text="", font=font(10), text_color=COLOR["muted"], anchor="w"
        )
        self.adv_summary.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        action = ctk.CTkFrame(right, fg_color=COLOR["panel"], corner_radius=8)
        action.grid(row=4, column=0, sticky="ew", pady=(0, 4))
        action.grid_columnconfigure((0, 1), weight=1)
        self.convert_btn = ctk.CTkButton(
            action,
            text=self._t("btn_convert"),
            height=34,
            font=font(13, "bold"),
            fg_color=COLOR["cta"],
            hover_color=COLOR["cta_hover"],
            text_color=COLOR["cta_text"],
            command=self._start_convert,
        )
        self.convert_btn.grid(row=0, column=0, sticky="ew", padx=(8, 4), pady=6)
        self.cancel_btn = ctk.CTkButton(
            action,
            text=self._t("btn_cancel"),
            height=34,
            font=font(12),
            state="disabled",
            fg_color=COLOR["stop_disabled"],
            text_color=COLOR["stop_disabled_text"],
            hover_color=COLOR["stop_hover"],
            command=self._cancel_convert,
        )
        self.cancel_btn.grid(row=0, column=1, sticky="ew", padx=(4, 8), pady=6)

        bottom = ctk.CTkFrame(self, fg_color=COLOR["panel"], corner_radius=8)
        self._bottom = bottom
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 8))
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=1)
        log_hdr = ctk.CTkLabel(
            bottom, text=self._t("label_log"), font=font(11, "bold"), text_color=COLOR["muted"], anchor="w"
        )
        log_hdr.grid(row=0, column=0, sticky="w", padx=8, pady=(4, 0))
        self._i18n_labels["label_log"] = log_hdr
        cmd_hdr = ctk.CTkLabel(
            bottom,
            text=self._t("label_command"),
            font=font(11, "bold"),
            text_color=COLOR["muted"],
            anchor="w",
        )
        cmd_hdr.grid(row=0, column=1, sticky="w", padx=8, pady=(4, 0))
        self._i18n_labels["label_command"] = cmd_hdr
        self.log_box = ctk.CTkTextbox(
            bottom, height=64, wrap="word", fg_color=COLOR["panel_alt"], font=font(10)
        )
        self.log_box.grid(row=1, column=0, sticky="ew", padx=(8, 4), pady=(2, 6))
        self.cmd_box = ctk.CTkTextbox(
            bottom, height=64, wrap="word", fg_color=COLOR["panel_alt"], font=font(10)
        )
        self.cmd_box.grid(row=1, column=1, sticky="ew", padx=(4, 8), pady=(2, 6))

        self.compat_var = ctk.StringVar(value=Compatibility.PDF_1_7.value)
        self.color_label_var = ctk.StringVar(
            value=color_value_to_label(self._lang)[ColorMode.KEEP.value]
        )
        self.dpi_var = ctk.StringVar(value="150")
        self.jpeg_var = ctk.IntVar(value=85)
        self.page_range_var = ctk.StringVar(value="")
        self.paper_label_var = ctk.StringVar(
            value=paper_value_to_label(self._lang)[PaperSize.FIT.value]
        )
        self.orient_label_var = ctk.StringVar(
            value=orient_value_to_label(self._lang)[Orientation.AUTO.value]
        )

        self._advanced = AdvancedDialog(
            self,
            get_lang=lambda: self._lang,
            compat_var=self.compat_var,
            color_label_var=self.color_label_var,
            dpi_var=self.dpi_var,
            jpeg_var=self.jpeg_var,
            page_range_var=self.page_range_var,
            paper_label_var=self.paper_label_var,
            orient_label_var=self.orient_label_var,
            on_changed=self._update_adv_summary,
        )

        self._setup_drop_targets()
        self._paint_preset_segment()
        for seg in (self.out_seg, self.overwrite_seg, self.unit_seg):
            paint_segment(seg)

    def _open_advanced(self) -> None:
        if self._advanced is not None:
            self._advanced.open_modal()
            self._on_options_changed()

    def _apply_preset_to_advanced(self, preset_value: str) -> None:
        """Sync 詳細設定 (dpi / JPEG / PDF互換) when a preset is selected."""
        defaults = PRESET_ADVANCED.get(preset_value, PRESET_ADVANCED[PdfSettings.EBOOK.value])
        if self._advanced is not None:
            self._advanced.apply_preset(defaults)
        self._update_adv_summary()

    def _on_preset_segment(self, label: str) -> None:
        value = self._preset_label_to_value().get(label, PdfSettings.EBOOK.value)
        self._gs_default_var.set(False)
        self._last_scale_preset = value
        self.preset_var.set(value)
        self.preset_seg.configure(state="normal")
        self._paint_preset_segment()
        self._apply_preset_to_advanced(value)
        self._update_preset_help()
        self._on_options_changed()

    def _on_gs_default_toggle(self) -> None:
        if self._gs_default_var.get():
            current = self._preset_label_to_value().get(
                self.preset_seg.get(), PdfSettings.EBOOK.value
            )
            if current in PRESET_SCALE_ORDER:
                self._last_scale_preset = current
            self.preset_var.set(PdfSettings.DEFAULT.value)
            self.preset_seg.configure(state="disabled")
            self._paint_preset_segment()
            self._apply_preset_to_advanced(PdfSettings.DEFAULT.value)
        else:
            value = getattr(self, "_last_scale_preset", PdfSettings.EBOOK.value)
            if value not in PRESET_SCALE_ORDER:
                value = PdfSettings.EBOOK.value
            self.preset_var.set(value)
            self.preset_seg.configure(state="normal")
            self._paint_preset_segment()
            self._apply_preset_to_advanced(value)
        self._update_preset_help()
        self._on_options_changed()

    def _on_image_mode_menu(self, label: str) -> None:
        self.img_label_var.set(label)
        paint_segment(self.unit_seg)
        self._on_options_changed()

    def _update_output_path_enabled(self) -> None:
        custom = (
            out_label_to_value(self._lang).get(self.out_label_var.get())
            == OutputLocation.CUSTOM.value
        )
        if custom:
            self.output_dir_entry.configure(
                state="normal",
                fg_color=COLOR["panel_alt"],
                border_color=COLOR["header"],
                text_color=COLOR["text"],
                placeholder_text_color=COLOR["muted"],
            )
            self.output_dir_browse.configure(
                state="normal",
                fg_color=COLOR["panel_alt"],
                text_color=COLOR["text"],
                hover_color=COLOR["header"],
            )
        else:
            self.output_dir_entry.configure(
                state="disabled",
                fg_color=COLOR["stop_disabled"],
                border_color=COLOR["stop_disabled"],
                text_color=COLOR["stop_disabled_text"],
                placeholder_text_color=COLOR["stop_disabled_text"],
            )
            self.output_dir_browse.configure(
                state="disabled",
                fg_color=COLOR["stop_disabled"],
                text_color=COLOR["stop_disabled_text"],
                hover_color=COLOR["stop_disabled"],
            )

    def _on_out_loc_segment(self, label: str) -> None:
        self.out_label_var.set(label)
        paint_segment(self.out_seg)
        self._update_output_path_enabled()
        self._on_options_changed()

    def _on_overwrite_segment(self, label: str) -> None:
        self.overwrite_label_var.set(label)
        paint_segment(self.overwrite_seg)
        self._on_options_changed()

    def _update_preset_help(self) -> None:
        value = self.preset_var.get()
        info = preset_info(self._lang)
        _label, help_text = info.get(value, ("", self._t("preset_help_fallback")))
        self.preset_help.configure(text=help_text)
        self._update_adv_summary()

    def _update_adv_summary(self) -> None:
        self.adv_summary.configure(
            text=(
                f"{self.compat_var.get()} · {self.color_label_var.get()} · "
                f"{self.dpi_var.get()}dpi · Q{int(self.jpeg_var.get())}"
            )
        )

    def _apply_settings_to_ui(self) -> None:
        s = self.settings
        self._set_language(parse_lang(s.ui_language), persist=False)
        self.preset_var.set(s.pdf_settings)
        if s.last_scale_preset in PRESET_SCALE_ORDER:
            self._last_scale_preset = s.last_scale_preset
        elif s.pdf_settings in PRESET_SCALE_ORDER:
            self._last_scale_preset = s.pdf_settings
        else:
            self._last_scale_preset = PdfSettings.EBOOK.value
        if s.pdf_settings == PdfSettings.DEFAULT.value:
            self._gs_default_var.set(True)
            self.preset_seg.configure(state="disabled")
            self._paint_preset_segment()
        else:
            self._gs_default_var.set(False)
            self.preset_seg.configure(state="normal")
            self._paint_preset_segment()
        lang = self._lang
        cv2l = color_value_to_label(lang)
        self.compat_var.set(s.compatibility)
        self.color_label_var.set(cv2l.get(s.color_mode, cv2l[ColorMode.KEEP.value]))
        self.dpi_var.set(str(s.resolution_dpi))
        self.jpeg_var.set(s.jpeg_quality)
        self.page_range_var.set(s.page_range)
        pv2l = paper_value_to_label(lang)
        self.paper_label_var.set(pv2l.get(s.paper_size, pv2l[PaperSize.FIT.value]))
        ov2l = orient_value_to_label(lang)
        self.orient_label_var.set(ov2l.get(s.orientation, ov2l[Orientation.AUTO.value]))
        iv2l = img_value_to_label(lang)
        self.img_label_var.set(iv2l.get(s.image_pdf_mode, iv2l[ImagePdfMode.ONE_PER_FILE.value]))
        self.unit_seg.set(self.img_label_var.get())
        out_v2l = out_value_to_label(lang)
        self.out_label_var.set(
            out_v2l.get(s.output_location, out_v2l[OutputLocation.SAME_AS_SOURCE.value])
        )
        self.out_seg.set(self.out_label_var.get())
        self.output_dir_entry.configure(state="normal")
        self.output_dir_entry.delete(0, "end")
        self.output_dir_entry.insert(0, s.custom_output_dir)
        self._update_output_path_enabled()
        ow_v2l = overwrite_value_to_label(lang)
        self.overwrite_label_var.set(
            ow_v2l.get(s.overwrite_policy, ow_v2l[OverwritePolicy.OVERWRITE.value])
        )
        self.overwrite_seg.set(self.overwrite_label_var.get())
        for seg in (self.out_seg, self.overwrite_seg, self.unit_seg):
            paint_segment(seg)
        self._update_preset_help()

    def _current_options(self) -> ConversionOptions:
        try:
            dpi = int(self.dpi_var.get().strip())
        except ValueError:
            dpi = 150
        dpi = max(1, min(dpi, 2400))
        return ConversionOptions(
            pdf_settings=PdfSettings(self.preset_var.get()),
            compatibility=Compatibility(self.compat_var.get()),
            color_mode=ColorMode(
                color_label_to_value(self._lang).get(
                    self.color_label_var.get(), ColorMode.KEEP.value
                )
            ),
            resolution_dpi=dpi,
            jpeg_quality=int(self.jpeg_var.get()),
            page_range=self.page_range_var.get().strip(),
            paper_size=PaperSize(
                paper_label_to_value(self._lang).get(
                    self.paper_label_var.get(), PaperSize.FIT.value
                )
            ),
            orientation=Orientation(
                orient_label_to_value(self._lang).get(
                    self.orient_label_var.get(), Orientation.AUTO.value
                )
            ),
            image_pdf_mode=ImagePdfMode(
                img_label_to_value(self._lang).get(
                    self.img_label_var.get(), ImagePdfMode.ONE_PER_FILE.value
                )
            ),
            output_location=OutputLocation(
                out_label_to_value(self._lang).get(
                    self.out_label_var.get(), OutputLocation.SAME_AS_SOURCE.value
                )
            ),
            custom_output_dir=self.output_dir_entry.get().strip(),
            overwrite_policy=OverwritePolicy(
                overwrite_label_to_value(self._lang).get(
                    self.overwrite_label_var.get(), OverwritePolicy.OVERWRITE.value
                )
            ),
        )

    def _persist_settings(self) -> None:
        options = self._current_options()
        gs = str(self.gs_path) if self.gs_path else self.settings.ghostscript_path
        last_scale = self._last_scale_preset
        if last_scale not in PRESET_SCALE_ORDER:
            last_scale = PdfSettings.EBOOK.value
        self.settings = AppSettings.from_options(
            options,
            ghostscript_path=gs,
            window_geometry=self._capture_window_geometry(),
            last_scale_preset=last_scale,
            ui_language=self._lang.value,
        )
        save_settings(self.settings)

    def _schedule_persist(self) -> None:
        if self._persist_after_id is not None:
            try:
                self.after_cancel(self._persist_after_id)
            except tk.TclError:
                pass
        self._persist_after_id = self.after(400, self._flush_persist)

    def _flush_persist(self) -> None:
        self._persist_after_id = None
        self._persist_settings()

    def _on_options_changed(self) -> None:
        self._update_adv_summary()
        self._update_command_preview()
        self._schedule_persist()

    def _refresh_gs_label(self) -> None:
        if self.gs_path and self.gs_path.is_file():
            name = nfc(self.gs_path.name)
            self.gs_status.configure(
                text=self._t("gs_found", name=name), text_color=COLOR["success"]
            )
        else:
            self.gs_status.configure(text=self._t("gs_missing"), text_color=COLOR["danger"])

    def _browse_gs(self) -> None:
        path = filedialog.askopenfilename(
            title=self._t("browse_gs_title"),
            filetypes=[("Executable", "*.exe"), ("All", "*.*")],
        )
        if path:
            self.gs_path = normalize_path(Path(path))
            self.settings.ghostscript_path = str(self.gs_path)
            save_settings(self.settings)
            self._refresh_gs_label()
            self._update_command_preview()

    def _browse_output_dir(self) -> None:
        path = filedialog.askdirectory(title=self._t("browse_out_title"))
        if path:
            custom_label = out_value_to_label(self._lang)[OutputLocation.CUSTOM.value]
            self.output_dir_entry.configure(state="normal")
            self.output_dir_entry.delete(0, "end")
            self.output_dir_entry.insert(0, nfc(path))
            self.out_label_var.set(custom_label)
            self.out_seg.set(custom_label)
            paint_segment(self.out_seg)
            self._update_output_path_enabled()
            self._on_options_changed()

    def _register_drop_target(self, widget) -> None:  # noqa: ANN001
        """Register DnD on a widget and CTk internals (canvas / children)."""
        try:
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self._on_drop)
        except (tk.TclError, AttributeError):
            pass
        canvas = getattr(widget, "_canvas", None)
        if canvas is not None:
            try:
                canvas.drop_target_register(DND_FILES)
                canvas.dnd_bind("<<Drop>>", self._on_drop)
            except (tk.TclError, AttributeError):
                pass
        try:
            children = widget.winfo_children()
        except tk.TclError:
            children = []
        for child in children:
            self._register_drop_target(child)

    def _setup_drop_targets(self) -> None:
        # Only the window and the drop-zone subtree (avoid duplicate Drop events)
        try:
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)
        except (tk.TclError, AttributeError):
            pass
        self._register_drop_target(self.drop_frame)
        self.after(120, lambda: self._register_drop_target(self.drop_frame))

    def _on_drop(self, event) -> None:  # noqa: ANN001
        data = getattr(event, "data", None)
        if data is None:
            data = ""
        elif isinstance(data, (bytes, bytearray)):
            data = data.decode("utf-8", errors="surrogateescape")
        else:
            data = str(data)

        # Ignore empty / duplicate Drop events from nested DnD targets
        key = data.strip()
        now = time.monotonic()
        if not key:
            return
        if key == self._last_drop_key and (now - self._last_drop_at) < 0.4:
            return
        self._last_drop_key = key
        self._last_drop_at = now

        paths = parse_drop_paths(data, splitlist=self.tk.splitlist)
        if not paths:
            self._log(self._t("log_drop_fail", data=data))
            messagebox.showinfo("GSGui", self._t("msg_drop_unparsed"))
            return
        self._add_paths(paths)

    def _add_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title=self._t("add_files_title"),
            filetypes=[
                ("Supported", "*.pdf;*.ps;*.eps;*.jpg;*.jpeg;*.png;*.tif;*.tiff"),
                ("All", "*.*"),
            ],
        )
        if paths:
            self._add_paths([normalize_path(Path(coerce_path_string(p) or p)) for p in paths])

    def _add_paths(self, paths: list[Path]) -> None:
        files = collect_files(paths)
        if not files:
            detail = ""
            if paths:
                detail = "\n".join(str(p) for p in paths[:5])
                self._log(self._t("log_unrecognized", detail=detail))
            messagebox.showinfo(
                "GSGui",
                self._t("msg_no_supported")
                + (self._t("msg_received_paths", detail=detail) if detail else ""),
            )
            return
        existing = {i.path.resolve() for i in self.queue}
        added = 0
        for path in files:
            if path.resolve() in existing:
                continue
            item = build_queue_item(path, lang=self._lang)
            if item.kind == FileKind.UNKNOWN:
                continue
            self.queue.append(item)
            added += 1
        self._log(self._t("log_added", n=added))
        self._refresh_queue_view()
        self._update_command_preview()
        self._schedule_pdf_meta_enrichment()

    def _remove_selected(self) -> None:
        if self.selected_index is None or not (0 <= self.selected_index < len(self.queue)):
            return
        del self.queue[self.selected_index]
        self.selected_index = None
        self._refresh_queue_view()
        self._update_command_preview()

    def _clear_queue(self) -> None:
        self.queue.clear()
        self.selected_index = None
        self._refresh_queue_view()
        self._update_command_preview()

    def _select_row(self, index: int) -> None:
        self.selected_index = index
        for i, widgets in enumerate(self._row_widgets):
            paint_queue_row_selection(widgets, selected=(i == index))

    def _queue_name_wraplength(self) -> int:
        return queue_name_wraplength(self.queue_scroll.winfo_width())

    def _on_queue_configure(self, _event=None) -> None:  # noqa: ANN001
        wrap = self._queue_name_wraplength()
        for label in getattr(self, "_name_labels", []):
            try:
                if label.winfo_exists():
                    label.configure(wraplength=wrap)
            except tk.TclError:
                pass

    def _refresh_queue_view(self) -> None:
        for child in self.queue_scroll.winfo_children():
            child.destroy()
        self._row_widgets.clear()
        self._name_labels = []

        build_queue_header(self.queue_scroll, self._lang)
        if not self.queue:
            build_queue_empty_label(self.queue_scroll, self._lang)
            return

        name_wrap = self._queue_name_wraplength()
        for idx, item in enumerate(self.queue):
            widgets = build_queue_row(
                self.queue_scroll,
                lang=self._lang,
                index=idx,
                item=item,
                selected=idx == self.selected_index,
                name_wrap=name_wrap,
                on_select=self._select_row,
                on_open_folder=self._open_item_folder,
                on_open_pdf=self._open_item_pdf,
            )
            self._name_labels.append(widgets["name"])
            self._row_widgets.append(widgets)

    def _apply_row_data(self, widgets: dict, item: QueueItem) -> None:
        apply_queue_row_data(widgets, item, self._lang)

    def _schedule_pdf_meta_enrichment(self) -> None:
        """Fill PDF page counts off the UI thread after bulk add."""
        pdf_meta = self._t("meta_pdf")
        targets = [item for item in self.queue if item.kind == FileKind.PDF and item.meta == pdf_meta]
        if not targets:
            return
        gs_path = self.gs_path

        def work() -> None:
            updates: list[tuple[QueueItem, str]] = []
            for item in targets:
                meta = enrich_pdf_meta(item, gs_path, lang=self._lang)
                if meta:
                    updates.append((item, meta))
            if updates:
                self.after(0, lambda: self._apply_pdf_meta_updates(updates))

        threading.Thread(target=work, daemon=True).start()

    def _apply_pdf_meta_updates(self, updates: list[tuple[QueueItem, str]]) -> None:
        changed = False
        for item, meta in updates:
            if item not in self.queue:
                continue
            if item.meta != meta:
                item.meta = meta
                changed = True
        if not changed:
            return
        by_id = {id(w["item"]): w for w in self._row_widgets}
        for item, _meta in updates:
            widgets = by_id.get(id(item))
            if widgets is not None:
                self._apply_row_data(widgets, item)

    def _update_command_preview(self) -> None:
        self.cmd_box.delete("1.0", "end")
        if not self.gs_path:
            self.cmd_box.insert("1.0", self._t("cmd_no_gs"))
            return
        if not self.queue:
            self.cmd_box.insert("1.0", self._t("cmd_empty_queue"))
            return

        options = self._current_options()

        lines: list[str] = []
        sample = self.queue[0]
        if sample.kind in (FileKind.PDF, FileKind.POSTSCRIPT):
            out = resolve_output_path(sample.path, options, create_dirs=False)
            cmd = build_pdf_or_ps_command(self.gs_path, sample, out, options)
            lines.append(format_gs_command(cmd))
        elif sample.kind == FileKind.IMAGE:
            images = [i for i in self.queue if i.kind == FileKind.IMAGE]
            subset = (
                images[:3] if options.image_pdf_mode == ImagePdfMode.ONE_PER_FILE else images
            )
            jobs = build_image_commands(self.gs_path, subset, options, create_dirs=False)
            for _items, _out, cmd in jobs[:2]:
                lines.append(format_gs_command(cmd))
        self.cmd_box.insert("1.0", "\n\n".join(lines) if lines else self._t("cmd_no_preview"))

    def _log(self, text: str) -> None:
        def append() -> None:
            self.log_box.insert("end", nfc(text) + "\n")
            self.log_box.see("end")

        self.after(0, append)

    def _start_convert(self) -> None:
        if self.worker is not None:
            return
        if not self.gs_path or not self.gs_path.is_file():
            messagebox.showerror(
                "GSGui",
                self._t("err_no_gs", button=self._t("gs_path_button")),
            )
            return
        if not self.queue:
            messagebox.showinfo("GSGui", self._t("err_empty_queue"))
            return

        options = self._current_options()
        if not validate_page_range(options.page_range):
            messagebox.showerror("GSGui", self._t("err_page_range"))
            return
        if options.output_location == OutputLocation.CUSTOM and not options.custom_output_dir.strip():
            messagebox.showerror("GSGui", self._t("err_need_outdir"))
            return

        self._persist_settings()
        for item in self.queue:
            item.status = JobStatus.PENDING
            item.message = ""
            item.output_path = None
            item.output_size_bytes = None
            item.command = []

        self.convert_btn.configure(state="disabled")
        self.cancel_btn.configure(
            state="normal",
            fg_color=COLOR["stop"],
            text_color=COLOR["stop_text"],
            hover_color=COLOR["stop_hover"],
        )
        self._log(self._t("log_convert_start"))

        self.worker = ConversionWorker(
            gs_path=self.gs_path,
            items=list(self.queue),
            options=options,
            on_item_update=lambda item: self.after(0, lambda: self._on_item_update(item)),
            on_log=lambda msg: self._log(msg),
            on_done=lambda: self.after(0, self._on_convert_done),
            lang=self._lang,
        )
        self.worker.start()
        self._refresh_queue_view()

    def _on_item_update(self, item: QueueItem) -> None:
        for widgets in self._row_widgets:
            if widgets.get("item") is item:
                self._apply_row_data(widgets, item)
                return
        self._refresh_queue_view()

    def _cancel_convert(self) -> None:
        if self.worker:
            self.worker.cancel()
            self._log(self._t("log_cancel_requested"))

    def _on_convert_done(self) -> None:
        self.worker = None
        self.convert_btn.configure(state="normal")
        self.cancel_btn.configure(
            state="disabled",
            fg_color=COLOR["stop_disabled"],
            text_color=COLOR["stop_disabled_text"],
        )
        self._refresh_queue_view()
        self._log(self._t("log_convert_end"))
        ok = sum(1 for i in self.queue if i.status == JobStatus.SUCCESS)
        ng = sum(1 for i in self.queue if i.status == JobStatus.FAILED)
        messagebox.showinfo("GSGui", self._t("msg_done", ok=ok, ng=ng))

    def _open_item_folder(self, item: QueueItem) -> None:
        if not item.output_path:
            messagebox.showinfo("GSGui", self._t("msg_no_out_file"))
            return
        folder = item.output_path.parent
        if sys.platform == "win32":
            # Select the file in Explorer when possible
            try:
                subprocess.run(
                    ["explorer", "/select,", str(item.output_path.resolve())],
                    check=False,
                )
                return
            except OSError:
                pass
            os.startfile(folder)  # noqa: S606
        else:
            subprocess.run(["xdg-open", str(folder)], check=False)

    def _open_item_pdf(self, item: QueueItem) -> None:
        if not item.output_path or not item.output_path.exists():
            messagebox.showinfo("GSGui", self._t("msg_no_out_pdf"))
            return
        if sys.platform == "win32":
            os.startfile(item.output_path)  # noqa: S606
        else:
            subprocess.run(["xdg-open", str(item.output_path)], check=False)

    def on_closing(self) -> None:
        if self._advanced is not None and self._advanced.is_open:
            self._advanced.close()
        if self._persist_after_id is not None:
            try:
                self.after_cancel(self._persist_after_id)
            except tk.TclError:
                pass
            self._persist_after_id = None
        self._persist_settings()
        if self.worker:
            self.worker.cancel()
        self.destroy()


def main() -> None:
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
