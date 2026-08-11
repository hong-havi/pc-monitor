@echo off
REM 프로젝트 루트로 이동
cd /d "%~dp0.."

echo === PC Monitor - Library Setup ===
echo.
echo This script downloads required libraries for building.
echo Requires: curl (included in Windows 10+), tar
echo.

REM === Configuration ===
set LHM_NUGET_VER=0.9.4
set HIDSHARP_VER=2.1.0
set LHM_RELEASE_VER=0.9.6
set LHM_RELEASE_URL=https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases/download/v%LHM_RELEASE_VER%/LibreHardwareMonitor-net472.zip

REM === Create lib directory ===
if not exist "lib" mkdir lib

REM ============================
REM 1. LibreHardwareMonitorLib (NuGet) - for DLL direct loading
REM ============================
echo [1/3] Downloading LibreHardwareMonitorLib %LHM_NUGET_VER% from NuGet...
if not exist "lib\lhm\lib\net472\LibreHardwareMonitorLib.dll" (
    if not exist "lib\lhm" mkdir lib\lhm
    curl -sL "https://www.nuget.org/api/v2/package/LibreHardwareMonitorLib/%LHM_NUGET_VER%" -o lib\lhm.nupkg.zip
    tar -xf lib\lhm.nupkg.zip -C lib\lhm
    del lib\lhm.nupkg.zip
    echo   Done.
) else (
    echo   Already exists, skipping.
)

REM ============================
REM 2. HidSharp (NuGet) - LHM dependency
REM ============================
echo [2/3] Downloading HidSharp %HIDSHARP_VER% from NuGet...
if not exist "lib\hidsharp\lib\net35\HidSharp.dll" (
    if not exist "lib\hidsharp" mkdir lib\hidsharp
    curl -sL "https://www.nuget.org/api/v2/package/HidSharp/%HIDSHARP_VER%" -o lib\hidsharp.nupkg.zip
    tar -xf lib\hidsharp.nupkg.zip -C lib\hidsharp
    del lib\hidsharp.nupkg.zip
    echo   Done.
) else (
    echo   Already exists, skipping.
)

REM ============================
REM 3. LibreHardwareMonitor 0.9.6 (GitHub Release) - for auto-launch with HTTP server
REM ============================
echo [3/3] Downloading LibreHardwareMonitor %LHM_RELEASE_VER% from GitHub...
if not exist "lib\lhm-096\LibreHardwareMonitor.exe" (
    if not exist "lib\lhm-096" mkdir lib\lhm-096
    curl -sL "%LHM_RELEASE_URL%" -o lib\lhm-096.zip
    tar -xf lib\lhm-096.zip -C lib\lhm-096
    del lib\lhm-096.zip
    echo   Done.
) else (
    echo   Already exists, skipping.
)

echo.
echo === Setup complete! ===
echo.
echo Libraries installed:
echo   lib\lhm\lib\net472\LibreHardwareMonitorLib.dll
echo   lib\hidsharp\lib\net35\HidSharp.dll
echo   lib\lhm-096\LibreHardwareMonitor.exe
echo.
echo You can now run scripts\build.bat to build the exe.
pause
