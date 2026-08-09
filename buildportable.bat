@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PROJECT_ROOT=%cd%"
set "ENTRY_POINT=main.py"
set "VENV_PYTHON=.venv\Scripts\python.exe"
set "META_CMD=.build_meta.cmd"
set "VERSION_FILE=.build_version_info.txt"
if exist "%VENV_PYTHON%" (
    set "PYTHON_CMD=%VENV_PYTHON%"
) else (
    set "PYTHON_CMD=python"
)
echo.
echo =======================================================
echo  Compilacion portable AudiTo
echo  Motor: PyInstaller
echo =======================================================
echo.
"%PYTHON_CMD%" --version
"%PYTHON_CMD%" build_meta.py > "%META_CMD%"
if errorlevel 1 goto meta_error
call "%META_CMD%"
if errorlevel 1 goto meta_error
"%PYTHON_CMD%" build_version_info.py "%VERSION_FILE%"
if errorlevel 1 goto version_error
if not exist "%ICON_FILE%" goto icon_error
if not exist "%OUTPUT_FOLDER%" mkdir "%OUTPUT_FOLDER%"
if exist "%OUTPUT_FOLDER%\%PORTABLE_ARTIFACT_NAME%" del /q "%OUTPUT_FOLDER%\%PORTABLE_ARTIFACT_NAME%"
if exist "dist" rmdir /s /q "dist"
if exist "build\pyinstaller" rmdir /s /q "build\pyinstaller"
if exist "build\%APP_NAME%.spec" del /q "build\%APP_NAME%.spec"
"%PYTHON_CMD%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name "%APP_NAME%" ^
    --icon "%PROJECT_ROOT%\%ICON_FILE%" ^
    --version-file "%PROJECT_ROOT%\%VERSION_FILE%" ^
    --add-data "%PROJECT_ROOT%\%ASSETS_FOLDER%;assets" ^
    --collect-all av ^
    --collect-all ctranslate2 ^
    --collect-all faster_whisper ^
    --collect-all tokenizers ^
    --collect-all huggingface_hub ^
    --distpath "%PROJECT_ROOT%\dist" ^
    --workpath "%PROJECT_ROOT%\build\pyinstaller" ^
    --specpath "%PROJECT_ROOT%\build" ^
    "%PROJECT_ROOT%\%ENTRY_POINT%"
if errorlevel 1 goto fail
move /y "dist\%APP_EXE_NAME%" "%OUTPUT_FOLDER%\%PORTABLE_ARTIFACT_NAME%" >nul
if errorlevel 1 goto fail
if exist "dist" rmdir /s /q "dist"
if exist "build\pyinstaller" rmdir /s /q "build\pyinstaller"
if exist "build\%APP_NAME%.spec" del /q "build\%APP_NAME%.spec"
if exist "%VERSION_FILE%" del /q "%VERSION_FILE%"
if exist "%META_CMD%" del /q "%META_CMD%"
echo.
echo =======================================================
echo  Portable generado correctamente
echo =======================================================
echo %OUTPUT_FOLDER%\%PORTABLE_ARTIFACT_NAME%
echo.
pause
exit /b 0
:meta_error
echo ERROR: No se pudieron cargar los metadatos desde app\app_meta.py.
goto cleanup_fail
:version_error
echo ERROR: No se pudo generar la metadata de Windows.
goto cleanup_fail
:icon_error
echo ERROR: No se encontro el icono %ICON_FILE%.
goto cleanup_fail
:fail
echo ERROR: La compilacion portable fallo.
:cleanup_fail
if exist "dist" rmdir /s /q "dist"
if exist "build\pyinstaller" rmdir /s /q "build\pyinstaller"
if exist "build\%APP_NAME%.spec" del /q "build\%APP_NAME%.spec"
if exist "%VERSION_FILE%" del /q "%VERSION_FILE%"
if exist "%META_CMD%" del /q "%META_CMD%"
pause
exit /b 1
