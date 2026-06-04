@echo off
REM ERA5 TimeSeries Viewer Launcher
REM This batch file launches the application

setlocal enabledelayedexpansion

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"

REM Check if the executable exists
if not exist "%SCRIPT_DIR%ERA5_TimeSeries_Viewer.exe" (
    echo.
    echo ERROR: ERA5_TimeSeries_Viewer.exe not found!
    echo.
    echo Please make sure the executable is in the same folder as this script.
    echo Expected location: %SCRIPT_DIR%ERA5_TimeSeries_Viewer.exe
    echo.
    pause
    exit /b 1
)

REM Launch the application
echo Launching ERA5 TimeSeries Viewer...
start "" "%SCRIPT_DIR%ERA5_TimeSeries_Viewer.exe"

exit /b 0
