@echo off
setlocal enabledelayedexpansion

rem Maximize console window (XP SP3 compatible)
title MediBot_Max
echo Set objShell = CreateObject("WScript.Shell") > "%TEMP%\maxwin.vbs"
echo WScript.Sleep 200 >> "%TEMP%\maxwin.vbs"
echo On Error Resume Next >> "%TEMP%\maxwin.vbs"
echo If objShell.AppActivate("MediBot_Max") Then >> "%TEMP%\maxwin.vbs"
echo     WScript.Sleep 100 >> "%TEMP%\maxwin.vbs"
echo     objShell.SendKeys "%%{SPACE}x" >> "%TEMP%\maxwin.vbs"
echo End If >> "%TEMP%\maxwin.vbs"
start /min cscript //nologo "%TEMP%\maxwin.vbs" >nul 2>&1
ping -n 2 127.0.0.1 >nul 2>&1
del "%TEMP%\maxwin.vbs" >nul 2>&1

rem Thin shim that delegates to the Python launcher.
rem Provides only the minimum recovery options when Python is unavailable
rem or when the launcher exits unexpectedly.

set "REPO_ROOT=%~dp0.."
set "LOG_DIR=%REPO_ROOT%\MediBot\DOWNLOADS"
if exist "F:\Medibot\DOWNLOADS" (
    set "LOG_DIR=F:\Medibot\DOWNLOADS"
)

call :ensure_python
if errorlevel 1 goto python_missing

call :run_launcher %*
set "RC=%errorlevel%"
if "%RC%"=="0" exit

call :launcher_recovery "%RC%" %*
exit /b %errorlevel%

:ensure_python
python --version >nul 2>&1
exit /b %errorlevel%

:run_launcher
pushd "%REPO_ROOT%" >nul
python -m MediCafe launcher %*
set "RC=%errorlevel%"
popd >nul
exit /b %RC%

:launcher_recovery
set "FAILCODE=%~1"
shift
if "%FAILCODE%"=="" set "FAILCODE=1"
echo.
echo [WARN] MediCafe Python launcher exited with code %FAILCODE%.

:recovery_prompt
echo.
echo Recovery options:
echo   1. Retry launcher
echo   2. Retry launcher with --debug flag
echo   3. Open latest MediCafe log
echo   4. Exit
set /p choice="Select an option (1-4) or press Enter to exit [%FAILCODE%]: "
if not defined choice (
    echo Exiting with code %FAILCODE%.
    exit /b %FAILCODE%
)
if "%choice%"=="1" (
    call :run_launcher %*
    set "RC=%errorlevel%"
    if "%RC%"=="0" exit /b 0
    set "FAILCODE=%RC%"
    goto recovery_prompt
)
if "%choice%"=="2" (
    call :run_launcher --debug %*
    set "RC=%errorlevel%"
    if "%RC%"=="0" exit /b 0
    set "FAILCODE=%RC%"
    goto recovery_prompt
)
if "%choice%"=="3" (
    call :open_latest_log
    goto recovery_prompt
)
if "%choice%"=="4" (
    echo Exiting with code %FAILCODE%.
    exit /b %FAILCODE%
)
echo Invalid choice.
goto recovery_prompt

:open_latest_log
if not exist "%LOG_DIR%" (
    echo No log directory found at %LOG_DIR%.
    exit /b 1
)
for /f "delims=" %%L in ('dir /b /a:-d /o:-d "%LOG_DIR%\Log_*.log" 2^>nul') do (
    start "" notepad "%LOG_DIR%\%%L"
    echo Opened %LOG_DIR%\%%L
    exit /b 0
)
echo No log files located under %LOG_DIR%.
exit /b 1

:python_missing
echo.
echo ========================================
echo [ERROR] Python interpreter not detected.
echo ========================================
echo.
echo Please install Python 3.4.4 (XP) or later (Win10/11) and ensure 'python' is on PATH.
echo After installation, rerun MediBot.bat to launch MediCafe.
echo.
exit /b 9009
