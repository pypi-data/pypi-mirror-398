@echo off
setlocal enabledelayedexpansion

:: Determine script and workspace directories
set "script_dir=%~dp0"
set "workspace_root=%script_dir%.."

:: Paths for deep clear helper script
set "upgrade_medicafe_local=%script_dir%update_medicafe.py"
set "upgrade_medicafe_legacy=F:\Medibot\update_medicafe.py"

:: Mode selection from first argument
set "mode=%~1"
if /i "%mode%"=="--quick" goto quick_clear
if /i "%mode%"=="--deep" goto deep_clear

:: Default behavior (backwards compatible): deep clear
goto deep_clear

:quick_clear
echo Quick clearing Python cache...
cd /d "%workspace_root%"
python -Bc "import compileall; compileall.compile_dir('.', force=True)" 2>nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo [OK] Quick cache clear complete.
exit /b 0

:deep_clear
echo Deep cache clear (via update_medicafe.py)...
echo Workspace root: %workspace_root%
echo.

:: F: drive diagnostics (brief)
if exist "F:\" (
    if exist "F:\Medibot" (
        dir "F:\Medibot\update_medicafe.py" >nul 2>&1 && echo [OK] F:\Medibot\update_medicafe.py exists || echo [WARN] F:\Medibot\update_medicafe.py missing
    ) else (
        echo [WARN] F:\Medibot directory does not exist
    )
) else (
    echo [WARN] F: drive is not accessible
)

:: Prefer F: updater first (ensures using shared, unlocked copy), then local
if exist "%upgrade_medicafe_legacy%" (
    echo Using F: update_medicafe.py for deep clear
    python "%upgrade_medicafe_legacy%" --clear-cache "%workspace_root%"
    exit /b %ERRORLEVEL%
) else if exist "%~dp0update_medicafe.py" (
    echo Using local update_medicafe.py for deep clear
    python "%~dp0update_medicafe.py" --clear-cache "%workspace_root%"
    exit /b %ERRORLEVEL%
) else (
    echo ERROR: update_medicafe.py not found (F: or local)
    exit /b 1
)