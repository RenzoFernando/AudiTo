@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PROJECT_ROOT=%cd%"
set "VENV_DIR=.venv"
set "REQ=requirements.txt"
set "PY_CMD="
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
goto :main

:trypy
set "candidate=%*"
%candidate% --version >nul 2>&1
if not errorlevel 1 if not defined PY_CMD set "PY_CMD=%candidate%"
exit /b 0

:cleanup_crash_reports
del /q "%PROJECT_ROOT%\NuGetCrashReport*" >nul 2>&1
for /d %%D in ("%PROJECT_ROOT%\NuGetCrashReport*") do rmdir /s /q "%%~fD" >nul 2>&1
del /q "%TEMP%\NuGetCrashReport*" >nul 2>&1
for /d %%D in ("%TEMP%\NuGetCrashReport*") do rmdir /s /q "%%~fD" >nul 2>&1
exit /b 0

:cleanup_pip_artifacts
for /d %%D in ("%VENV_DIR%\Lib\site-packages\~ip*") do rmdir /s /q "%%~fD" >nul 2>&1
for %%F in ("%VENV_DIR%\Lib\site-packages\~ip*") do del /q "%%~fF" >nul 2>&1
exit /b 0

:py_fail
call :cleanup_crash_reports
echo.
echo ERROR: Instala Python 3.11 o 3.12 y vuelve a ejecutar este archivo.
echo.
pause
exit /b 1

:fail
call :cleanup_crash_reports
echo.
echo ERROR: No fue posible preparar el entorno.
echo.
pause
exit /b 1

:main
call :cleanup_crash_reports
echo.
echo =======================================================
echo  Preparacion de entorno AudiTo
echo =======================================================
echo.
call :trypy py -3.11
if defined PY_CMD goto py_ok
call :trypy py -3.12
if defined PY_CMD goto py_ok
call :trypy py -3
if not defined PY_CMD call :trypy python
if not defined PY_CMD goto py_fail
:py_ok
echo Python detectado:
%PY_CMD% --version
if exist "%VENV_PY%" goto venv_ready
if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%"
if exist "%VENV_DIR%" goto fail
%PY_CMD% -m venv "%VENV_DIR%"
if errorlevel 1 goto fail
:venv_ready
call :cleanup_pip_artifacts
"%VENV_PY%" -m pip --version >nul 2>&1
if not errorlevel 1 goto pip_ready
"%VENV_PY%" -m ensurepip --upgrade
if errorlevel 1 goto fail
:pip_ready
"%VENV_PY%" -m pip install -r "%REQ%" --disable-pip-version-check --default-timeout=100
if errorlevel 1 goto fail
call :cleanup_pip_artifacts
call :cleanup_crash_reports
echo.
echo Entorno listo.
echo Ejecuta buildportable.bat para el portable.
echo Ejecuta buildinstaller.bat para el instalador.
echo.
pause
exit /b 0
