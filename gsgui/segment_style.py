"""CTkSegmentedButton styling helpers.

CTk private attributes (``_buttons_dict``, ``_text_label``) are accessed only here.
"""

from __future__ import annotations

import tkinter as tk
from typing import Any

import customtkinter as ctk

from gsgui.theme import COLOR, font


def _segment_buttons(seg: ctk.CTkSegmentedButton) -> dict[str, Any]:
    """CTk private: map of value → chip button."""
    raw = getattr(seg, "_buttons_dict", None)
    return raw if isinstance(raw, dict) else {}


def _button_text_label(btn: Any) -> Any | None:
    """CTk private: inner label used for chip padding tweaks."""
    return getattr(btn, "_text_label", None)


def paint_segment(seg: ctk.CTkSegmentedButton) -> None:
    """Selected chip: white on deep blue. Others: dark text on light chip."""
    current = seg.get()
    for value, btn in _segment_buttons(seg).items():
        if value == current:
            btn.configure(
                fg_color=COLOR["accent"],
                hover_color=COLOR["accent_hover"],
                text_color=COLOR["seg_on_text"],
            )
        else:
            btn.configure(
                fg_color=COLOR["panel_alt"],
                hover_color=COLOR["header"],
                text_color=COLOR["seg_off_text"],
            )


def paint_segment_none(seg: ctk.CTkSegmentedButton) -> None:
    """Show all chips unselected."""
    for btn in _segment_buttons(seg).values():
        btn.configure(
            fg_color=COLOR["panel_alt"],
            hover_color=COLOR["header"],
            text_color=COLOR["seg_off_text"],
        )


def tighten_segment(seg: ctk.CTkSegmentedButton) -> None:
    """Size chips to label width instead of stretching across the pane."""
    for btn in _segment_buttons(seg).values():
        btn.configure(width=1)
        label = _button_text_label(btn)
        if label is not None:
            label.grid_configure(padx=4)


def make_segment(
    parent: ctk.CTkFrame | ctk.CTkToplevel,
    values: list[str],
    command,  # noqa: ANN001
    *,
    height: int = 28,
    font_size: int = 11,
) -> ctk.CTkSegmentedButton:
    return ctk.CTkSegmentedButton(
        parent,
        values=values,
        command=command,
        height=height,
        font=font(font_size),
        selected_color=COLOR["accent"],
        selected_hover_color=COLOR["accent_hover"],
        unselected_color=COLOR["panel_alt"],
        unselected_hover_color=COLOR["header"],
        text_color=COLOR["seg_off_text"],
    )


def paint_preset_segment(
    seg: ctk.CTkSegmentedButton,
    *,
    last_scale_label: str,
    gs_default_on: bool,
) -> None:
    """Paint scale chips; when GS既定 is on, keep last selection visible but muted."""
    try:
        seg.set(last_scale_label)
    except tk.TclError:
        pass
    current = seg.get()
    for value, btn in _segment_buttons(seg).items():
        if value == current:
            if gs_default_on:
                btn.configure(
                    fg_color=COLOR["seg_muted_on"],
                    hover_color=COLOR["seg_muted_on"],
                    text_color=COLOR["seg_muted_on_text"],
                    text_color_disabled=COLOR["seg_muted_on_text"],
                )
            else:
                btn.configure(
                    fg_color=COLOR["accent"],
                    hover_color=COLOR["accent_hover"],
                    text_color=COLOR["seg_on_text"],
                    text_color_disabled=COLOR["seg_on_text"],
                )
        else:
            btn.configure(
                fg_color=COLOR["panel_alt"] if not gs_default_on else COLOR["seg_muted_off"],
                hover_color=COLOR["header"],
                text_color=COLOR["seg_off_text"] if not gs_default_on else COLOR["muted"],
                text_color_disabled=COLOR["muted"],
            )
