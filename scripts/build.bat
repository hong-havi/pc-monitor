@echo off
REM 프로젝트 루트로 이동
cd /d "%~dp0.."

echo === PC Monitor Dashboard Build ===
echo.

REM 기존 프로세스 종료
taskkill /F /IM PCMonitor.exe >nul 2>&1
timeout /t 1 /nobreak >nul

REM lib 폴더 체크
if not exist "lib\lhm-096\LibreHardwareMonitor.exe" (
    echo ERROR: lib folder not found. Run scripts\setup_libs.bat first!
    pause
    exit /b 1
)

echo Building exe...
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "PCMonitor" ^
    --paths src ^
    --add-data "lib/lhm-096;lhm" ^
    --add-data "lib/lhm/lib/net472;lib" ^
    --add-data "lib/hidsharp/lib/net35;lib" ^
    --hidden-import wmi ^
    --hidden-import pythoncom ^
    --hidden-import win32com ^
    --hidden-import clr ^
    --hidden-import clr_loader ^
    --distpath dist ^
    --workpath build/PCMonitor ^
    --specpath . ^
    -y ^
    src/main.py

echo.
if exist "dist\PCMonitor.exe" (
    echo Build complete! Output: dist\PCMonitor.exe
) else (
    echo Build FAILED!
)
pause
