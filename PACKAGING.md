# ERA5 TimeSeries Viewer - Packaging & Distribution Guide

This guide explains how to package the standalone application for end users.

## What You Have

After building with PyInstaller, you have:
```
ERA5/
├── dist/
│   ├── ERA5_TimeSeries_Viewer.exe      (Main executable)
│   └── ERA5_TimeSeries_Viewer/          (Supporting files)
├── era5_build.spec                      (Build configuration)
├── era5_installer.nsi                   (Installer configuration)
├── README.md                            (User manual)
├── BUILD.md                             (Developer guide)
├── QUICK_START.txt                      (Quick reference)
├── LICENSE.txt                          (License)
└── Run_ERA5_Viewer.bat                  (Launcher script)
```

## Distribution Options

### OPTION A: Simple ZIP Distribution (Easiest)

This is the simplest way to distribute to end users.

**Step 1: Create package folder**
```batch
mkdir ERA5_TimeSeries_Viewer_v1.0
```

**Step 2: Copy files**
```batch
copy dist\ERA5_TimeSeries_Viewer.exe ERA5_TimeSeries_Viewer_v1.0\
xcopy dist\ERA5_TimeSeries_Viewer ERA5_TimeSeries_Viewer_v1.0\ERA5_TimeSeries_Viewer /I /E
copy README.md ERA5_TimeSeries_Viewer_v1.0\
copy QUICK_START.txt ERA5_TimeSeries_Viewer_v1.0\
copy LICENSE.txt ERA5_TimeSeries_Viewer_v1.0\
copy Run_ERA5_Viewer.bat ERA5_TimeSeries_Viewer_v1.0\
```

**Step 3: Create ZIP**
- Right-click `ERA5_TimeSeries_Viewer_v1.0` folder
- Select "Send to" → "Compressed (zipped) folder"
- Result: `ERA5_TimeSeries_Viewer_v1.0.zip`

**Step 4: Distribute**
- Upload `ERA5_TimeSeries_Viewer_v1.0.zip` to your hosting
- Users extract the ZIP
- Users double-click `ERA5_TimeSeries_Viewer.exe` or `Run_ERA5_Viewer.bat`

**File size:** ~300-500 MB (depending on library sizes)

### OPTION B: Professional Installer (Recommended)

This creates a Windows installer (.exe) for a professional distribution.

**Step 1: Install NSIS**
- Download from: https://nsis.sourceforge.io/
- Run installer, select all options

**Step 2: Build installer**
```batch
"C:\Program Files (x86)\NSIS\makensis.exe" era5_installer.nsi
```

**Step 3: Result**
- Creates: `ERA5_TimeSeries_Viewer_Setup.exe` (~300-400 MB)

**Step 4: Distribute**
- Upload `ERA5_TimeSeries_Viewer_Setup.exe`
- Users run the installer
- Automatically creates:
  - Start Menu shortcuts
  - Desktop shortcut
  - Program Files folder
  - Uninstall option

### OPTION C: Windows Package Manager

For advanced distribution, register with:
- **Windows Package Manager**: `winget install ERA5TimeSeries`
- **Chocolatey**: `choco install era5timeseries`
- **Microsoft Store**: Professional submission process

See https://learn.microsoft.com/en-us/windows/package-manager/ for details.

## File Size Optimization

The standalone executable includes all Python dependencies. Here's typical sizing:

```
Base libraries:         ~150 MB
NumPy + SciPy:         ~100 MB
Pandas:                ~50 MB
Matplotlib:            ~30 MB
Tkinter:               ~20 MB
xarray:                ~5 MB
mikeio:                ~10 MB
PyInstaller overhead:  ~30 MB
─────────────────────────────
Total:                 ~395 MB
```

**To reduce size:**
1. Remove unused matplotlib backends
2. Use UPX compression (see BUILD.md)
3. Exclude optional libraries

## System Requirements Documentation

**For End Users:**
```
Minimum Requirements:
- Operating System: Windows 7 64-bit or later
- Processor: 1 GHz (dual-core recommended)
- RAM: 4 GB (8 GB for large files)
- Storage: 500 MB free space
- Monitor: 1024x768 resolution minimum

No Python installation required!
No additional software needed!
```

## Pre-Distribution Checklist

Test on a clean Windows machine:

