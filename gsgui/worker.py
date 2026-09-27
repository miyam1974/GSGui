"""Background conversion worker."""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

from gsgui.ghostscript import (
    build_image_commands,
    build_pdf_or_ps_command,
    format_gs_command,
    resolve_output_path,
    run_ghostscript,
    validate_page_range,
)
from gsgui.i18n import Lang, t
from gsgui.models import (
    ConversionOptions,
    FileKind,
    JobStatus,
    QueueItem,
)


ProgressCallback = Callable[[str], None]
ItemCallback = Callable[[QueueItem], None]


class ConversionWorker:
    def __init__(
        self,
        gs_path: Path,
        items: list[QueueItem],
        options: ConversionOptions,
        on_item_update: ItemCallback,
        on_log: ProgressCallback,
        on_done: Callable[[], None],
        lang: Lang = Lang.EN,
    ) -> None:
        self.gs_path = gs_path
        self.items = items
        self.options = options
        self.on_item_update = on_item_update
        self.on_log = on_log
        self.on_done = on_done
        self.lang = lang
        self._cancel = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def cancel(self) -> None:
        self._cancel.set()

    def _run(self) -> None:
        try:
            if not validate_page_range(self.options.page_range):
                self.on_log(t(self.lang, "worker_bad_pages_log"))
                for item in self.items:
                    item.status = JobStatus.FAILED
                    item.message = t(self.lang, "worker_bad_pages")
                    self.on_item_update(item)
                return

            pdf_ps = [i for i in self.items if i.kind in (FileKind.PDF, FileKind.POSTSCRIPT)]
            images = [i for i in self.items if i.kind == FileKind.IMAGE]

            for item in pdf_ps:
                if self._cancel.is_set():
                    self._mark_cancelled(item)
                    continue
                self._convert_single(item)

            if images:
                if self._cancel.is_set():
                    for item in images:
                        self._mark_cancelled(item)
                else:
                    self._convert_images(images)
        finally:
            self.on_done()

    def _mark_cancelled(self, item: QueueItem) -> None:
        if item.status in (JobStatus.SUCCESS, JobStatus.FAILED):
            return
        item.status = JobStatus.CANCELLED
        item.message = t(self.lang, "worker_cancelled")
        self.on_item_update(item)

    def _convert_single(self, item: QueueItem) -> None:
        item.status = JobStatus.RUNNING
        item.message = t(self.lang, "worker_converting")
        self.on_item_update(item)

        output = resolve_output_path(item.path, self.options)
        command = build_pdf_or_ps_command(self.gs_path, item, output, self.options)
        item.command = command
        self.on_log(format_gs_command(command))

        try:
            code, log = run_ghostscript(command)
        except OSError as exc:
            item.status = JobStatus.FAILED
            item.message = str(exc)
            self.on_item_update(item)
            self.on_log(str(exc))
            return

        if self._cancel.is_set():
            self._mark_cancelled(item)
            return

        if code == 0 and output.exists():
            item.status = JobStatus.SUCCESS
            item.output_path = output
            item.output_size_bytes = output.stat().st_size
            item.message = ""
            if log:
                self.on_log(log)
        else:
            item.status = JobStatus.FAILED
            item.message = log or (
                f"Exit code {code}" if self.lang == Lang.EN else f"終了コード {code}"
            )
            self.on_log(item.message)
        self.on_item_update(item)

    def _convert_images(self, images: list[QueueItem]) -> None:
        jobs = build_image_commands(self.gs_path, images, self.options)
        for affected, output, command in jobs:
            if self._cancel.is_set():
                for item in affected:
                    self._mark_cancelled(item)
                continue

            for item in affected:
                item.status = JobStatus.RUNNING
                item.message = t(self.lang, "worker_converting")
                item.command = command
                self.on_item_update(item)

            self.on_log(format_gs_command(command))

            try:
                code, log = run_ghostscript(command)
            except OSError as exc:
                for item in affected:
                    item.status = JobStatus.FAILED
                    item.message = str(exc)
                    self.on_item_update(item)
                self.on_log(str(exc))
                continue

            if self._cancel.is_set():
                for item in affected:
                    self._mark_cancelled(item)
                continue

            if code == 0 and output.exists():
                size = output.stat().st_size
                for item in affected:
                    item.status = JobStatus.SUCCESS
                    item.output_path = output
                    # For merge, show total output size on each row.
                    item.output_size_bytes = size
                    item.message = ""
                    self.on_item_update(item)
                if log:
                    self.on_log(log)
            else:
                msg = log or (
                    f"Exit code {code}" if self.lang == Lang.EN else f"終了コード {code}"
                )
                for item in affected:
                    item.status = JobStatus.FAILED
                    item.message = msg
                    self.on_item_update(item)
                self.on_log(msg)
