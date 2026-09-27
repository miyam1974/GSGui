"""Unit tests for command building and helpers (no GUI)."""

from __future__ import annotations

from pathlib import Path

from gsgui.drop_paths import parse_drop_paths
from gsgui.files import build_queue_item, collect_files, display_name
from gsgui.ghostscript import (
    build_image_commands,
    build_pdf_or_ps_command,
    format_gs_command,
    resolve_output_path,
    validate_page_range,
)
from gsgui.models import (
    Compatibility,
    ConversionOptions,
    FileKind,
    ImagePdfMode,
    OutputLocation,
    OverwritePolicy,
    PaperSize,
    QueueItem,
    classify_path,
    format_size,
)
from gsgui.settings import AppSettings, load_settings, save_settings
from gsgui.textutil import coerce_path_string, nfc


def test_classify_path() -> None:
    assert classify_path(Path("a.PDF")) == FileKind.PDF
    assert classify_path(Path("a.eps")) == FileKind.POSTSCRIPT
    assert classify_path(Path("a.jpeg")) == FileKind.IMAGE


def test_format_size() -> None:
    assert format_size(500) == "500 B"
    assert "KB" in format_size(2048)


def test_validate_page_range() -> None:
    assert validate_page_range("")
    assert validate_page_range("1")
    assert validate_page_range("1-3,5")
    assert not validate_page_range("1-")
    assert not validate_page_range("abc")


def test_resolve_output_numbered(tmp_path: Path) -> None:
    src = tmp_path / "doc.pdf"
    src.write_bytes(b"%PDF")
    existing = tmp_path / "doc_gs.pdf"
    existing.write_bytes(b"x")
    options = ConversionOptions(
        output_location=OutputLocation.SAME_AS_SOURCE,
        overwrite_policy=OverwritePolicy.NUMBERED,
    )
    out = resolve_output_path(src, options)
    assert out.name == "doc_gs_1.pdf"


def test_resolve_output_preview_skips_mkdir(tmp_path: Path) -> None:
    src = tmp_path / "nested" / "doc.pdf"
    # parent does not exist yet
    custom = tmp_path / "out_only"
    options = ConversionOptions(
        output_location=OutputLocation.CUSTOM,
        custom_output_dir=str(custom),
        overwrite_policy=OverwritePolicy.OVERWRITE,
    )
    out = resolve_output_path(src, options, create_dirs=False)
    assert out == custom / "doc_gs.pdf"
    assert not custom.exists()
    out2 = resolve_output_path(src, options, create_dirs=True)
    assert out2 == custom / "doc_gs.pdf"
    assert custom.is_dir()


def test_resolve_output_overwrite(tmp_path: Path) -> None:
    src = tmp_path / "doc.pdf"
    src.write_bytes(b"%PDF")
    existing = tmp_path / "doc_gs.pdf"
    existing.write_bytes(b"x")
    options = ConversionOptions(overwrite_policy=OverwritePolicy.OVERWRITE)
    out = resolve_output_path(src, options)
    assert out.name == "doc_gs.pdf"


def test_build_pdf_command(tmp_path: Path) -> None:
    src = tmp_path / "in.pdf"
    src.write_bytes(b"%PDF")
    item = QueueItem(path=src, kind=FileKind.PDF, size_bytes=4)
    out = tmp_path / "out.pdf"
    gs = Path(r"C:\gs\gswin64c.exe")
    cmd = build_pdf_or_ps_command(gs, item, out, ConversionOptions())
    assert cmd[0] == str(gs)
    assert "-sDEVICE=pdfwrite" in cmd
    assert any(c.startswith("-sOutputFile=") for c in cmd)
    assert str(src) in cmd


def test_build_pdf_command_page_range(tmp_path: Path) -> None:
    src = tmp_path / "in.pdf"
    src.write_bytes(b"%PDF")
    item = QueueItem(path=src, kind=FileKind.PDF, size_bytes=4)
    out = tmp_path / "out.pdf"
    gs = Path("gswin64c.exe")
    cmd = build_pdf_or_ps_command(
        gs, item, out, ConversionOptions(page_range="2-4", compatibility=Compatibility.PDF_1_4)
    )
    assert "-dFirstPage=2" in cmd
    assert "-dLastPage=4" in cmd
    assert "-dCompatibilityLevel=1.4" in cmd


