# -*- mode: python ; coding: utf-8 -*-
# packaging/rtl_scan.spec — PyInstaller 打包配置
#
# 产出: dist/rtl_scan (单一可执行文件)
# 兼容: Docker 构建 → CentOS 7+ (glibc >= 2.17)
#       本地构建 → 当前系统 glibc 及以上

import os
from pathlib import Path

block_cipher = None

# spec 在 packaging/ 下，项目根在上一级
ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(ROOT / 'src' / '__main__.py')],
    pathex=[str(ROOT)],
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
