@echo off
setlocal enabledelayedexpansion

:: Config Editor Launcher
:: Called from MediBot.bat Troubleshooting menu

:: Get script directory and set paths
set "script_dir=%~dp0"
set "workspace_root=%script_dir%.."
set "python_script=%script_dir%config_editor.py"

:: Use the same path resolution logic as MediLink_ConfigLoader
:: Try default path first (relative to MediCafe module)
set "config_path=%workspace_root%\json\config.json"

:: If default path doesn't exist, try platform-specific fallbacks
if not exist "%config_path%" (
    :: Check for Windows XP (F: drive)
    if exist "F:\" (
        set "config_path=F:\Medibot\json\config.json"
    ) else (
        :: Use current working directory for other Windows versions
        set "config_path=%CD%\json\config.json"
    )
)

:: Display header
cls
echo ========================================
echo        MediCafe Config Editor
echo ========================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not available or not in PATH
    echo.
    echo Please ensure Python 3.4.4 or later is installed and accessible.
    echo.
    pause
    exit /b 1
)

:: Check if config file exists
if not exist "%config_path%" (
    echo WARNING: Config file not found at:
    echo %config_path%
    echo.
    echo The editor will start with an empty configuration.
    echo You can create a new config file or navigate to the correct location.
    echo.
    set /p continue_choice="Continue anyway? (Y/N): "
    if /i not "!continue_choice!"=="Y" (
        echo Operation cancelled.
        pause
        exit /b 0
    )
)

:: Check if editor script exists
if not exist "%python_script%" (
    echo ERROR: Config editor script not found at:
    echo %python_script%
    echo.
    echo Please ensure config_editor.py is in the MediBot directory.
    echo.
    pause
    exit /b 1
)

:: Run the config editor
echo Starting config editor...
echo.
python "%python_script%" "%config_path%"

:: Check exit code
if errorlevel 1 (
    echo.
    echo ERROR: Config editor encountered an error.
    echo.
) else (
    echo.
    echo Config editor completed successfully.
    echo.
)

:: Return to caller
pause
exit /b %errorlevel%
