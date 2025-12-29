@echo off
setlocal enabledelayedexpansion

echo [DIAGNOSTIC] ========================================
echo [DIAGNOSTIC] F: Drive and update_medicafe.py Diagnostic
echo [DIAGNOSTIC] ========================================
if defined NON_INTERACTIVE (
  echo [DIAGNOSTIC] NON_INTERACTIVE detected - skipping F: drive diagnostics to avoid hangs
  exit /b 0
)
echo [DIAGNOSTIC] Current directory: %CD%
echo [DIAGNOSTIC] Current time: %TIME%
echo [DIAGNOSTIC] Press Enter to start diagnostics...
call :maybe_pause

echo.
echo [DIAGNOSTIC] STEP 1: Checking F: drive existence
echo [DIAGNOSTIC] ========================================
if exist "F:\" (
    echo [SUCCESS] F: drive exists
    echo [DIAGNOSTIC] F: drive contents:
    dir /b "F:\" 2>nul || echo [ERROR] Cannot list F: drive contents
) else (
    echo [ERROR] F: drive does not exist
)
echo [DIAGNOSTIC] Press Enter to continue...
call :maybe_pause

echo.
echo [DIAGNOSTIC] STEP 2: Checking F:\Medibot directory
echo [DIAGNOSTIC] ========================================
if exist "F:\Medibot" (
    echo [SUCCESS] F:\Medibot directory exists
    echo [DIAGNOSTIC] F:\Medibot contents:
    dir /b "F:\Medibot" 2>nul || echo [ERROR] Cannot list F:\Medibot contents
) else (
    echo [ERROR] F:\Medibot directory does not exist
)
echo [DIAGNOSTIC] Press Enter to continue...
call :maybe_pause

echo.
echo [DIAGNOSTIC] STEP 3: Checking for update_medicafe.py in F:\Medibot
echo [DIAGNOSTIC] ========================================
if exist "F:\Medibot\update_medicafe.py" (
    echo [SUCCESS] F:\Medibot\update_medicafe.py exists
    echo [DIAGNOSTIC] File details:
    dir "F:\Medibot\update_medicafe.py" 2>nul || echo [ERROR] Cannot get file details
) else (
    echo [ERROR] F:\Medibot\update_medicafe.py does not exist
)
echo [DIAGNOSTIC] Press Enter to continue...
call :maybe_pause

echo.
echo [DIAGNOSTIC] STEP 4: Checking local update_medicafe.py
echo [DIAGNOSTIC] ========================================
if exist "MediBot\update_medicafe.py" (
    echo [SUCCESS] Local MediBot\update_medicafe.py exists
    echo [DIAGNOSTIC] File details:
    dir "MediBot\update_medicafe.py" 2>nul || echo [ERROR] Cannot get file details
) else (
    echo [ERROR] Local MediBot\update_medicafe.py does not exist
)
echo [DIAGNOSTIC] Press Enter to continue...
call :maybe_pause

echo.
echo [DIAGNOSTIC] STEP 5: Testing Python access to F: drive file
echo [DIAGNOSTIC] ========================================
if exist "F:\Medibot\update_medicafe.py" (
    echo [DIAGNOSTIC] Testing Python access to F:\Medibot\update_medicafe.py...
    python -c "import os; print('[SUCCESS] Python can access F: drive file') if os.path.exists('F:\\Medibot\\update_medicafe.py') else print('[ERROR] Python cannot access F: drive file')" 2>nul
    if errorlevel 1 (
        echo [ERROR] Python test failed for F: drive file
    )
) else (
    echo [WARNING] Skipping Python test - F: drive file does not exist
)
echo [DIAGNOSTIC] Press Enter to continue...
call :maybe_pause

