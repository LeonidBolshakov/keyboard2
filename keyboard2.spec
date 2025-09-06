# -*- mode: python ; coding: utf-8 -*-

import os

a = Analysis(
    ['SRC\\keyboard2.py'],
    pathex=[os.path.abspath('SRC')],
    binaries=[],
    datas=[('_internal/dialogue.ui', '_internal')],
    hiddenimports=['dotenv', 'customtextedit'],
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='keyboard2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='peremeshat_bwa1745uinup.ico', 
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