- [ ] Download the distributed file (ZIP or EXE)
- [ ] Extract/Install on clean Windows 10 VM
- [ ] Application launches successfully
- [ ] Load sample ERA5 files
- [ ] Plot functions work correctly
- [ ] Save to CSV format works
- [ ] Save to DFS0 format works
- [ ] Statistics display is accurate
- [ ] Time slider zoom works
- [ ] Application closes without crashes
- [ ] All documentation files are included
- [ ] README.md is accurate and helpful
- [ ] QUICK_START.txt is clear

## Distribution Channels

### Channel 1: Direct Download
- Host on personal website
- Services: Google Drive, Dropbox, OneDrive
- GitHub Releases: https://github.com

**Pros:** Full control, no review process
**Cons:** Need to host files, manage versions

### Channel 2: GitHub Releases
1. Create GitHub repository
2. Tag release: `git tag v1.0`
3. Upload `ERA5_TimeSeries_Viewer_Setup.exe`
4. Create release notes

```markdown
# ERA5 TimeSeries Viewer v1.0

Standalone Windows application for ERA5 data visualization.

## New Features
- Time series plotting with zoom
- CSV and DFS0 export
- Combined atmospheric/oceanic export

## Download
- [Setup Installer](ERA5_TimeSeries_Viewer_Setup.exe) - 400 MB
- [Portable ZIP](ERA5_TimeSeries_Viewer_v1.0.zip) - 400 MB

## Installation
Extract ZIP or run Setup.exe

## Requirements
Windows 7 or later (64-bit)
No Python required!
```

### Channel 3: University/Organization Portal
- Post on institutional software portal
- Include:
  - Installation guide
  - Quick start guide
  - Support contact information
  - License details

## Update Distribution

For future updates:

1. **Version numbering**: v1.0, v1.1, v1.2, v2.0
2. **Release notes**: Document changes
3. **Backward compatibility**: Ensure old files still open
4. **Migration path**: Help users upgrade

**Update checklist:**
```
v1.0 → v1.1 (patch)
├── Increment version in spec file
├── Update README.md
├── Rebuild executable
├── Create installer
├── Tag git: v1.1
├── Create release notes
└── Publish to all channels
```

## Support Resources to Include

**README.md sections:**
- Getting Started
- Feature Overview
- Troubleshooting
- Contact Information

**QUICK_START.txt:**
- 5-minute tutorial
- Common shortcuts
- FAQ

**Included files:**
- LICENSE.txt - Legal information
- requirements.txt - For developers
- BUILD.md - Build instructions

**Online resources:**
- ERA5 Data: https://cds.climate.copernicus.eu
- Python Issues: GitHub Issues page
- MIKE Software: https://www.dhigroup.com

## Launch Sequence

When user runs the application:

1. Windows checks executable integrity
2. First run: Unpacks dependencies (~15-30 seconds)
3. Subsequent runs: Cached, faster startup
4. Tkinter creates main window
5. Application ready for data loading

**Typical startup time:**
- First run: 20-30 seconds
- Subsequent runs: 5-10 seconds

## Security Notes

**Code signing (Optional):**
- Sign executable with certificate
- Reduces Windows SmartScreen warnings
- Costs: $300-500/year per certificate

**Reputation:**
- First downloads may trigger Windows Defender
- False positive: Application is safe
- Reputation improves after many downloads

## Final Checklist Before Release

- [ ] Version number consistent everywhere
- [ ] README.md reviewed and complete
- [ ] QUICK_START.txt tested by non-technical user
- [ ] All dependencies included in executable
- [ ] No personal data in distribution
- [ ] Source code backed up in Git
- [ ] License file included
- [ ] Tested on multiple Windows versions
- [ ] Performance acceptable on target systems
- [ ] Uninstaller works cleanly (if using installer)
- [ ] Support contact information provided
- [ ] Release notes prepared
- [ ] Distribution channel tested

## Troubleshooting Distribution Issues

**Issue: Antivirus warns about executable**
- Solution: Code signing + reputation building

**Issue: File too large**
- Solution: Use UPX compression or cloud hosting

**Issue: Users don't know how to extract ZIP**
- Solution: Use NSIS installer instead

**Issue: DLL errors on user's machine**
- Solution: Ensure PyInstaller bundled all dependencies

---

**Packaging Guide Version:** 1.0
**Last Updated:** June 2026
