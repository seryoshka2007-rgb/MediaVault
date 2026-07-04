# PyInstaller build spec for MediaVault. Build with:
#   .venv\Scripts\pyinstaller.exe mediavault.spec
# Produces dist/MediaVault/MediaVault.exe (onedir - not onefile, so bundled
# resources live in a stable, predictable location instead of being
# re-extracted to a fresh temp dir on every launch).
from __future__ import annotations

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[("themes", "themes"), ("resources", "resources")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MediaVault",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="resources/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MediaVault",
)
