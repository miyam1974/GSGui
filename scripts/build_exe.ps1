# Build GSGui.exe with PyInstaller (Windows).
# Usage:  .\.venv\Scripts\Activate.ps1; .\scripts\build_exe.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    throw "pyinstaller not found. Run: pip install -r requirements-build.txt"
}

$Entry = Join-Path $Root "gsgui\__main__.py"
$OutName = "GSGui-windows-x64"

& pyinstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name $OutName `
    --collect-all customtkinter `
    --collect-all tkinterdnd2 `
    $Entry

if ($LASTEXITCODE -ne 0) {
    throw "pyinstaller failed with exit code $LASTEXITCODE"
}

$Exe = Join-Path $Root "dist\$OutName.exe"
if (-not (Test-Path $Exe)) {
    throw "Build output not found: $Exe"
}

Write-Host "OK: $Exe"
