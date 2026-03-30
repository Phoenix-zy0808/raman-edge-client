# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

# 获取项目根目录（main.spec 所在目录）
BASE_DIR = Path(__file__).parent

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (str(BASE_DIR / 'resources.qrc'), '.'),  # Qt 资源文件
        (str(BASE_DIR / 'backend' / 'model_config.json'), 'backend'),
    ],
    hiddenimports=[
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtWebChannel',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineCore',
        'numpy',
        'scipy',
        'scipy.interpolate',
    ],
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
    name='RamanEdgeClient',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
