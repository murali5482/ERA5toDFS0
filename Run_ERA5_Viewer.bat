@echo off
REM ERA5 TimeSeries Viewer Launcher
REM This batch file launches the application

setlocal enabledelayedexpansion

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
set "APP_EXE=%SCRIPT_DIR%ERA5_TimeSeries_Viewer.exe"

REM Prefer newer executables if present.
if exist "%SCRIPT_DIR%ERA5_TimeSeries_Viewer_updated.exe" (
    set "APP_EXE=%SCRIPT_DIR%ERA5_TimeSeries_Viewer_updated.exe"
)

if exist "%SCRIPT_DIR%ERA5_TimeSeries_Viewer_analysis.exe" (
    set "APP_EXE=%SCRIPT_DIR%ERA5_TimeSeries_Viewer_analysis.exe"
)

if exist "%SCRIPT_DIR%ERA5_TimeSeries_Tool.exe" (
    set "APP_EXE=%SCRIPT_DIR%ERA5_TimeSeries_Tool.exe"
)

REM Check if the executable exists
if not exist "%APP_EXE%" (
    echo.
    echo ERROR: ERA5 TimeSeries Viewer executable not found!
    echo.
    echo Please make sure the executable is in the same folder as this script.
    echo Expected location: %APP_EXE%
    echo.
    pause
    exit /b 1
)

REM Launch the application
echo Launching ERA5 TimeSeries Viewer...
start "" "%APP_EXE%"

exit /b 0
