# foxhole_quartermaster.spec
import PyInstaller.config
from PyInstaller.utils.hooks import collect_all

# -*- mode: python ; coding: utf-8 -*-

# foxhole_quartermaster.spec
block_cipher = None

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('CheckImages/Default/*.png', 'CheckImages/Default'),
        ('CheckImages/Numbers/*.png', 'CheckImages/Numbers'),
        ('item_mappings.csv', '.'),
        ('number_mappings.csv', '.')
    ],
    hiddenimports=['PIL', 'PIL._tkinter_finder', 'cv2', 'pandas', 'numpy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FoxholeQuartermaster',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)