echo.
echo [DIAGNOSTIC] STEP 6: Testing Python access to local file
echo [DIAGNOSTIC] ========================================
if exist "MediBot\update_medicafe.py" (
    echo [DIAGNOSTIC] Testing Python access to local MediBot\update_medicafe.py...
    python -c "import os; print('[SUCCESS] Python can access local file') if os.path.exists('MediBot\\update_medicafe.py') else print('[ERROR] Python cannot access local file')" 2>nul
    if errorlevel 1 (
        echo [ERROR] Python test failed for local file
    )
) else (
    echo [WARNING] Skipping Python test - local file does not exist
)
echo [DIAGNOSTIC] Press Enter to continue...
call :maybe_pause

echo.
echo [DIAGNOSTIC] STEP 7: Testing actual Python execution of F: drive file
echo [DIAGNOSTIC] ========================================
if exist "F:\Medibot\update_medicafe.py" (
    echo [DIAGNOSTIC] Testing Python execution of F:\Medibot\update_medicafe.py...
    echo [DIAGNOSTIC] This will test if Python can actually run the file
    echo [DIAGNOSTIC] Command: python "F:\Medibot\update_medicafe.py" --help
    python "F:\Medibot\update_medicafe.py" --help 2>nul
    if errorlevel 1 (
        echo [ERROR] Python execution of F: drive file failed
        echo [DIAGNOSTIC] This is likely the source of the "can't find" error
    ) else (
        echo [SUCCESS] Python execution of F: drive file succeeded
    )
) else (
    echo [WARNING] Skipping execution test - F: drive file does not exist
)
echo [DIAGNOSTIC] Press Enter to continue...
call :maybe_pause

echo.
echo [DIAGNOSTIC] STEP 8: Testing actual Python execution of local file
echo [DIAGNOSTIC] ========================================
if exist "MediBot\update_medicafe.py" (
    echo [DIAGNOSTIC] Testing Python execution of local MediBot\update_medicafe.py...
    echo [DIAGNOSTIC] This will test if Python can actually run the local file
    echo [DIAGNOSTIC] Command: python "MediBot\update_medicafe.py" --help
    python "MediBot\update_medicafe.py" --help 2>nul
    if errorlevel 1 (
        echo [ERROR] Python execution of local file failed
    ) else (
        echo [SUCCESS] Python execution of local file succeeded
    )
) else (
    echo [WARNING] Skipping execution test - local file does not exist
)
echo [DIAGNOSTIC] Press Enter to continue...
call :maybe_pause

echo.
echo [DIAGNOSTIC] STEP 9: Checking Python PATH and environment
echo [DIAGNOSTIC] ========================================
echo [DIAGNOSTIC] Python version:
python --version 2>nul || echo [ERROR] Python not found
echo [DIAGNOSTIC] Python executable location:
python -c "import sys; print(sys.executable)" 2>nul || echo [ERROR] Cannot determine python executable path
echo [DIAGNOSTIC] Current PATH:
echo %PATH%
echo [DIAGNOSTIC] Press Enter to continue...
call :maybe_pause

echo.
echo [DIAGNOSTIC] STEP 10: Summary and recommendations
echo [DIAGNOSTIC] ========================================
echo [DIAGNOSTIC] Based on the diagnostics above:
echo [DIAGNOSTIC] 
if exist "F:\Medibot\update_medicafe.py" (
    echo [DIAGNOSTIC] - F: drive file exists but may have access issues
) else (
    echo [DIAGNOSTIC] - F: drive file does not exist (this is the main issue)
)
if exist "MediBot\update_medicafe.py" (
    echo [DIAGNOSTIC] - Local file exists and should be used instead
) else (
    echo [DIAGNOSTIC] - Local file also missing (critical issue)
)
echo [DIAGNOSTIC] 
echo [DIAGNOSTIC] RECOMMENDATION: The batch file should prioritize the local
echo [DIAGNOSTIC] MediBot\update_medicafe.py file over the F: drive version.
echo [DIAGNOSTIC] 
echo [DIAGNOSTIC] Press Enter to exit...
call :maybe_pause
exit /b 0

:maybe_pause
if defined NON_INTERACTIVE goto :eof
pause >nul
goto :eof