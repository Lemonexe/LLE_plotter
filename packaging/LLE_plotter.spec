# Build this same spec on Linux and Windows; cross-compilation is not supported.
from pathlib import Path
import sys

root = Path(SPECPATH).parent
analysis = Analysis(
    [str(root / 'launch.py')],
    pathex=[str(root)],
    datas=[(str(root / 'lle_plotter' / 'icon.ico'), 'lle_plotter')],
    hiddenimports=['matplotlib.backends.backend_svg', 'matplotlib.backends.backend_pdf'],
    hookspath=[], hooksconfig={'matplotlib': {'backends': ['QtAgg', 'Agg', 'svg', 'pdf']}},
    excludes=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtQml',
              'PySide6.QtQuick', 'tkinter'],
    noarchive=False,
)
pyz = PYZ(analysis.pure)
exe = EXE(pyz, analysis.scripts, [], exclude_binaries=True, name='LLE_plotter',
          debug=False, strip=False, upx=False, console=False,
          icon=str(root / 'lle_plotter' / 'icon.ico') if sys.platform == 'win32' else None)
coll = COLLECT(exe, analysis.binaries, analysis.datas, strip=False, upx=False, name='LLE_plotter')
