"""Parse OS / Tk DnD payloads into filesystem paths (no GUI)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from gsgui.textutil import coerce_path_string, normalize_path


def parse_drop_paths(data: str, *, splitlist: Callable[[str], list] | None = None) -> list[Path]:
    """Parse a DnD data string into normalized Paths.

    splitlist: optional Tk ``tk.splitlist`` for brace-quoted Windows paths.
    """
    if not data:
        return []
    text = data.strip().strip("\0")
    tokens: list[str] = []

    if "\n" in text or "\r" in text:
        tokens = [line.strip() for line in text.replace("\r\n", "\n").split("\n") if line.strip()]
    else:
        if splitlist is not None:
            try:
                tokens = [str(p) for p in splitlist(text) if str(p).strip()]
            except (TypeError, ValueError, RuntimeError, OSError):
                tokens = []
        if not tokens:
            current = ""
            in_brace = False
            for ch in text:
                if ch == "{":
                    in_brace = True
                    current = ""
                elif ch == "}":
                    in_brace = False
                    if current:
                        tokens.append(current)
                    current = ""
                elif ch == " " and not in_brace:
                    if current:
                        tokens.append(current)
                    current = ""
                else:
                    current += ch
            if current:
                tokens.append(current)

    paths: list[Path] = []
    for token in tokens:
        coerced = coerce_path_string(token)
        if not coerced:
            continue
        paths.append(normalize_path(Path(coerced)))
    return paths
