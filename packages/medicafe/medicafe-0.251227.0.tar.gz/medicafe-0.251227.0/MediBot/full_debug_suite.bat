@echo off
setlocal enabledelayedexpansion

echo ========================================
echo         FULL DEBUG SUITE START
echo ========================================
if /I "%~1"=="/interactive" (
  set "NON_INTERACTIVE="
  echo Running diagnostics interactively...
) else (
  set "NON_INTERACTIVE=1"
  echo Running diagnostics non-interactively...
)
echo.

:: F: Drive Diagnostic
if defined NON_INTERACTIVE (
  echo [SKIP] F: Drive diagnostic skipped in NON_INTERACTIVE mode
) else (
  call "%~dp0f_drive_diagnostic.bat"
  if errorlevel 1 (
    echo [WARN] F: Drive diagnostic reported issues
  ) else (
    echo [OK] F: Drive diagnostic passed
  )
)

:: Crash Diagnostic
if defined NON_INTERACTIVE (
  echo [SKIP] Crash diagnostic skipped in NON_INTERACTIVE mode
) else (
  call "%~dp0crash_diagnostic.bat"
  if errorlevel 1 (
    echo [WARN] Crash diagnostic reported issues
  ) else (
    echo [OK] Crash diagnostic passed
  )
)

:: Basic Debug
if defined NON_INTERACTIVE (
  echo [SKIP] Basic debug skipped in NON_INTERACTIVE mode
) else (
  call "%~dp0MediBot_debug.bat"
  if errorlevel 1 (
    echo [WARN] Basic debug reported issues
  ) else (
    echo [OK] Basic debug passed
  )
)

:: Fixed Version Test removed (redundant script)

:: Additional automated checks
python --version >nul 2>&1 && echo [OK] Python found || echo [ERROR] Python not found in PATH
python -c "import pkg_resources; print('MediCafe=='+pkg_resources.get_distribution('medicafe').version)" >nul 2>&1 && echo [OK] MediCafe package found || echo [WARN] MediCafe package missing
if exist "%~dp0update_medicafe.py" (echo [OK] Local update_medicafe.py present) else (echo [WARN] Local update_medicafe.py missing)
if exist "F:\" (
  if exist "F:\Medibot\update_medicafe.py" (echo [OK] F:\Medibot\update_medicafe.py present) else (echo [WARN] F: update script missing)
) else (
  echo [WARN] F: drive not accessible
)

echo.
echo ========================================
echo           FULL DEBUG SUITE DONE
echo ========================================
endlocal & exit /b 0


