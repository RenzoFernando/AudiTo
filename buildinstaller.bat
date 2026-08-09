@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PROJECT_ROOT=%cd%"
set "ENTRY_POINT=main.py"
set "VENV_PYTHON=.venv\Scripts\python.exe"
set "META_CMD=.build_meta_installer.cmd"
set "VERSION_FILE=.build_version_info_installer.txt"
set "INSTALLER_SCRIPT=.build_installer.iss"
set "BUILD_ROOT=build\installer"
set "DIST_DIR=%BUILD_ROOT%\dist"
set "WORK_DIR=%BUILD_ROOT%\pyinstaller"
set "SPEC_DIR=%BUILD_ROOT%\spec"
set "STAGE_DIR=%BUILD_ROOT%\payload"
set "ISCC_CMD="
if exist "%VENV_PYTHON%" (
    set "PYTHON_CMD=%VENV_PYTHON%"
) else (
    set "PYTHON_CMD=python"
)
call :cleanup_crash_reports
if exist "%BUILD_ROOT%" rmdir /s /q "%BUILD_ROOT%"
if exist "%META_CMD%" del /q "%META_CMD%"
if exist "%VERSION_FILE%" del /q "%VERSION_FILE%"
if exist "%INSTALLER_SCRIPT%" del /q "%INSTALLER_SCRIPT%"
echo.
echo =======================================================
echo  Compilacion instalador AudiTo
echo  Motor: PyInstaller + Inno Setup
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
if not exist "%STAGE_DIR%" mkdir "%STAGE_DIR%"
if not exist "%SPEC_DIR%" mkdir "%SPEC_DIR%"
if not exist "%OUTPUT_FOLDER%" mkdir "%OUTPUT_FOLDER%"
if exist "%OUTPUT_FOLDER%\%INSTALLER_NAME%" del /q "%OUTPUT_FOLDER%\%INSTALLER_NAME%"
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
    --distpath "%PROJECT_ROOT%\%DIST_DIR%" ^
    --workpath "%PROJECT_ROOT%\%WORK_DIR%" ^
    --specpath "%PROJECT_ROOT%\%SPEC_DIR%" ^
    "%PROJECT_ROOT%\%ENTRY_POINT%"
