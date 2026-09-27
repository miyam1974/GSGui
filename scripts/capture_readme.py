"""Capture GSGui main windows for README (Windows): English + Japanese."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from pathlib import Path

from PIL import Image

import gsgui.settings as settings_mod
from gsgui.app import App
from gsgui.i18n import Lang

IMAGES = Path(__file__).resolve().parents[1] / "docs" / "images"
OUT_EN = IMAGES / "main.png"
OUT_JA = IMAGES / "main.ja.png"

# Neutral sample path — no real username / home directory
SAMPLE_OUTPUT_DIR = r"C:\Output"

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
PW_RENDERFULLCONTENT = 2


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


def capture_hwnd(hwnd: int) -> Image.Image:
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    if width <= 0 or height <= 0:
        raise RuntimeError(f"invalid window size: {width}x{height}")

    hwnd_dc = user32.GetWindowDC(hwnd)
    mem_dc = gdi32.CreateCompatibleDC(hwnd_dc)
    bmp = gdi32.CreateCompatibleBitmap(hwnd_dc, width, height)
    old = gdi32.SelectObject(mem_dc, bmp)

    ok = user32.PrintWindow(hwnd, mem_dc, PW_RENDERFULLCONTENT)
    if not ok:
        gdi32.BitBlt(mem_dc, 0, 0, width, height, hwnd_dc, 0, 0, 0x00CC0020)

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = width
    bmi.biHeight = -height  # top-down
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    buf_len = width * height * 4
    buf = (ctypes.c_char * buf_len)()
    gdi32.GetDIBits(mem_dc, bmp, 0, height, buf, ctypes.byref(bmi), 0)

    gdi32.SelectObject(mem_dc, old)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem_dc)
    user32.ReleaseDC(hwnd, hwnd_dc)

    return Image.frombuffer("RGB", (width, height), bytes(buf), "raw", "BGRX", 0, 1)


def _disable_persist(app: App) -> None:
    settings_mod.save_settings = lambda _s: True  # type: ignore[assignment]
    app._schedule_persist = lambda: None  # type: ignore[method-assign]
    app._persist_settings = lambda: None  # type: ignore[method-assign]


def sanitize_for_readme(app: App, lang: Lang) -> None:
    """Strip personal paths and force UI language for the public screenshot."""
    from gsgui.labels import out_value_to_label
    from gsgui.models import OutputLocation

    _disable_persist(app)
    app._set_language(lang, persist=False)

    same = out_value_to_label(lang)[OutputLocation.SAME_AS_SOURCE.value]
    app.out_label_var.set(same)
    app.out_seg.set(same)
    from gsgui.segment_style import paint_segment

    paint_segment(app.out_seg)

    app.output_dir_entry.configure(state="normal")
    app.output_dir_entry.delete(0, "end")
    app.output_dir_entry.insert(0, SAMPLE_OUTPUT_DIR)
    app._update_output_path_enabled()


def _window_hwnd(app: App) -> int:
    hwnd = user32.GetParent(int(app.winfo_id()))
    return hwnd if hwnd else int(app.winfo_id())


def capture_once(lang: Lang, out: Path) -> None:
    app = App()
    app.geometry("1140x680")
    sanitize_for_readme(app, lang)

    def shoot_and_quit() -> None:
        try:
            app.update_idletasks()
            app.update()
            app.lift()
            app.focus_force()
            app.update()
            img = capture_hwnd(_window_hwnd(app))
            extrema = img.convert("L").getextrema()
            if extrema[1] < 10:
                raise RuntimeError(f"capture looks black (extrema={extrema})")
            out.parent.mkdir(parents=True, exist_ok=True)
            img.save(out, format="PNG", optimize=True)
            print(f"saved {out} ({img.size[0]}x{img.size[1]}) lang={lang.value}")
        finally:
            app.destroy()

    app.after(2000, shoot_and_quit)
    app.mainloop()


def main() -> None:
    capture_once(Lang.EN, OUT_EN)
    capture_once(Lang.JA, OUT_JA)


if __name__ == "__main__":
    main()
