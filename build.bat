@echo off
echo === PC Monitor Dashboard Build ===
echo.

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
