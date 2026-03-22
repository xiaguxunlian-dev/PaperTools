# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

ROOT = Path(SPECPATH)          # 仓库根目录

a = Analysis(
    [str(ROOT / 'main_gui.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # 将所有子模块目录打进 exe
        (str(ROOT / 'scripts'),    'scripts'),
        (str(ROOT / 'config.py'),  '.'),
        (str(ROOT / 'search'),     'search'),
        (str(ROOT / 'assess'),     'assess'),
        (str(ROOT / 'synthesize'), 'synthesize'),
        (str(ROOT / 'write'),      'write'),
        (str(ROOT / 'meta'),       'meta'),
        (str(ROOT / 'kg'),         'kg'),
    ],
    hiddenimports=[
        # 所有内部模块
        'config',
        'search.federated', 'search.arxiv', 'search.pubmed',
        'search.semantic', 'search.crossref', 'search.openalex',
        'search.bgpt',
        'assess.grade', 'assess.rob2', 'assess.robins', 'assess.jbi',
        'synthesize.pico', 'synthesize.evidence_table', 'synthesize.prisma',
        'write.imrad', 'write.references',
        'meta.analyzer', 'meta.effect_size', 'meta.forest_plot', 'meta.heterogeneity',
        'kg.builder', 'kg.extractor',
        # 外部依赖
        'feedparser', 'feedparser.api', 'feedparser.encodings',
        'feedparser.namespaces', 'feedparser.parsers',
        'tkinter', 'tkinter.ttk', 'tkinter.scrolledtext',
        'urllib', 'urllib.request', 'urllib.parse', 'urllib.error',
        'xml', 'xml.etree', 'xml.etree.ElementTree',
        'json', 'dataclasses', 'pathlib', 'threading', 'queue',
        'subprocess', 'io', 'os', 'sys', 'math', 'statistics',
        'collections', 'itertools', 'functools', 'datetime',
        'hashlib', 'base64', 'struct', 'copy', 're', 'textwrap',
        'http', 'http.client', 'email', 'email.message',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'PIL',
              'cv2', 'torch', 'tensorflow', 'pytest'],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PaperTools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # 不显示黑色控制台窗口（GUI 模式）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version=None,
    uac_admin=False,
    uac_uiaccess=False,
)