def test_build_image_merge(tmp_path: Path) -> None:
    imgs = []
    for name in ("a.png", "b.png"):
        p = tmp_path / name
        p.write_bytes(b"\x89PNG")
        imgs.append(QueueItem(path=p, kind=FileKind.IMAGE, size_bytes=4))
    options = ConversionOptions(image_pdf_mode=ImagePdfMode.MERGE)
    jobs = build_image_commands(Path("gswin64c.exe"), imgs, options)
    assert len(jobs) == 1
    affected, output, cmd = jobs[0]
    assert len(affected) == 2
    assert output.name == "images_merged_gs.pdf"
    assert str(imgs[0].path) in cmd
    assert str(imgs[1].path) in cmd


def test_build_image_paper_a4(tmp_path: Path) -> None:
    img = tmp_path / "a.png"
    img.write_bytes(b"\x89PNG")
    item = QueueItem(path=img, kind=FileKind.IMAGE, size_bytes=4)
    options = ConversionOptions(paper_size=PaperSize.A4)
    jobs = build_image_commands(Path("gswin64c.exe"), [item], options, create_dirs=False)
    assert len(jobs) == 1
    _affected, _out, cmd = jobs[0]
    assert "-dFIXEDMEDIA" in cmd
    assert "-sPAPERSIZE=a4" in cmd


def test_format_gs_command_quotes_unicode() -> None:
    cmd = [r"C:\gs\gswin64c.exe", "-dBATCH", r"C:\Temp\ドコモ.pdf"]
    line = format_gs_command(cmd)
    assert "ドコモ.pdf" in line
    assert "-dBATCH" in line


def test_nfc_composes_dakuten() -> None:
    nfd = "ト\u3099コモて\u3099んき.pdf"
    assert nfc(nfd) == "ドコモでんき.pdf"
    assert display_name(Path(nfd)) == "ドコモでんき.pdf"


def test_coerce_file_uri_windows() -> None:
    assert coerce_path_string("file:///C:/Temp/a.pdf").replace("\\", "/") == "C:/Temp/a.pdf"
    assert coerce_path_string("{C:/Temp/a.pdf}") == "C:/Temp/a.pdf"
    assert coerce_path_string('"C:/Temp/a.pdf"') == "C:/Temp/a.pdf"
    # Must not force NFC (would break NFD on-disk names)
    nfd = "C:/Temp/ト\u3099.pdf"
    assert "\u3099" in coerce_path_string(nfd)


def test_collect_files_pdf(tmp_path: Path) -> None:
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF")
    found = collect_files([pdf])
    assert len(found) == 1
    assert found[0].name == "sample.pdf"
    uri = "file:///" + str(pdf.resolve()).replace("\\", "/")
    found2 = collect_files([Path(coerce_path_string(uri))])
    assert len(found2) == 1


def test_collect_nfd_japanese_pdf(tmp_path: Path) -> None:
    """Filesystem lookup must keep NFD paths; NFC is display-only."""
    import unicodedata

    nfd_name = "ト\u3099コモて\u3099んき.pdf"
    assert unicodedata.normalize("NFC", nfd_name) != nfd_name
    pdf = tmp_path / nfd_name
    pdf.write_bytes(b"%PDF")
    assert pdf.exists()
    assert not (tmp_path / unicodedata.normalize("NFC", nfd_name)).exists()
    found = collect_files([pdf])
    assert len(found) == 1
    assert found[0].exists()
    assert display_name(found[0]) == "ドコモでんき.pdf"


def test_parse_drop_paths_braces(tmp_path: Path) -> None:
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF")
    raw = "{" + str(pdf) + "}"
    paths = parse_drop_paths(raw)
    assert len(paths) == 1
    assert paths[0].name == "a.pdf"


def test_parse_drop_paths_newlines(tmp_path: Path) -> None:
    a = tmp_path / "a.pdf"
    b = tmp_path / "b.pdf"
    a.write_bytes(b"%PDF")
    b.write_bytes(b"%PDF")
    raw = f"{a}\n{b}"
    paths = parse_drop_paths(raw)
    assert {p.name for p in paths} == {"a.pdf", "b.pdf"}


