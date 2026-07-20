# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Matplotlib backend for tkinter embedding
        'matplotlib.backends.backend_tkagg',
        # scipy sub-modules imported dynamically
        'scipy.special._ufuncs_cxx',
        'scipy.linalg._fblas',
        'scipy.linalg._flapack',
        'scipy.sparse.csgraph._validation',
        # pandas internal modules
        'pandas._libs.tslibs.np_datetime',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # pandas optional IO backends (not used by this app)
        'sqlalchemy', 'sqlalchemy.engine', 'sqlalchemy.sql',
        'xlsxwriter', 'openpyxl', 'xlrd', 'pyxlsb', 'odf',
        'pyarrow', 'tables', 'lxml', 'html5lib', 'bs4',
        'sphinx', 'pytest', 'jinja2', 'IPython',
        # Unused matplotlib backends
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_webagg',
        'matplotlib.backends.backend_wxagg',
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'tornado',
    ],
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
    name='IS3Pro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app_icon.png'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='IS3Pro',
)
