# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Foxhole Quartermaster
Configured to create a single-file executable with optimized exclusions
"""
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ============================================
# Data Files Configuration
# ============================================

# Collect all necessary data files
datas = [
    ('data/processed_templates', 'data/processed_templates'),
    ('data/catalog.json', 'data'),
    ('data/item_thresholds.json', 'data'),
]

# Add config.yaml if it exists
if os.path.exists('config.yaml'):
    datas.append(('config.yaml', '.'))

# ============================================
# Hidden Imports Configuration
# ============================================

# Collect all submodules for packages that might need them
hiddenimports = [
    # Core dependencies
    'numpy',
    'pandas',
    'cv2',
    'yaml',
    'xlsxwriter',
    
    # Matplotlib and backends
    'matplotlib',
    'matplotlib.backends.backend_tkagg',
    'matplotlib.backends.backend_agg',
    
    # PIL/Pillow
    'PIL',
    'PIL._tkinter_finder',
    'PIL.Image',
    'PIL.ImageTk',
    
    # Tkinter components
    'tkinter',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.ttk',
    'tkinter.scrolledtext',
    
    # Project modules
    'core.models',
    'core.image_recognition',
    'core.inventory_manager',
    'core.quartermaster',
    'utils.config_manager',
    'utils.error_logger',
    'ui.main_window',
    'ui.analytics_window',
]

# ============================================
# Module Exclusions
# ============================================

# Exclude unnecessary modules to reduce executable size
excludes = [
    'scipy',
    'setuptools',
    'distutils',
    'tornado',
    'PyQt4',
    'PyQt5',
    'pydoc',
    'pythoncom',
    'pywintypes',
    'sqlite3',
    'sklearn',
    'scapy',
    'scrapy',
    'sympy',
    'kivy',
    'pyramid',
    'tensorflow',
    'pipenv',
    'pattern',
    'mechanize',
    'beautifulsoup4',
    'requests',
    'wxPython',
    'pygi',
    'pygame',
    'pyglet',
    'flask',
    'django',
    'pylint',
    'pytube',
    'odfpy',
    'mccabe',
    'pilkit',
    'wrapt',
    'astroid',
    'isort',
    # Additional common exclusions
    'test',
    'tests',
    'testing',
    '_pytest',
    'pytest',
    'unittest',
    'doctest',
]

# ============================================
# Analysis Configuration
# ============================================

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ============================================
# PYZ Archive
# ============================================

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# ============================================
# Executable Configuration
# ============================================

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
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)

# ============================================
# macOS Bundle (if applicable)
# ============================================

if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='FoxholeQuartermaster.app',
        icon='icon.icns' if os.path.exists('icon.icns') else None,
        bundle_identifier='com.foxhole.quartermaster',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '1.0.0',
        },
    )
