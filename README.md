# ERA5 Time Series Viewer - User Guide

## Overview
ERA5 Time Series Viewer is a standalone desktop application for loading, visualizing, and exporting ERA5 atmospheric and oceanic NetCDF data from Copernicus Climate Data Store.

**No Python installation required** - Simply run the executable!

## System Requirements
- **Operating System:** Windows 7 or later (64-bit)
- **Memory:** Minimum 4GB RAM (8GB recommended)
- **Disk Space:** 500MB for the application
- **Internet:** Not required after download

## Installation

### Option 1: Extract and Run (Simplest)
1. Download and extract `ERA5_TimeSeries_Viewer.zip`
2. Double-click `ERA5_TimeSeries_Viewer.exe`
3. Done! The application will launch.

### Option 2: Using the Installer
1. Download and run `ERA5_TimeSeries_Viewer_Setup.exe`
2. Follow the on-screen prompts
3. Click "Finish" to launch the application

## Getting Started

### Step 1: Load Data Files
1. Download ERA5 NetCDF files from [Copernicus CDS](https://cds.climate.copernicus.eu)
   - Atmospheric data: Search for "ERA5 single levels timeseries"
   - Oceanic data: Search for "ERA5 sea surface wave timeseries"
2. Click **"Select atmospheric file"** to load atmospheric NetCDF (.nc) file
3. Click **"Select oceanic file"** to load oceanic NetCDF (.nc) file

### Step 2: Select Data Source and Variable
1. Choose data source: **Atmospheric** or **Oceanic** (radio buttons)
2. Select a variable from the dropdown menu
3. Variables are automatically renamed for clarity:
   - `u10`, `v10` → Wind components (used to calculate Wind Speed & Direction)
   - `swh` → Significant Wave Height
   - `mwp` → Wave Period
   - `mwd` → Wave Direction
   - `msl` → Air Pressure
   - `tp` → Precipitation Rate

### Step 3: Plot and Analyze
1. Click **"Plot time series"** to generate a plot
2. **Interactive zoom:** Click and drag on the plot to zoom into a time range
3. **Subset sliders:** Use Start/End sliders to select a specific time range
4. Click **"Show statistics"** to display min, max, mean, standard deviation, and percentiles

### Step 4: Save Data
1. Use time sliders to select the range you want to export
2. Click **"Save data"** and choose file format:
   - **CSV** - Plain text format with headers and units (Excel-compatible)
   - **DFS0** - DHI MIKE format (for water modeling software)

**CSV Format:**
```
Time,Air pressure,Precipitation rate,...
,Pa,mm/hr,...
1940-01-01 00:00:00,101968.19,nan,...
```

**Units for each variable:**
- Air pressure: Pa (Pascals)
- Precipitation rate: mm/hr
- Wind speed/U velocity/V velocity: m/s (meters per second)
- Wave height: m (meters)
- Wave period: s (seconds)
- Wave/Wind direction: ° (degrees)

## Features

✓ **Load both atmospheric and oceanic ERA5 data simultaneously**
✓ **Automatic wind speed/direction calculation** from u10/v10 components
✓ **Interactive time series plotting** with zoom capability
✓ **Time range subsetting** with slider controls
✓ **Combined data export** - save atmospheric and oceanic data in one file
✓ **Multiple export formats** - CSV and DFS0/MIKE
✓ **Full statistics** - min, max, mean, standard deviation, percentiles
✓ **Save plots** as PNG or PDF
✓ **Professional variable naming** for technical and non-technical users

## Troubleshooting

### Application won't start
- Ensure you have Windows 7 or later (64-bit)
- Try running as Administrator: Right-click → "Run as administrator"
- Restart your computer

### "No data" error after loading files
- Verify the .nc files are valid ERA5 NetCDF files
- File must contain a time dimension (time, date, or valid_time)
- File must contain at least one data variable

### Plot appears empty
- Make sure you selected both a data source AND a variable
- Verify the time range sliders are set correctly
- Check that the variable contains numeric data

### Export fails
- Verify write permissions in the target folder
- Ensure sufficient disk space
- Try a different file location (e.g., Documents instead of Desktop)

## Data Format Details

### Supported Input Files
- **Format:** NetCDF (.nc)
- **Source:** Copernicus Climate Data Store ERA5 reanalysis data
- **Atmosphere:** Single-level fields (u10, v10, msl, tp, etc.)
- **Ocean:** Wave parameters (swh, mwp, mwd, etc.)

### Export Formats

**CSV (Comma-Separated Values)**
- Opens in Excel, LibreOffice, or any text editor
- Contains units in row 2
- Time format: YYYY-MM-DD HH:MM:SS

**DFS0 (MIKE Time Series)**
- Binary format for DHI MIKE modeling software
- Includes EUM (Engineering Units Manager) metadata
- Preserves variable types and units for water quality/hydrodynamic models

## Performance Tips

- Smaller files load and plot faster (subset by time in the CDS before downloading)
- When working with large files, use the time sliders to focus on specific periods
- Save to SSD for faster file operations

## File Locations

After installation, you can find:
- **Program files:** `C:\Program Files\ERA5_TimeSeries_Viewer\`
- **User data:** Create a folder for your NetCDF files (e.g., `C:\Users\YourName\Documents\ERA5_Data\`)
- **Exported files:** Save to any location you have write access to

## Contact & Support

For issues or feature requests, refer to the technical documentation or contact your system administrator.

---

**Version:** 1.0  
**Last Updated:** June 2026  
**License:** See LICENSE.txt in program folder