if errorlevel 1 goto fail
move /y "%DIST_DIR%\%APP_EXE_NAME%" "%STAGE_DIR%\%APP_EXE_NAME%" >nul
if errorlevel 1 goto fail
> "%STAGE_DIR%\%INSTALL_MARKER_FILE%" echo installed
call :resolve_iscc
if not defined ISCC_CMD call :install_iscc
if not defined ISCC_CMD goto iscc_error
> "%INSTALLER_SCRIPT%" echo [Setup]
>> "%INSTALLER_SCRIPT%" echo AppId={{42698D03-F13F-4F48-9488-AEE60958D686}
>> "%INSTALLER_SCRIPT%" echo AppName=%PRODUCT_NAME%
>> "%INSTALLER_SCRIPT%" echo AppVersion=%PRODUCT_VERSION%
>> "%INSTALLER_SCRIPT%" echo AppPublisher=%COMPANY_NAME%
>> "%INSTALLER_SCRIPT%" echo AppPublisherURL=%PUBLISHER_URL%
>> "%INSTALLER_SCRIPT%" echo AppSupportURL=%SUPPORT_URL%
>> "%INSTALLER_SCRIPT%" echo AppUpdatesURL=%UPDATES_URL%
>> "%INSTALLER_SCRIPT%" echo AppCopyright=%COPYRIGHT_TEXT%
>> "%INSTALLER_SCRIPT%" echo DefaultDirName={autopf}\%PRODUCT_NAME%
>> "%INSTALLER_SCRIPT%" echo DefaultGroupName=%PRODUCT_NAME%
>> "%INSTALLER_SCRIPT%" echo OutputDir=%OUTPUT_FOLDER%
>> "%INSTALLER_SCRIPT%" echo OutputBaseFilename=%INSTALLER_BASENAME%
>> "%INSTALLER_SCRIPT%" echo SetupIconFile=%ICON_FILE%
>> "%INSTALLER_SCRIPT%" echo UninstallDisplayIcon={app}\%APP_EXE_NAME%
>> "%INSTALLER_SCRIPT%" echo Compression=lzma2
>> "%INSTALLER_SCRIPT%" echo SolidCompression=yes
>> "%INSTALLER_SCRIPT%" echo WizardStyle=modern
>> "%INSTALLER_SCRIPT%" echo PrivilegesRequired=admin
>> "%INSTALLER_SCRIPT%" echo ArchitecturesAllowed=x64compatible
>> "%INSTALLER_SCRIPT%" echo ArchitecturesInstallIn64BitMode=x64compatible
>> "%INSTALLER_SCRIPT%" echo VersionInfoCompany=%COMPANY_NAME%
>> "%INSTALLER_SCRIPT%" echo VersionInfoDescription=%FILE_DESCRIPTION%
>> "%INSTALLER_SCRIPT%" echo VersionInfoVersion=%PRODUCT_VERSION%
>> "%INSTALLER_SCRIPT%" echo VersionInfoProductName=%PRODUCT_NAME%
>> "%INSTALLER_SCRIPT%" echo VersionInfoProductVersion=%PRODUCT_VERSION%
>> "%INSTALLER_SCRIPT%" echo UsePreviousAppDir=yes
>> "%INSTALLER_SCRIPT%" echo DisableProgramGroupPage=yes
>> "%INSTALLER_SCRIPT%" echo.
>> "%INSTALLER_SCRIPT%" echo [Tasks]
>> "%INSTALLER_SCRIPT%" echo Name: "desktopicon"; Description: "Crear acceso directo en el Escritorio"; GroupDescription: "Accesos directos:"
>> "%INSTALLER_SCRIPT%" echo.
>> "%INSTALLER_SCRIPT%" echo [Files]
>> "%INSTALLER_SCRIPT%" echo Source: "%STAGE_DIR%\%APP_EXE_NAME%"; DestDir: "{app}"; Flags: ignoreversion
>> "%INSTALLER_SCRIPT%" echo Source: "%STAGE_DIR%\%INSTALL_MARKER_FILE%"; DestDir: "{app}"; Flags: ignoreversion
>> "%INSTALLER_SCRIPT%" echo.
>> "%INSTALLER_SCRIPT%" echo [Icons]
>> "%INSTALLER_SCRIPT%" echo Name: "{autodesktop}\%PRODUCT_NAME%"; Filename: "{app}\%APP_EXE_NAME%"; WorkingDir: "{app}"; IconFilename: "{app}\%APP_EXE_NAME%"; Tasks: desktopicon
>> "%INSTALLER_SCRIPT%" echo Name: "{autoprograms}\%PRODUCT_NAME%"; Filename: "{app}\%APP_EXE_NAME%"; WorkingDir: "{app}"; IconFilename: "{app}\%APP_EXE_NAME%"
>> "%INSTALLER_SCRIPT%" echo.
>> "%INSTALLER_SCRIPT%" echo [Run]
>> "%INSTALLER_SCRIPT%" echo Filename: "{app}\%APP_EXE_NAME%"; Description: "Abrir %PRODUCT_NAME% ahora"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent unchecked runasoriginaluser
"%ISCC_CMD%" "%INSTALLER_SCRIPT%"
if errorlevel 1 goto fail
call :cleanup_build
echo.
echo =======================================================
echo  Instalador generado correctamente
echo =======================================================
echo %OUTPUT_FOLDER%\%INSTALLER_NAME%
echo.
pause
exit /b 0
:resolve_iscc
if defined ISCC_PATH if exist "%ISCC_PATH%" set "ISCC_CMD=%ISCC_PATH%"
if defined ISCC_CMD goto :eof
where ISCC.exe >nul 2>&1
if not errorlevel 1 set "ISCC_CMD=ISCC.exe"
if defined ISCC_CMD goto :eof
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_CMD=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if defined ISCC_CMD goto :eof
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_CMD=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if defined ISCC_CMD goto :eof
if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_CMD=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
goto :eof
:install_iscc
echo.
echo Inno Setup 6 no esta instalado. Intentando instalarlo automaticamente...
where winget.exe >nul 2>&1
if errorlevel 1 goto :eof
winget install --id JRSoftware.InnoSetup -e --source winget --scope user --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto :eof
set "ISCC_CMD="
call :resolve_iscc
goto :eof
:cleanup_build
if exist "%BUILD_ROOT%" rmdir /s /q "%BUILD_ROOT%"
if exist "%INSTALLER_SCRIPT%" del /q "%INSTALLER_SCRIPT%"
if exist "%VERSION_FILE%" del /q "%VERSION_FILE%"
if exist "%META_CMD%" del /q "%META_CMD%"
call :cleanup_crash_reports
goto :eof
:cleanup_crash_reports
del /q "%PROJECT_ROOT%\NuGetCrashReport*" >nul 2>&1
for /d %%D in ("%PROJECT_ROOT%\NuGetCrashReport*") do rmdir /s /q "%%~fD" >nul 2>&1
del /q "%TEMP%\NuGetCrashReport*" >nul 2>&1
for /d %%D in ("%TEMP%\NuGetCrashReport*") do rmdir /s /q "%%~fD" >nul 2>&1
goto :eof
:meta_error
echo ERROR: No se pudieron cargar los metadatos desde app\app_meta.py.
goto cleanup_fail
:version_error
echo ERROR: No se pudo generar la metadata de Windows.
goto cleanup_fail
:icon_error
echo ERROR: No se encontro el icono %ICON_FILE%.
goto cleanup_fail
:iscc_error
echo ERROR: No se encontro Inno Setup 6 y no fue posible instalarlo automaticamente. Instala Inno Setup 6 o define ISCC_PATH.
goto cleanup_fail
:fail
echo ERROR: La generacion del instalador fallo.
:cleanup_fail
call :cleanup_build
pause
exit /b 1
