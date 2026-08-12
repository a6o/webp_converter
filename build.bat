@echo off
setlocal
cd /d "%~dp0"

echo Building WebP Converter with drag-drop support...
echo.

REM Use the project virtualenv, not whatever "python" happens to be on PATH
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" (
    echo ERROR: virtualenv not found at "%PY%"
    echo.
    echo Create it first:
    echo     py -3.13 -m venv .venv
    echo     .venv\Scripts\python -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

"%PY%" -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed in .venv
    echo     .venv\Scripts\python -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Clean up old build output
if exist "dist\WebP_Converter.exe" del /f /q "dist\WebP_Converter.exe"
if exist "build" rmdir /s /q "build"

REM Build with PyInstaller.
REM tkinterdnd2's tkdnd binaries are bundled automatically by the
REM hook in pyinstaller-hooks-contrib, so they need no --add-data here.
"%PY%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name "WebP_Converter" ^
    --add-data "lang;lang" ^
    --hidden-import pillow_heif ^
    --hidden-import tkinterdnd2 ^
    --hidden-import about_dialog ^
    --hidden-import lang_manager ^
    --hidden-import config_manager ^
    --hidden-import dpi_helper ^
    webp_converter.py

if errorlevel 1 (
    echo.
    echo Build failed: PyInstaller exited with an error.
    pause
    exit /b 1
)

echo.
if exist "dist\WebP_Converter.exe" (
    echo Build successful! Executable created at: dist\WebP_Converter.exe
    dir "dist\WebP_Converter.exe"
) else (
    echo Build failed: dist\WebP_Converter.exe was not produced.
    pause
    exit /b 1
)

pause
