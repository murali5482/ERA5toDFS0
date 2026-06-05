# PyInstaller spec file for ERA5 TimeSeries GUI
# Build with: pyinstaller era5_build.spec
#
# mikeio/mikecore need their package metadata, Python modules, data files,
# and native DHI DLLs available in the extracted PyInstaller runtime.
from PyInstaller.utils.hooks import collect_all

block_cipher = None

datas = []
binaries = []
hiddenimports = []

for package_name in ('mikeio', 'mikecore'):
    package_datas, package_binaries, package_hiddenimports = collect_all(package_name)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

a = Analysis(
    ['era5_timeseries_gui.py'],
    pathex=[r'C:\Users\surisemk\Documents\GitHub\ERA5\build_env\Lib\site-packages'],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        'tkinter',
        'xarray',
        'numpy',
        'pandas',
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'netCDF4',
    ] + hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
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
    name='ERA5_TimeSeries_Viewer',
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
    icon=None,
)
