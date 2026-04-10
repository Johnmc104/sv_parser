# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for rtl_scan binary.

Build:  pyinstaller rtl_scan.spec --clean
Output: dist/rtl_scan
"""

import os

block_cipher = None
project_root = os.path.abspath('.')

a = Analysis(
    ['src/__main__.py'],
    pathex=[project_root],
    binaries=[],
    datas=[],
    hiddenimports=[
        'src',
        'src.port_classify',
        'src.data_model',
        'src.preprocessor',
        'src.ast_utils',
        'src.extractors',
        'src.verilog_parser',
        'src.file_discovery',
        'src.hierarchy',
        'src.rtl_scan',
        'src.formatter',
        'verilog',
        'verilog.VerilogLexer',
        'verilog.VerilogParser',
        'verilog.VerilogParserVisitor',
        'antlr4',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Not needed at runtime
        'systemverilog',
        'verilog.VerilogPreParser',
        'verilog.VerilogPreParserVisitor',
        'tkinter',
        'unittest',
        'pytest',
        'pip',
        'setuptools',
    ],
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
    name='rtl_scan',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=True,
)
