"""Queue table UI helpers (header / row build + status styling)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from gsgui.files import display_name
from gsgui.models import JobStatus, QueueItem, format_size
from gsgui.textutil import nfc
from gsgui.theme import (
    COLOR,
    QUEUE_COL_FILE_FALLBACK,
    QUEUE_COL_META,
    QUEUE_COL_OPEN,
    QUEUE_COL_REDUCTION,
    QUEUE_COL_SIZE,
    QUEUE_COL_STATUS,
    QUEUE_COLUMNS,
    QUEUE_DETAIL_WRAP_EXTRA,
    QUEUE_FIXED_COLS_WIDTH,
    QUEUE_NAME_MIN_WRAP,
    QUEUE_OPEN_BTN_HEIGHT,
    QUEUE_OPEN_BTN_WIDTH,
    QUEUE_SCROLL_FALLBACK_WIDTH,
    font,
    icon_font,
)

STATUS_LABELS = {
    JobStatus.PENDING: "待機",
    JobStatus.RUNNING: "実行中",
    JobStatus.SUCCESS: "成功",
    JobStatus.FAILED: "失敗",
    JobStatus.CANCELLED: "中断",
}

STATUS_COLORS = {
    JobStatus.PENDING: COLOR["muted"],
    JobStatus.RUNNING: COLOR["accent"],
    JobStatus.SUCCESS: COLOR["success"],
    JobStatus.FAILED: COLOR["danger"],
    JobStatus.CANCELLED: COLOR["muted"],
}

RowWidgets = dict[str, Any]


def queue_name_wraplength(scroll_width: int) -> int:
    """Pixels available for the filename column."""
    width = scroll_width if scroll_width >= 80 else QUEUE_SCROLL_FALLBACK_WIDTH
    return max(QUEUE_NAME_MIN_WRAP, width - QUEUE_FIXED_COLS_WIDTH)


def queue_detail_wraplength(name_wrap: int) -> int:
    return name_wrap + QUEUE_DETAIL_WRAP_EXTRA


def show_row_detail(item: QueueItem) -> bool:
    return bool(
        item.message
        and item.status not in (JobStatus.PENDING, JobStatus.SUCCESS)
        and item.message not in ("完了",)
    )


def has_openable_output(item: QueueItem) -> bool:
    return bool(
        item.status == JobStatus.SUCCESS
        and item.output_path is not None
        and item.output_path.exists()
    )


def reduction_label(item: QueueItem) -> tuple[str, object]:
    """Return (text, text_color) for the reduction column."""
    red = item.reduction_percent
    if red is None:
        return "—", COLOR["muted"]
    color = COLOR["success"] if red > 0 else COLOR["muted"]
    return f"{red:.0f}%", color


def build_queue_header(parent: ctk.CTkScrollableFrame) -> ctk.CTkFrame:
    header = ctk.CTkFrame(parent, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", pady=(0, 2))
    header.grid_columnconfigure(1, weight=1)
    for col, (text, w) in enumerate(QUEUE_COLUMNS):
        ctk.CTkLabel(
            header,
            text=text,
            width=w if w else QUEUE_COL_FILE_FALLBACK,
            anchor="w",
            font=font(10),
            text_color=COLOR["muted"],
        ).grid(row=0, column=col, sticky="ew", padx=2)
    return header


def build_queue_empty_label(parent: ctk.CTkScrollableFrame) -> ctk.CTkLabel:
    label = ctk.CTkLabel(
        parent,
        text="まだファイルがありません",
        text_color=COLOR["muted"],
        font=font(12),
    )
    label.grid(row=1, column=0, pady=12)
    return label


def build_queue_row(
    parent: ctk.CTkScrollableFrame,
    *,
    index: int,
    item: QueueItem,
    selected: bool,
    name_wrap: int,
    on_select: Callable[[int], None],
    on_open_folder: Callable[[QueueItem], None],
    on_open_pdf: Callable[[QueueItem], None],
) -> RowWidgets:
    """Create one queue row and return widget refs for differential updates."""
    frame = ctk.CTkFrame(
        parent,
        fg_color=COLOR["row_sel"] if selected else COLOR["row"],
        corner_radius=6,
        border_width=2 if selected else 1,
        border_color=COLOR["row_sel_border"] if selected else COLOR["header"],
    )
    frame.grid(row=index + 1, column=0, sticky="ew", pady=2)
    frame.grid_columnconfigure(1, weight=1)

    status = ctk.CTkLabel(
        frame,
        text=STATUS_LABELS[item.status],
        width=QUEUE_COL_STATUS,
        anchor="nw",
        font=font(11, "bold"),
        text_color=STATUS_COLORS[item.status],
    )
    status.grid(row=0, column=0, padx=6, pady=4, sticky="nw")

    name = ctk.CTkLabel(
        frame,
        text=display_name(item.path),
        anchor="w",
        justify="left",
        font=font(12),
        text_color=COLOR["text"],
        wraplength=name_wrap,
    )
    name.grid(row=0, column=1, sticky="ew", padx=2, pady=4)

    meta = ctk.CTkLabel(
        frame,
        text=item.meta,
        width=QUEUE_COL_META,
        anchor="nw",
        text_color=COLOR["muted"],
        font=font(11),
    )
    meta.grid(row=0, column=2, padx=2, pady=4, sticky="nw")
    size = ctk.CTkLabel(
        frame,
        text=format_size(item.size_bytes),
        width=QUEUE_COL_SIZE,
        anchor="nw",
        text_color=COLOR["muted"],
        font=font(11),
    )
    size.grid(row=0, column=3, padx=2, pady=4, sticky="nw")
    out_size = ctk.CTkLabel(
        frame,
        text=format_size(item.output_size_bytes),
        width=QUEUE_COL_SIZE,
        anchor="nw",
        text_color=COLOR["muted"],
        font=font(11),
    )
    out_size.grid(row=0, column=4, padx=2, pady=4, sticky="nw")
    red_text, red_color = reduction_label(item)
    reduction = ctk.CTkLabel(
        frame,
        text=red_text,
        width=QUEUE_COL_REDUCTION,
        anchor="nw",
        font=font(11),
        text_color=red_color,
    )
    reduction.grid(row=0, column=5, padx=2, pady=4, sticky="nw")

    open_cell = ctk.CTkFrame(frame, fg_color="transparent", width=QUEUE_COL_OPEN)
    open_cell.grid(row=0, column=6, padx=(2, 6), pady=2, sticky="nw")
    folder_btn = ctk.CTkButton(
        open_cell,
        text="📁",
        width=QUEUE_OPEN_BTN_WIDTH,
        height=QUEUE_OPEN_BTN_HEIGHT,
        font=icon_font(13),
        fg_color="transparent",
        hover_color=COLOR["panel_alt"],
        text_color=COLOR["icon_muted"],
        state="disabled",
        command=lambda i=item: on_open_folder(i),
    )
    folder_btn.pack(side="left")
    pdf_btn = ctk.CTkButton(
        open_cell,
        text="📄",
        width=QUEUE_OPEN_BTN_WIDTH,
        height=QUEUE_OPEN_BTN_HEIGHT,
        font=icon_font(13),
        fg_color="transparent",
        hover_color=COLOR["panel_alt"],
        text_color=COLOR["icon_muted"],
        state="disabled",
        command=lambda i=item: on_open_pdf(i),
    )
    pdf_btn.pack(side="left")

    detail = ctk.CTkLabel(
        frame,
        text="",
        anchor="w",
        justify="left",
        font=font(10),
        text_color=COLOR["muted"],
        wraplength=queue_detail_wraplength(name_wrap),
    )

    for widget in (frame, status, name, meta, size, out_size, reduction, open_cell):
        widget.bind("<Button-1>", lambda _e, i=index: on_select(i))

    widgets: RowWidgets = {
        "frame": frame,
        "item": item,
        "status": status,
        "name": name,
        "meta": meta,
        "size": size,
        "out_size": out_size,
        "reduction": reduction,
        "folder_btn": folder_btn,
        "pdf_btn": pdf_btn,
        "detail": detail,
    }
    apply_queue_row_data(widgets, item)
    return widgets


def apply_queue_row_data(widgets: RowWidgets, item: QueueItem) -> None:
    """Update an existing row's labels/buttons without destroying the frame."""
    widgets["item"] = item
    widgets["status"].configure(
        text=STATUS_LABELS[item.status],
        text_color=STATUS_COLORS[item.status],
    )
    widgets["meta"].configure(text=item.meta)
    widgets["size"].configure(text=format_size(item.size_bytes))
    widgets["out_size"].configure(text=format_size(item.output_size_bytes))
    red_text, red_color = reduction_label(item)
    widgets["reduction"].configure(text=red_text, text_color=red_color)

    has_out = has_openable_output(item)
    open_color = COLOR["icon"] if has_out else COLOR["icon_muted"]
    open_state = "normal" if has_out else "disabled"
    widgets["folder_btn"].configure(text_color=open_color, state=open_state)
    widgets["pdf_btn"].configure(text_color=open_color, state=open_state)

    detail = widgets["detail"]
    if show_row_detail(item):
        detail.configure(text=nfc(item.message[:100]))
        detail.grid(row=1, column=0, columnspan=7, sticky="ew", padx=8, pady=(0, 4))
    else:
        detail.grid_remove()


def paint_queue_row_selection(widgets: RowWidgets, *, selected: bool) -> None:
    widgets["frame"].configure(
        fg_color=COLOR["row_sel"] if selected else COLOR["row"],
        border_width=2 if selected else 1,
        border_color=COLOR["row_sel_border"] if selected else COLOR["header"],
    )


__all__ = [
    "QUEUE_COLUMNS",
    "STATUS_COLORS",
    "STATUS_LABELS",
    "apply_queue_row_data",
    "build_queue_empty_label",
    "build_queue_header",
    "build_queue_row",
    "has_openable_output",
    "paint_queue_row_selection",
    "queue_detail_wraplength",
    "queue_name_wraplength",
    "reduction_label",
    "show_row_detail",
]
