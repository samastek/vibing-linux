# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import copy_metadata

block_cipher = None

# Identify current platform's factory to always include
hidden_imports = [
    'vibing.platform.macos.factory',
    'vibing.platform.linux.factory'
]

# Include the entry points metadata for importlib.metadata to find our platform plugins
metadata_datas = copy_metadata('vibing-linux')

a = Analysis(
    ['vibing/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('vibing/platform', 'vibing/platform'),
        ('vibing/providers', 'vibing/providers')
    ] + metadata_datas,
    hiddenimports=hidden_imports,
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
    name='Vibing',
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Vibing',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Vibing.app',
        icon=None,
        bundle_identifier='com.vibing.macos',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'LSUIElement': 'True', # Hides the app from the Dock (useful for menu bar/tray apps)
            'NSMicrophoneUsageDescription': 'Vibing needs access to your microphone to record your voice.',
            'NSAppleEventsUsageDescription': 'Vibing needs access to paste text into your active applications.',
        },
    )
