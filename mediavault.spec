# PyInstaller build spec for MediaVault. Build with:
#   .venv\Scripts\pyinstaller.exe mediavault.spec   (Windows)
#   .venv/bin/pyinstaller mediavault.spec           (macOS - must run ON a Mac,
#                                                     PyInstaller doesn't cross-compile)
# Produces dist/MediaVault/MediaVault.exe (onedir - not onefile, so bundled
# resources live in a stable, predictable location instead of being
# re-extracted to a fresh temp dir on every launch). On macOS also wraps the
# result into dist/MediaVault.app, since a plain onedir folder isn't a real
# double-clickable Mac app (no Info.plist, no Dock icon).
from __future__ import annotations

import sys

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
    icon="resources/icon.ico" if sys.platform == "win32" else None,
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

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="MediaVault.app",
        icon=None,  # resources/icon.ico isn't a valid .icns - add one later if needed
        bundle_identifier="com.mediavault.desktop",
        info_plist={"NSHighResolutionCapable": True},
    )
