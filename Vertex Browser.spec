# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('Vertex Browser.png', '.'), ('config.yaml', '.'), ('frontend', 'frontend'), ('extensions', 'extensions'), ('backend', 'backend'), ('ai', 'ai'), ('security', 'security')],
    hiddenimports=['tkinter', 'customtkinter', 'cefpython3', 'flask', 'requests', 'beautifulsoup4', 'lxml', 'yaml', 'sklearn', 'numpy', 'pandas'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'PySide2', 'PySide6'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Vertex Browser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['Vertex Browser.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Vertex Browser',
)
app = BUNDLE(
    coll,
    name='Vertex Browser.app',
    icon='Vertex Browser.icns',
    bundle_identifier=None,
)
