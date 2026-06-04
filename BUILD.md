# ERA5 TimeSeries Viewer - Build & Deployment Guide

This guide is for developers who want to build the standalone executable and installer.

## Prerequisites

You need the following installed on your development machine:
- Python 3.9 or later
- Windows 10 or later (64-bit)

## Step 1: Setup Development Environment

### 1.1 Create Python Virtual Environment
```batch
python -m venv venv
venv\Scripts\activate
```

### 1.2 Install Build Dependencies
```batch
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
```

## Step 2: Build Standalone Executable

### 2.1 Create PyInstaller Spec File
The `era5_build.spec` file is already provided.

### 2.2 Build the Executable
```batch
pyinstaller era5_build.spec
```

This creates:
- `dist/ERA5_TimeSeries_Viewer.exe` - The standalone executable
- `dist/ERA5_TimeSeries_Viewer/` - Supporting libraries and files

### 2.3 Test the Executable
```batch
dist\ERA5_TimeSeries_Viewer.exe
```

The application should launch without requiring Python to be installed.

## Step 3: Create Distribution Package (Optional)

### 3.1 Simple ZIP Distribution
```batch
cd dist
7z a -r ERA5_TimeSeries_Viewer.zip ERA5_TimeSeries_Viewer.exe ERA5_TimeSeries_Viewer\*
```

Or using Windows built-in compression:
1. Select `ERA5_TimeSeries_Viewer.exe` and the `ERA5_TimeSeries_Viewer` folder
2. Right-click → Send to → Compressed (zipped) folder
3. Name it `ERA5_TimeSeries_Viewer.zip`

Users can extract and run the .exe directly.

## Step 4: Create Windows Installer (Optional)

### 4.1 Install NSIS
Download and install NSIS from: https://nsis.sourceforge.io/

### 4.2 Build Installer
```batch
"C:\Program Files (x86)\NSIS\makensis.exe" era5_installer.nsi
```

This creates `ERA5_TimeSeries_Viewer_Setup.exe` - a professional installer.

### 4.3 Test the Installer
1. Run `ERA5_TimeSeries_Viewer_Setup.exe`
2. Follow prompts to install
3. Launch from Start Menu or Desktop shortcut
4. Verify all features work
5. Test uninstall: Settings → Apps → ERA5 TimeSeries Viewer → Uninstall

## File Structure for Distribution

### Option A: Simple ZIP
```
ERA5_TimeSeries_Viewer.zip
├── ERA5_TimeSeries_Viewer.exe
├── ERA5_TimeSeries_Viewer/
│   ├── (all supporting files)
├── README.md
└── QUICK_START.txt
```

### Option B: Installer
```
ERA5_TimeSeries_Viewer_Setup.exe
README.md
QUICK_START.txt
LICENSE.txt
```

## Troubleshooting Build Issues

### Issue: PyInstaller can't find mikeio
**Solution:** Add to hidden imports in spec file:
```python
hiddenimports=['mikeio', 'mikeio.eum._eum', ...]
```

### Issue: Executable is too large (>500MB)
**Solution:** This is normal for PyInstaller bundles. Optimize with UPX:
```bash
pip install upx
pyinstaller --upx-dir=path\to\upx era5_build.spec
```

### Issue: "No module named tkinter"
**Solution:** tkinter is included in Python, but on some Linux systems:
```bash
sudo apt-get install python3-tk  # Linux
```

For Windows, ensure tkinter was selected during Python installation.

### Issue: Application crashes on startup
**Solution:** Run with console to see errors:
```python
# In era5_build.spec, change:
console=False  # Change to True
```
Rebuild and test to see error messages.

## Release Checklist

- [ ] Test with fresh Windows installation (VM)
- [ ] Verify no Python installation required
- [ ] Test all buttons and features
- [ ] Load sample ERA5 files successfully
- [ ] Export CSV format works
- [ ] Export DFS0 format works
- [ ] Plot zoom/pan works
- [ ] Statistics display works correctly
- [ ] Close application cleanly (no crashes)
- [ ] Test uninstaller removes all files
- [ ] Documentation is clear and complete
- [ ] README.md is included in distribution

## Release Package Contents

### For End Users
1. `ERA5_TimeSeries_Viewer_Setup.exe` or `.zip`
2. `README.md` - User guide
3. `QUICK_START.txt` - Quick reference
4. `LICENSE.txt` - License information

### For Support/Developers
5. `BUILD.md` - This file
6. Source code repository link
7. Contact information

## Distribution Channels

You can distribute the executable through:
1. **Direct download** - Host on website or cloud storage
2. **GitHub Releases** - Upload `.exe` and `.zip` to releases
3. **Package managers**:
   - Windows Package Manager: `winget install ERA5TimeSeries`
   - Chocolatey: `choco install era5timeseries`
   - Microsoft Store: Submit for Store listing

## Version Updates

When releasing updates:
1. Increment version in `era5_build.spec` comments
2. Update `README.md` with new features
3. Tag release in git: `git tag v1.0.1`
4. Rebuild executable
5. Create new installer
6. Publish release notes

## Performance Optimization

For faster startup time:
- Compiled with PyInstaller's default settings
- All dependencies are bundled
- First launch may be slower (Windows security scan)
- Subsequent launches will be faster

## Support

For build issues, check:
- PyInstaller documentation: https://pyinstaller.org/
- NSIS documentation: https://nsis.sourceforge.io/
- ERA5 Copernicus: https://cds.climate.copernicus.eu/

---

**Build Date:** June 2026
**Python Version Used:** 3.9+
**PyInstaller Version Used:** Latest
