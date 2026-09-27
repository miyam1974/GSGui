"""UI language strings. English is the default."""

from __future__ import annotations

from enum import Enum


class Lang(str, Enum):
    EN = "en"
    JA = "ja"


DEFAULT_LANG = Lang.EN

LANG_TOGGLE_LABELS = {
    Lang.EN: "EN",
    Lang.JA: "日本語",
}

# Flat UI strings keyed by id. Nested structures for choice maps live in labels.py / presets.py.
STRINGS: dict[Lang, dict[str, str]] = {
    Lang.EN: {
        "tagline": "Drop · Choose · Make PDF",
        "gs_path_button": "Ghostscript path",
        "gs_found": "Ghostscript  {name}",
        "gs_missing": "Ghostscript not found",
        "drop_title": "Drop files here",
        "drop_hint": "PDF / PS / EPS / JPEG / PNG / TIFF  ·  Folders OK",
        "btn_add": "Add…",
        "btn_remove": "Remove",
        "btn_clear": "Clear",
        "queue_title": "Queue",
        "section_preset": "Preset",
        "gs_default_check": "GS default",
        "section_output": "Output",
        "label_location": "Location",
        "label_path": "Path",
        "placeholder_output_dir": "Output folder",
        "label_overwrite": "If exists",
        "section_unit": "PDF unit (JPEG / PNG / TIFF)",
        "label_unit": "Unit",
        "btn_advanced": "Advanced…",
        "btn_convert": "Convert",
        "btn_cancel": "Cancel",
        "label_log": "Log",
        "label_command": "Command",
        "cmd_no_gs": "Ghostscript is not configured.",
        "cmd_empty_queue": "Queue is empty.",
        "cmd_no_preview": "No preview",
        "queue_empty": "No files yet",
        "dialog_advanced_title": "Advanced",
        "adv_compat": "PDF compatibility",
        "adv_color": "Color",
        "adv_dpi": "Resolution dpi",
        "adv_dpi_other": "Other",
        "adv_dpi_placeholder": "e.g. 96",
        "adv_jpeg": "JPEG quality",
        "adv_pages": "Page range",
        "adv_pages_placeholder": "e.g. 1-3,5 (blank = all)",
        "adv_paper": "Image paper",
        "adv_orient": "Orientation",
        "adv_help": "Page range applies to PDF / PS only. Paper and orientation apply to image conversion.",
        "adv_ok": "OK",
        "browse_gs_title": "Select gswin64c.exe",
        "browse_out_title": "Output folder",
        "add_files_title": "Add files",
        "msg_drop_unparsed": "Could not interpret the dropped path.\nUse Add… or try dropping from another location.",
        "msg_no_supported": "No supported files found.",
        "msg_received_paths": "\n\nPaths received:\n{detail}",
        "log_unrecognized": "Unrecognized path: {detail}",
        "log_added": "Added {n} file(s)",
        "log_drop_fail": "Could not parse drop: {data!r}",
        "err_no_gs": (
            "Ghostscript was not found.\n"
            "Install it from https://www.ghostscript.com/ or set gswin64c.exe "
            "with “{button}” at the top right."
        ),
        "err_empty_queue": "There are no files to convert.",
        "err_page_range": "Invalid page range. Example: 1-3,5",
        "err_need_outdir": "Please specify an output folder.",
        "log_convert_start": "——— Convert start ———",
        "log_convert_end": "——— Convert end ———",
        "log_cancel_requested": "Cancel requested…",
        "msg_done": "Done: {ok} succeeded / {ng} failed",
        "msg_no_out_file": "No output file to open.",
        "msg_no_out_pdf": "No output PDF to open.",
        "status_pending": "Pending",
        "status_running": "Running",
        "status_success": "OK",
        "status_failed": "Failed",
        "status_cancelled": "Cancelled",
        "col_status": "Status",
        "col_file": "File",
        "col_info": "Info",
        "col_src": "Src",
        "col_out": "Out",
        "col_reduce": "Saved",
        "col_open": "Open",
        "worker_converting": "Converting…",
        "worker_cancelled": "Cancelled",
        "worker_bad_pages": "Invalid page range",
        "worker_bad_pages_log": "Invalid page range (e.g. 1-3,5)",
        "meta_image": "Image",
        "meta_pdf": "PDF",
        "meta_ps": "PostScript",
        "meta_unknown": "Unknown",
        "meta_pages": "{n} pages",
        "preset_help_fallback": "Maps to Ghostscript -dPDFSETTINGS.",
    },
    Lang.JA: {
        "tagline": "落とす · 選ぶ · PDF にする",
        "gs_path_button": "Ghostscriptパス設定",
        "gs_found": "Ghostscript  {name}",
        "gs_missing": "Ghostscript 未検出",
        "drop_title": "ファイルをドロップ",
        "drop_hint": "PDF / PS / EPS / JPEG / PNG / TIFF　·　フォルダ可",
        "btn_add": "追加…",
        "btn_remove": "削除",
        "btn_clear": "クリア",
        "queue_title": "キュー",
        "section_preset": "プリセット",
        "gs_default_check": "GS既定",
        "section_output": "出力",
        "label_location": "場所",
        "label_path": "パス",
        "placeholder_output_dir": "出力フォルダ",
        "label_overwrite": "同名時",
        "section_unit": "PDF変換単位（JPEG / PNG / TIFF の場合）",
        "label_unit": "単位",
        "btn_advanced": "詳細設定…",
        "btn_convert": "変換する",
        "btn_cancel": "中断",
        "label_log": "ログ",
        "label_command": "実行コマンド",
        "cmd_no_gs": "Ghostscript が未設定です。",
        "cmd_empty_queue": "キューが空です。",
        "cmd_no_preview": "プレビューなし",
        "queue_empty": "まだファイルがありません",
        "dialog_advanced_title": "詳細設定",
        "adv_compat": "PDF 互換",
        "adv_color": "色",
        "adv_dpi": "解像度 dpi",
        "adv_dpi_other": "その他",
        "adv_dpi_placeholder": "例: 96",
        "adv_jpeg": "JPEG 品質",
        "adv_pages": "ページ範囲",
        "adv_pages_placeholder": "例: 1-3,5（空欄で全ページ）",
        "adv_paper": "画像の用紙",
        "adv_orient": "向き",
        "adv_help": "ページ範囲は PDF / PS のみ。用紙・向きは画像変換時に有効。",
        "adv_ok": "OK",
        "browse_gs_title": "gswin64c.exe を選択",
        "browse_out_title": "出力フォルダ",
        "add_files_title": "ファイルを追加",
        "msg_drop_unparsed": "ドロップされたパスを解釈できませんでした。\n「追加…」から選ぶか、別の場所からドロップしてください。",
        "msg_no_supported": "対応ファイルが見つかりませんでした。",
        "msg_received_paths": "\n\n受け取ったパス:\n{detail}",
        "log_unrecognized": "未認識のパス: {detail}",
        "log_added": "{n} 件追加しました",
        "log_drop_fail": "ドロップを解釈できませんでした: {data!r}",
        "err_no_gs": (
            "Ghostscript が見つかりません。\n"
            "https://www.ghostscript.com/ からインストールするか、"
            "右上の「{button}」で gswin64c.exe を指定してください。"
        ),
        "err_empty_queue": "変換するファイルがありません。",
        "err_page_range": "ページ範囲の形式が不正です。例: 1-3,5",
        "err_need_outdir": "出力フォルダを指定してください。",
        "log_convert_start": "——— 変換開始 ———",
        "log_convert_end": "——— 変換終了 ———",
        "log_cancel_requested": "中断を要求しました…",
        "msg_done": "完了: 成功 {ok} / 失敗 {ng}",
        "msg_no_out_file": "開く出力ファイルがありません。",
        "msg_no_out_pdf": "開く出力 PDF がありません。",
        "status_pending": "待機",
        "status_running": "実行中",
        "status_success": "成功",
        "status_failed": "失敗",
        "status_cancelled": "中断",
        "col_status": "状態",
        "col_file": "ファイル",
        "col_info": "情報",
        "col_src": "元",
        "col_out": "出力",
        "col_reduce": "削減",
        "col_open": "開く",
        "worker_converting": "変換中…",
        "worker_cancelled": "中断されました",
        "worker_bad_pages": "ページ範囲が不正です",
        "worker_bad_pages_log": "ページ範囲の形式が不正です（例: 1-3,5）",
        "meta_image": "画像",
        "meta_pdf": "PDF",
        "meta_ps": "PostScript",
        "meta_unknown": "不明",
        "meta_pages": "{n} ページ",
        "preset_help_fallback": "Ghostscript の -dPDFSETTINGS に対応します。",
    },
}


def parse_lang(value: str | None) -> Lang:
    if value in (Lang.JA.value, "ja", "jp", "japanese"):
        return Lang.JA
    return Lang.EN


def t(lang: Lang, key: str, **kwargs: object) -> str:
    table = STRINGS.get(lang) or STRINGS[DEFAULT_LANG]
    text = table.get(key) or STRINGS[DEFAULT_LANG].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text
