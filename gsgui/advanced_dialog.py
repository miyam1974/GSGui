"""Advanced settings modal dialog."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from gsgui.i18n import Lang, t
from gsgui.labels import (
    DPI_PRESETS,
    color_label_to_value,
    orient_label_to_value,
    paper_label_to_value,
)
from gsgui.models import Compatibility
from gsgui.presets import PresetAdvancedDefaults
from gsgui.segment_style import make_segment, paint_segment, paint_segment_none
from gsgui.theme import (
    ADVANCED_HELP_WRAP,
    ADVANCED_LABEL_WIDTH,
    COLOR,
    font,
)


MODAL_DIM_COLOR = ("#1A2330", "#0B0F14")


def centered_geometry(parent: Any, width: int | None = None, height: int | None = None) -> str:
    """Return ``WxH+X+Y`` centered over *parent*."""
    from gsgui.theme import ADVANCED_DIALOG_HEIGHT, ADVANCED_DIALOG_WIDTH

    ww = ADVANCED_DIALOG_WIDTH if width is None else width
    wh = ADVANCED_DIALOG_HEIGHT if height is None else height
    parent.update_idletasks()
    px, py = parent.winfo_rootx(), parent.winfo_rooty()
    pw, ph = parent.winfo_width(), parent.winfo_height()
    return f"{ww}x{wh}+{px + (pw - ww) // 2}+{py + (ph - wh) // 2}"


def reset_entry_placeholder(entry: ctk.CTkEntry) -> None:
    """Clear entry text and restore CTk placeholder (textvariable-free entries only).

    Touches CTk private fields (``_entry``, ``_placeholder_text_active``, …);
    keep all such Entry tweaks here beside the advanced dialog.
    """
    entry._entry.delete(0, "end")  # noqa: SLF001
    entry._placeholder_text_active = False  # noqa: SLF001
    entry._is_focused = False  # noqa: SLF001
    entry._activate_placeholder()  # noqa: SLF001


class AdvancedDialog:
    """Modal advanced settings. Mutates the shared StringVars / IntVar owned by App."""

    def __init__(
        self,
        parent: ctk.CTk,
        *,
        get_lang: Callable[[], Lang],
        compat_var: ctk.StringVar,
        color_label_var: ctk.StringVar,
        dpi_var: ctk.StringVar,
        jpeg_var: ctk.IntVar,
        page_range_var: ctk.StringVar,
        paper_label_var: ctk.StringVar,
        orient_label_var: ctk.StringVar,
        on_changed: Callable[[], None],
    ) -> None:
        self._parent = parent
        self._get_lang = get_lang
        self.compat_var = compat_var
        self.color_label_var = color_label_var
        self.dpi_var = dpi_var
        self.jpeg_var = jpeg_var
        self.page_range_var = page_range_var
        self.paper_label_var = paper_label_var
        self.orient_label_var = orient_label_var
        self._on_changed = on_changed

        self._open = False
        self._window: ctk.CTkToplevel | None = None
        self._dim: ctk.CTkFrame | None = None
        self._compat_seg: ctk.CTkSegmentedButton | None = None
        self._color_seg: ctk.CTkSegmentedButton | None = None
        self._paper_seg: ctk.CTkSegmentedButton | None = None
        self._orient_seg: ctk.CTkSegmentedButton | None = None
        self._dpi_seg: ctk.CTkSegmentedButton | None = None
        self._dpi_entry: ctk.CTkEntry | None = None
        self._page_entry: ctk.CTkEntry | None = None
        self._jpeg_label: ctk.CTkLabel | None = None

    @property
    def is_open(self) -> bool:
        return self._open

    def open_modal(self) -> None:
        if self._open:
            return
        self._open = True
        lang = self._get_lang()

        self._dim = ctk.CTkFrame(self._parent, fg_color=MODAL_DIM_COLOR, corner_radius=0)
        self._dim.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._dim.lift()

        win = ctk.CTkToplevel(self._parent)
        win.title(t(lang, "dialog_advanced_title"))
        win.geometry(centered_geometry(self._parent))
        win.resizable(False, False)
        win.transient(self._parent)
        win.configure(fg_color=COLOR["bg"])
        win.protocol("WM_DELETE_WINDOW", self.close)
        self._window = win

        body = ctk.CTkFrame(win, fg_color=COLOR["panel"], corner_radius=12)
        body.pack(fill="both", expand=True, padx=14, pady=14)
        body.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            body,
            text=t(lang, "dialog_advanced_title"),
            font=font(16, "bold"),
            text_color=COLOR["text"],
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 8))

        def row(r: int, label: str, widget) -> None:  # noqa: ANN001
            ctk.CTkLabel(
                body,
                text=label,
                text_color=COLOR["muted"],
                anchor="w",
                width=ADVANCED_LABEL_WIDTH,
                font=font(12),
            ).grid(row=r, column=0, sticky="w", padx=12, pady=8)
            widget.grid(row=r, column=1, sticky="ew", padx=12, pady=8)

        compat_seg = make_segment(body, [c.value for c in Compatibility], self._on_compat)
        compat_seg.set(self.compat_var.get())
        paint_segment(compat_seg)
        self._compat_seg = compat_seg
        row(1, t(lang, "adv_compat"), compat_seg)

        color_map = color_label_to_value(lang)
        color_seg = make_segment(body, list(color_map.keys()), self._on_color)
        color_seg.set(self.color_label_var.get())
        paint_segment(color_seg)
        self._color_seg = color_seg
        row(2, t(lang, "adv_color"), color_seg)

        dpi_row = ctk.CTkFrame(body, fg_color="transparent")
        dpi_presets = list(DPI_PRESETS)
        self._dpi_seg = make_segment(dpi_row, dpi_presets, self._on_dpi_segment)
        current_dpi = self.dpi_var.get().strip()
        if current_dpi in dpi_presets:
            self._dpi_seg.set(current_dpi)
            paint_segment(self._dpi_seg)
            custom_dpi = ""
        else:
            paint_segment_none(self._dpi_seg)
            custom_dpi = current_dpi
        self._dpi_seg.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            dpi_row,
            text=t(lang, "adv_dpi_other"),
            text_color=COLOR["muted"],
            font=font(11),
            width=36,
        ).pack(side="left", padx=(10, 2))
        self._dpi_entry = ctk.CTkEntry(
            dpi_row,
            width=72,
            font=font(12),
            fg_color=COLOR["panel_alt"],
            border_color=COLOR["drop_border"],
            placeholder_text=t(lang, "adv_dpi_placeholder"),
            placeholder_text_color=COLOR["muted"],
        )
        if custom_dpi:
            self._dpi_entry.insert(0, custom_dpi)
        self._dpi_entry.pack(side="left")
        self._dpi_entry.bind("<KeyRelease>", lambda _e: self._on_dpi_typed())
        row(3, t(lang, "adv_dpi"), dpi_row)

        jpeg_row = ctk.CTkFrame(body, fg_color="transparent")
        ctk.CTkSlider(
            jpeg_row,
            from_=1,
            to=100,
            number_of_steps=99,
            variable=self.jpeg_var,
            command=lambda _v: self._on_jpeg(),
            progress_color=COLOR["accent"],
            button_color=COLOR["accent"],
        ).pack(side="left", fill="x", expand=True)
        self._jpeg_label = ctk.CTkLabel(
            jpeg_row, text=str(int(self.jpeg_var.get())), width=36, font=font(12)
        )
        self._jpeg_label.pack(side="left", padx=4)
        row(4, t(lang, "adv_jpeg"), jpeg_row)

        self._page_entry = ctk.CTkEntry(
            body,
            placeholder_text=t(lang, "adv_pages_placeholder"),
            placeholder_text_color=COLOR["muted"],
            fg_color=COLOR["panel_alt"],
            font=font(12),
        )
        if self.page_range_var.get().strip():
            self._page_entry.insert(0, self.page_range_var.get().strip())
        self._page_entry.bind(
            "<KeyRelease>",
            lambda _e: self.page_range_var.set(self._page_entry.get().strip()) if self._page_entry else None,
        )
        row(5, t(lang, "adv_pages"), self._page_entry)

        paper_map = paper_label_to_value(lang)
        paper_seg = make_segment(body, list(paper_map.keys()), self._on_paper)
        paper_seg.set(self.paper_label_var.get())
        paint_segment(paper_seg)
        self._paper_seg = paper_seg
        row(6, t(lang, "adv_paper"), paper_seg)

        orient_map = orient_label_to_value(lang)
        orient_seg = make_segment(body, list(orient_map.keys()), self._on_orient)
        orient_seg.set(self.orient_label_var.get())
        paint_segment(orient_seg)
        self._orient_seg = orient_seg
        row(7, t(lang, "adv_orient"), orient_seg)

        ctk.CTkLabel(
            body,
            text=t(lang, "adv_help"),
            wraplength=ADVANCED_HELP_WRAP,
            justify="left",
            font=font(11),
            text_color=COLOR["muted"],
        ).grid(row=8, column=0, columnspan=2, sticky="w", padx=12, pady=(4, 8))

        ctk.CTkButton(
            body,
            text=t(lang, "adv_ok"),
            font=font(13, "bold"),
            fg_color=COLOR["cta"],
            hover_color=COLOR["cta_hover"],
            text_color=COLOR["cta_text"],
            command=self.close,
        ).grid(row=9, column=0, columnspan=2, pady=(8, 14), padx=12, sticky="ew")

        win.update_idletasks()
        win.grab_set()
        win.focus_force()
        win.lift()
        self._parent.wait_window(win)

    def close(self) -> None:
        self._sync_entries()
        if self._window is not None and self._window.winfo_exists():
            try:
                self._window.grab_release()
            except tk.TclError:
                pass
            self._window.destroy()
        self._window = None
        if self._dim is not None and self._dim.winfo_exists():
            self._dim.destroy()
        self._dim = None
        self._open = False
        self._compat_seg = None
        self._color_seg = None
        self._paper_seg = None
        self._orient_seg = None
        self._dpi_seg = None
        self._dpi_entry = None
        self._page_entry = None
        self._jpeg_label = None
        self._on_changed()

    def apply_preset(self, defaults: PresetAdvancedDefaults) -> None:
        """Push preset defaults into vars and refresh open widgets."""
        self.dpi_var.set(str(defaults.resolution_dpi))
        self.jpeg_var.set(defaults.jpeg_quality)
        self.compat_var.set(defaults.compatibility)
        if not self._open:
            return
        if self._dpi_seg is not None and self._dpi_seg.winfo_exists():
            dpi = str(defaults.resolution_dpi)
            if dpi in DPI_PRESETS:
                self._dpi_seg.set(dpi)
                paint_segment(self._dpi_seg)
                if self._dpi_entry is not None and self._dpi_entry.winfo_exists():
                    reset_entry_placeholder(self._dpi_entry)
            else:
                paint_segment_none(self._dpi_seg)
                if self._dpi_entry is not None and self._dpi_entry.winfo_exists():
                    self._dpi_entry.delete(0, "end")
                    self._dpi_entry.insert(0, dpi)
        if self._compat_seg is not None and self._compat_seg.winfo_exists():
            self._compat_seg.set(defaults.compatibility)
            paint_segment(self._compat_seg)
        if self._jpeg_label is not None:
            try:
                if self._jpeg_label.winfo_exists():
                    self._jpeg_label.configure(text=str(defaults.jpeg_quality))
            except tk.TclError:
                pass

    def _sync_entries(self) -> None:
        page = self._page_entry
        if page is not None and page.winfo_exists():
            self.page_range_var.set(page.get().strip())
        dpi = self._dpi_entry
        if dpi is not None and dpi.winfo_exists():
            custom = dpi.get().strip()
            if custom:
                self.dpi_var.set(custom)

    def _on_compat(self, value: str) -> None:
        self.compat_var.set(value)
        if self._compat_seg is not None:
            paint_segment(self._compat_seg)
        self._on_changed()

    def _on_color(self, label: str) -> None:
        self.color_label_var.set(label)
        if self._color_seg is not None:
            paint_segment(self._color_seg)
        self._on_changed()

    def _on_paper(self, label: str) -> None:
        self.paper_label_var.set(label)
        if self._paper_seg is not None:
            paint_segment(self._paper_seg)
        self._on_changed()

    def _on_orient(self, label: str) -> None:
        self.orient_label_var.set(label)
        if self._orient_seg is not None:
            paint_segment(self._orient_seg)
        self._on_changed()

    def _on_jpeg(self) -> None:
        if self._jpeg_label is not None and self._jpeg_label.winfo_exists():
            self._jpeg_label.configure(text=str(int(self.jpeg_var.get())))
        self._on_changed()

    def _on_dpi_segment(self, value: str) -> None:
        self.dpi_var.set(value)
        if self._dpi_entry is not None and self._dpi_entry.winfo_exists():
            reset_entry_placeholder(self._dpi_entry)
        if self._dpi_seg is not None:
            paint_segment(self._dpi_seg)
        self._on_changed()

    def _on_dpi_typed(self) -> None:
        entry = self._dpi_entry
        if entry is None or not entry.winfo_exists():
            self._on_changed()
            return
        value = entry.get().strip()
        if not value:
            if self._dpi_seg is not None:
                selected = self._dpi_seg.get()
                if selected in DPI_PRESETS:
                    self.dpi_var.set(selected)
                    paint_segment(self._dpi_seg)
            self._on_changed()
            return
        self.dpi_var.set(value)
        if self._dpi_seg is None:
            self._on_changed()
            return
        if value in DPI_PRESETS:
            self._dpi_seg.set(value)
            reset_entry_placeholder(entry)
            paint_segment(self._dpi_seg)
        else:
            paint_segment_none(self._dpi_seg)
        self._on_changed()
