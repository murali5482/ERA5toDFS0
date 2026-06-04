; NSIS Installer Script for ERA5 Time Series Viewer
; Requires: NSIS (nullsoft scriptable install system)
; Download from: https://nsis.sourceforge.io/
; Build with: makensis era5_installer.nsi

!include "MUI2.nsh"

; Basic settings
Name "ERA5 TimeSeries Viewer"
OutFile "ERA5_TimeSeries_Viewer_Setup.exe"
InstallDir "$PROGRAMFILES\ERA5_TimeSeries_Viewer"
InstallDirRegKey HKCU "Software\ERA5_TimeSeries_Viewer" ""

; Request admin privileges for system-wide installation
RequestExecutionLevel admin

; UI Settings
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; Installation section
Section "Install"
  SetOutPath "$INSTDIR"
  
  ; Copy main executable
  File "dist\ERA5_TimeSeries_Viewer.exe"
  
  ; Copy README and supporting files
  File "README.md"
  File "requirements.txt"
  
  ; Create Start Menu shortcuts
  SetShellVarContext all
  CreateDirectory "$SMPROGRAMS\ERA5_TimeSeries_Viewer"
  CreateShortcut "$SMPROGRAMS\ERA5_TimeSeries_Viewer\ERA5_TimeSeries_Viewer.lnk" "$INSTDIR\ERA5_TimeSeries_Viewer.exe"
  CreateShortcut "$SMPROGRAMS\ERA5_TimeSeries_Viewer\README.lnk" "$INSTDIR\README.md"
  CreateShortcut "$SMPROGRAMS\ERA5_TimeSeries_Viewer\Uninstall.lnk" "$INSTDIR\uninstall.exe"
  
  ; Create Desktop shortcut
  CreateShortcut "$DESKTOP\ERA5_TimeSeries_Viewer.lnk" "$INSTDIR\ERA5_TimeSeries_Viewer.exe"
  
  ; Write registry keys for uninstall
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ERA5_TimeSeries_Viewer" "DisplayName" "ERA5 TimeSeries Viewer"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ERA5_TimeSeries_Viewer" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ERA5_TimeSeries_Viewer" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ERA5_TimeSeries_Viewer" "DisplayVersion" "1.0"
  
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"
  
  ; Show completion message
  MessageBox MB_OK "ERA5 TimeSeries Viewer has been installed successfully.$\n$\nYou can now launch it from the Start Menu or Desktop shortcut."
SectionEnd

; Uninstaller section
Section "Uninstall"
  SetShellVarContext all
  
  ; Remove shortcuts
  RMDir /r "$SMPROGRAMS\ERA5_TimeSeries_Viewer"
  Delete "$DESKTOP\ERA5_TimeSeries_Viewer.lnk"
  
  ; Remove files
  Delete "$INSTDIR\ERA5_TimeSeries_Viewer.exe"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\requirements.txt"
  Delete "$INSTDIR\uninstall.exe"
  
  ; Remove directory
  RMDir "$INSTDIR"
  
  ; Remove registry keys
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ERA5_TimeSeries_Viewer"
  DeleteRegKey HKCU "Software\ERA5_TimeSeries_Viewer"
SectionEnd
