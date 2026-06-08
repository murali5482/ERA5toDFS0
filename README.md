# ERA5 Time Series Viewer - User Guide

## Overview
ERA5 Time Series Viewer is a standalone desktop application for loading, visualizing, and exporting ERA5 atmospheric and oceanic NetCDF data from Copernicus Climate Data Store.

**No Python installation required** - Simply run the executable!

## System Requirements
- **Operating System:** Windows 7 or later (64-bit)
- **Memory:** Minimum 4GB RAM (8GB recommended)
- **Disk Space:** 500MB for the application
- **Internet:** Required for direct Copernicus CDS downloads; not required when using local NetCDF files

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

### Step 1: Download or Load Data Files

**Option A: Download directly from Copernicus CDS**
1. Log in to Copernicus CDS and accept the licence/terms for [ERA5 hourly time-series data on single levels](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries?tab=download).
2. In the application, enter your CDS API URL and API key / personal access token.
3. Click **Save settings** if you want to store the API settings for future sessions.
4. Enter latitude/longitude manually, or click the OpenStreetMap-based map to choose a point. Use **+**, **-**, mouse wheel, **Center**, and **World** to navigate; maximum zoom reaches a local view of about 3 degrees.
5. Select the date range, variables, and download folder.
6. Click **Request and download**. The application waits for CDS to prepare the request, downloads the NetCDF result, extracts any ZIP result, and loads the data.

**Option B: Load existing NetCDF files**
1. Click **"Select atmospheric file"** to load atmospheric NetCDF (.nc) file.
2. Click **"Select oceanic file"** to load oceanic NetCDF (.nc) file.

### Step 2: Select Data Source and Variable
1. Open the **Data analysis** tab.
2. Choose data source: **Atmospheric** or **Oceanic** (radio buttons)
3. Select a variable from the dropdown menu
3. Variables are automatically renamed for clarity:
   - `u10`, `v10` → Wind components (used to calculate Wind Speed & Direction)
   - `swh` → Significant Wave Height
   - `mwp` → Wave Period
   - `mwd` → Wave Direction
   - `msl` → Air Pressure
   - `tp` → Precipitation Rate

### Step 3: Plot and Analyze
1. Click **"Plot time series"** to generate a plot
2. Use **Start Date** and **End Date** in the top analysis panel to choose the period used for plotting, statistics, rose plots, directional DFS0 export, and saved data
3. **Interactive zoom:** Click and drag on the plot to zoom into a visible time range; the compact statistics panel updates for the displayed data
4. Click **"Show statistics"** to display min, max, mean, standard deviation, and percentiles for the selected dates
5. Click **Wave Rose** or **Wind Rose** to plot all-years and representative-year directional roses for the selected dates
6. Click **Directional Data** to create 16 sector-filtered DFS0 files for the selected parameter and selected dates

### Step 4: Save Data
1. Use **Start Date** and **End Date** in the Data analysis tab to select the range you want to export
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
✓ **Direct Copernicus CDS download** for ERA5 point time-series NetCDF data
✓ **Zoomable OpenStreetMap coordinate picker** with manual latitude/longitude entry
✓ **One-time CDS API settings** for API URL and personal access token
✓ **Automatic wind speed/direction calculation** from u10/v10 components
✓ **Interactive time series plotting** with zoom capability
✓ **Time range subsetting** with top Start Date / End Date controls
✓ **Wave and wind rose plots** with 16 directional sectors
✓ **Representative calendar year ranking** saved as CSV for wave and wind roses
✓ **Directional DFS0 export** - 16 sector files with non-sector data written as delete/missing values
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

### CDS download fails
- Confirm that `cdsapi>=0.7.7` is installed or bundled in the executable
- Confirm your CDS API key / personal access token is correct
- Log in to the CDS website and accept the dataset terms before using the API
- Try a smaller date range or fewer variables if CDS queueing is slow

### Map tiles do not appear
- The coordinate picker downloads OpenStreetMap tiles on first use and caches them in the application settings folder
- If internet access is blocked, the latitude/longitude grid and manual coordinate entry still work

### Plot appears empty
- Make sure you selected both a data source AND a variable
- Verify Start Date and End Date are inside the loaded data range
- Check that the variable contains numeric data

### Export fails
- Verify write permissions in the target folder
- Ensure sufficient disk space
- Try a different file location (e.g., Documents instead of Desktop)

### Rose plot or directional export unavailable
- Wave Rose requires significant wave height and mean wave direction
- Wind Rose requires 10m U/V wind components so wind speed and direction can be calculated
- Directional Data requires a selected parameter plus a matching direction variable in the same source

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
- When working with large files, use the Start Date and End Date controls to focus on specific periods
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
