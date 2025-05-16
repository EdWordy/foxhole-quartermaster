
# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all necessary data files
datas = [
    ('CheckImages/Default/*.png', 'CheckImages/Default'),
    ('CheckImages/Numbers/*.png', 'CheckImages/Numbers'),
    ('item_mappings.csv', '.'),
    ('item_thresholds.json', '.'),
]

# Add config.yaml if it exists
if os.path.exists('config.yaml'):
    datas.append(('config.yaml', '.'))

# Collect all submodules for packages that might need them
hiddenimports = [
    'numpy',
    'pandas',
    'matplotlib',
    'matplotlib.backends.backend_tkagg',
    'matplotlib.backends.backend_agg',
    'PIL._tkinter_finder',
    'cv2',
    'yaml',
    'xlsxwriter',
    'tkinter',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.ttk',
    'tkinter.scrolledtext',
]

# Add all project modules
hiddenimports.extend([
    'core.models',
    'core.image_recognition',
    'core.inventory_manager',
    'core.quartermaster',
    'utils.config_manager',
    'utils.error_logger',
    'ui.main_window',
    'ui.analytics_window',
])

a = Analysis(
    ['main.py'],  # Main script
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='FoxholeQuartermaster',
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
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FoxholeQuartermaster',
)

# For macOS, create a .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='FoxholeQuartermaster.app',
        icon='icon.icns' if os.path.exists('icon.icns') else None,
        bundle_identifier=None,
    )
