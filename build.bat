@echo off
echo Building WebP Converter with drag-drop support...
echo.

REM Clean up old files
if exist "dist\WebP_Converter.exe" del /f "dist\WebP_Converter.exe"
if exist "build" rmdir /s /q "build"

REM Build with PyInstaller
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "WebP_Converter" ^
    --add-data "C:\Users\%USERNAME%\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\tkinterdnd2;tkinterdnd2" ^
    --add-data "lang;lang" ^
    --hidden-import pillow_heif ^
    --hidden-import tkinterdnd2 ^
    --hidden-import about_dialog ^
    --hidden-import lang_manager ^
    --hidden-import config_manager ^
    webp_converter.py

echo.
if exist "dist\WebP_Converter.exe" (
    echo Build successful! Executable created at: dist\WebP_Converter.exe
    dir "dist\WebP_Converter.exe"
) else (
    echo Build failed!
)

pause