def test_build_queue_item_pdf_defers_probe(tmp_path: Path) -> None:
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF")
    item = build_queue_item(pdf)
    assert item.kind == FileKind.PDF
    assert item.meta == "PDF"


def test_settings_roundtrip(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    path = tmp_path / "settings.json"
    monkeypatch.setattr("gsgui.settings.settings_path", lambda: path)
    original = AppSettings(
        pdf_settings="printer",
        last_scale_preset="screen",
        window_geometry="1000x700+10+20",
        custom_output_dir=str(tmp_path / "out"),
    )
    save_settings(original)
    loaded = load_settings()
    assert loaded.pdf_settings == "printer"
    assert loaded.last_scale_preset == "screen"
    assert loaded.window_geometry == "1000x700+10+20"
    assert loaded.custom_output_dir == str(tmp_path / "out")


def test_queue_name_wraplength() -> None:
    from gsgui.queue_view import queue_name_wraplength
    from gsgui.theme import QUEUE_FIXED_COLS_WIDTH, QUEUE_NAME_MIN_WRAP

    assert queue_name_wraplength(10) >= QUEUE_NAME_MIN_WRAP
    assert queue_name_wraplength(800) == 800 - QUEUE_FIXED_COLS_WIDTH


def test_show_row_detail_and_reduction(tmp_path: Path) -> None:
    from gsgui.models import JobStatus
    from gsgui.queue_view import has_openable_output, reduction_label, show_row_detail

    item = QueueItem(path=tmp_path / "a.pdf", kind=FileKind.PDF, size_bytes=10)
    item.status = JobStatus.FAILED
    item.message = "error"
    assert show_row_detail(item)
    item.status = JobStatus.SUCCESS
    item.message = "完了"
    assert not show_row_detail(item)
    assert not has_openable_output(item)
    text, _color = reduction_label(item)
    assert text == "—"


def test_build_pdf_command_page_list_and_color(tmp_path: Path) -> None:
    from gsgui.models import ColorMode

    src = tmp_path / "in.pdf"
    src.write_bytes(b"%PDF")
    item = QueueItem(path=src, kind=FileKind.PDF, size_bytes=4)
    out = tmp_path / "out.pdf"
    options = ConversionOptions(page_range="1,3,5", color_mode=ColorMode.GRAY)
    cmd = build_pdf_or_ps_command(Path("gswin64c.exe"), item, out, options)
    assert "-sPageList=1,3,5" in cmd
    assert "-sColorConversionStrategy=Gray" in cmd


def test_app_settings_from_options() -> None:
    from gsgui.models import PdfSettings

    options = ConversionOptions(
        pdf_settings=PdfSettings.PRINTER,
        page_range="2-4",
        custom_output_dir=r"C:\out",
    )
    s = AppSettings.from_options(
        options,
        ghostscript_path=r"C:\gs\gswin64c.exe",
        window_geometry="800x600+0+0",
        last_scale_preset="screen",
    )
    assert s.pdf_settings == "printer"
    assert s.page_range == "2-4"
    assert s.custom_output_dir == r"C:\out"
    assert s.ghostscript_path.endswith("gswin64c.exe")
    assert s.last_scale_preset == "screen"


def test_save_settings_oserror(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    path = tmp_path / "settings.json"
    monkeypatch.setattr("gsgui.settings.settings_path", lambda: path)

    def boom(*_a, **_k):  # noqa: ANN001
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_text", boom)
    assert save_settings(AppSettings()) is False


def test_worker_success_and_failure(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    from gsgui.models import JobStatus
    from gsgui.worker import ConversionWorker

    src = tmp_path / "doc.pdf"
    src.write_bytes(b"%PDF")
    item = QueueItem(path=src, kind=FileKind.PDF, size_bytes=4)
    updates: list[JobStatus] = []
    logs: list[str] = []
    done = {"ok": False}

    def fake_run(command, timeout=None):  # noqa: ANN001
        out = Path(next(c.split("=", 1)[1] for c in command if c.startswith("-sOutputFile=")))
        out.write_bytes(b"%PDF-out")
        return 0, ""

    monkeypatch.setattr("gsgui.worker.run_ghostscript", fake_run)
    worker = ConversionWorker(
        gs_path=Path("gswin64c.exe"),
        items=[item],
        options=ConversionOptions(),
        on_item_update=lambda i: updates.append(i.status),
        on_log=logs.append,
        on_done=lambda: done.__setitem__("ok", True),
    )
    worker._run()
    assert done["ok"]
    assert item.status == JobStatus.SUCCESS
    assert item.output_path is not None and item.output_path.exists()
    assert JobStatus.RUNNING in updates
    assert JobStatus.SUCCESS in updates

    bad = QueueItem(path=src, kind=FileKind.PDF, size_bytes=4)

    def fail_run(command, timeout=None):  # noqa: ANN001
        return 1, "boom"

    monkeypatch.setattr("gsgui.worker.run_ghostscript", fail_run)
    worker2 = ConversionWorker(
        gs_path=Path("gswin64c.exe"),
        items=[bad],
        options=ConversionOptions(),
        on_item_update=lambda i: None,
        on_log=logs.append,
        on_done=lambda: None,
    )
    worker2._run()
    assert bad.status == JobStatus.FAILED
    assert "boom" in bad.message


def test_worker_cancel_before_and_during(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    from gsgui.models import JobStatus
    from gsgui.worker import ConversionWorker

    a = tmp_path / "a.pdf"
    b = tmp_path / "b.pdf"
    a.write_bytes(b"%PDF")
    b.write_bytes(b"%PDF")
    items = [
        QueueItem(path=a, kind=FileKind.PDF, size_bytes=4),
        QueueItem(path=b, kind=FileKind.PDF, size_bytes=4),
    ]

    # Cancel before any convert: both pending → cancelled
    worker = ConversionWorker(
        gs_path=Path("gswin64c.exe"),
        items=items,
        options=ConversionOptions(),
        on_item_update=lambda i: None,
        on_log=lambda _m: None,
        on_done=lambda: None,
    )
    worker.cancel()
    worker._run()
    assert all(i.status == JobStatus.CANCELLED for i in items)
    assert all(i.message == "Cancelled" for i in items)

    # First succeeds, then cancel so the second item is skipped
    first = QueueItem(path=a, kind=FileKind.PDF, size_bytes=4)
    second = QueueItem(path=b, kind=FileKind.PDF, size_bytes=4)
    holder: dict = {}

    def fake_ok(command, timeout=None):  # noqa: ANN001
        out = Path(next(c.split("=", 1)[1] for c in command if c.startswith("-sOutputFile=")))
        out.write_bytes(b"%PDF-out")
        return 0, ""

    def on_update(item: QueueItem) -> None:
        if item.status == JobStatus.SUCCESS:
            holder["w"].cancel()

    monkeypatch.setattr("gsgui.worker.run_ghostscript", fake_ok)
    worker2 = ConversionWorker(
        gs_path=Path("gswin64c.exe"),
        items=[first, second],
        options=ConversionOptions(),
        on_item_update=on_update,
        on_log=lambda _m: None,
        on_done=lambda: None,
    )
    holder["w"] = worker2
    worker2._run()
    assert first.status == JobStatus.SUCCESS
    assert second.status == JobStatus.CANCELLED


def test_worker_invalid_page_range(tmp_path: Path) -> None:
    from gsgui.models import JobStatus
    from gsgui.worker import ConversionWorker

    src = tmp_path / "doc.pdf"
    src.write_bytes(b"%PDF")
    item = QueueItem(path=src, kind=FileKind.PDF, size_bytes=4)
    logs: list[str] = []
    worker = ConversionWorker(
        gs_path=Path("gswin64c.exe"),
        items=[item],
        options=ConversionOptions(page_range="1-"),
        on_item_update=lambda i: None,
        on_log=logs.append,
        on_done=lambda: None,
    )
    worker._run()
    assert item.status == JobStatus.FAILED
    assert "page range" in item.message.lower()
    assert logs
