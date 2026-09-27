# GSGui

**[English](README.md)** | **[日本語](README.ja.md)**

A **Windows PDF conversion GUI** powered by Ghostscript.  
Drop PDFs, PostScript, or images, then re-export or convert them with presets and a small set of advanced options.

Ghostscript itself is **not** bundled. GSGui calls the system `gswin64c.exe`.

![GSGui main window](docs/images/main.png)

## Download (executable)

Get the latest **`GSGui-windows-x64.exe`** from [Releases](https://github.com/miyam1974/GSGui/releases).

- No Python install required
- **Ghostscript must be installed separately** (see below)
- Windows may warn about an unknown publisher (the exe is unsigned)

Pushing a `v*` tag runs GitHub Actions, which builds the exe and attaches it to the Release.

## Features

- Input queue (drag & drop / add / remove / clear). Folder drop supported
- Formats: PDF, PS, EPS, JPEG, PNG, TIFF
- Output location (same folder as source, or a chosen folder). Names: `original_gs.pdf`
- On name conflict: overwrite / numbered
- Modes: PDF rewrite, PS/EPS → PDF, images → PDF (per file / merge)
- Quality presets: Screen / Ebook (default) / Printer / Prepress / GS default
- Advanced: PDF compatibility, color, resolution, JPEG quality, page range, image paper & orientation
- Batch convert, progress, cancel, results, log, and command preview
- Auto-detect Ghostscript, or set it with **Ghostscript path** in the header
- UI language: **EN** (default) / **日本語** (toggle in the header)
- Remembers window position and settings (`%USERPROFILE%\.gsgui\settings.json`)

## Requirements

| Item | Detail |
|------|--------|
| OS | Windows 10 / 11 |
| Ghostscript | Install separately from the [official site](https://www.ghostscript.com/) (64-bit `gswin64c.exe`) |
| From source | Python 3.11+ (developed on 3.13) and `requirements.txt` |

### If Ghostscript is not found

1. Install Ghostscript  
2. If it still is not detected, use **Ghostscript path** at the top right and select `gswin64c.exe`

## Usage

1. Drop PDF / PS / EPS / JPEG / PNG / TIFF onto the window (or use **Add…**)
2. Choose preset, output location, and conflict policy on the right (open **Advanced…** if needed)
3. Click **Convert**
4. Use 📁 / 📄 on a queue row to open the output folder or PDF

## Run from source

```powershell
git clone https://github.com/miyam1974/GSGui.git
cd GSGui
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m gsgui
```

After the first setup you can also use `run.bat` (creates a venv if missing).

## Development

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt pytest
python -m pytest tests -q
```

### Build the exe locally

```powershell
pip install -r requirements.txt -r requirements-build.txt
.\scripts\build_exe.ps1
```

Output: `dist\GSGui-windows-x64.exe`

### Cut a release (maintainers)

```powershell
git tag v0.1.0
git push origin v0.1.0
```

The **Release** workflow builds on Windows and attaches the exe to the GitHub Release.

## Out of scope

Thumbnails, PDF/A, page editing / annotations / OCR, password removal, shell integration, conversion history, and similar features.  
GSGui is intentionally a focused Ghostscript front end.

## License

Source code in this repository is under the [MIT License](LICENSE).

[Ghostscript](https://www.ghostscript.com/) is not part of this project and is subject to Artifex licensing (e.g. AGPL). Check Ghostscript’s terms when you use or redistribute it.
