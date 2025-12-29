@echo off
setlocal enabledelayedexpansion

echo [DEBUG] ========================================
echo [DEBUG] MediBot Debug Version Starting
echo [DEBUG] ========================================
echo [DEBUG] Current directory: %CD%
echo [DEBUG] Current time: %TIME%
echo [DEBUG] Current date: %DATE%
echo [DEBUG] Press Enter to continue...
call :maybe_pause

echo [DEBUG] Step 1: Basic environment check
echo [DEBUG] Checking if we can access basic commands...
dir >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Basic dir command failed
    pause
    exit /b 1
) else (
    echo [DEBUG] Basic dir command works
)

echo [DEBUG] Press Enter to continue...
call :maybe_pause

echo [DEBUG] Step 2: Python check
echo [DEBUG] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found or not in PATH
    echo [DEBUG] Current PATH: %PATH%
    echo [DEBUG] Press Enter to exit...
    pause >nul
    exit /b 1
) else (
    echo [DEBUG] Python found successfully
    python --version
)

echo [DEBUG] Press Enter to continue...
call :maybe_pause

echo [DEBUG] Step 3: Directory structure check
echo [DEBUG] Checking current directory contents...
dir /b
echo [DEBUG] Press Enter to continue...
call :maybe_pause

echo [DEBUG] Step 4: MediBot directory check
if exist "MediBot" (
    echo [DEBUG] MediBot directory exists
    echo [DEBUG] MediBot directory contents:
    dir /b MediBot
) else (
    echo [WARNING] MediBot directory not found
)

echo [DEBUG] Press Enter to continue...
call :maybe_pause

echo [DEBUG] Step 5: F: drive check
if exist "F:\" (
    echo [DEBUG] F: drive exists
    if exist "F:\Medibot" (
        echo [DEBUG] F:\Medibot directory exists
        echo [DEBUG] F:\Medibot contents:
        dir /b "F:\Medibot" 2>nul || echo [ERROR] Cannot list F:\Medibot contents
    ) else (
        echo [DEBUG] F:\Medibot directory does not exist
    )
) else (
    echo [DEBUG] F: drive does not exist
)

echo [DEBUG] Press Enter to continue...
call :maybe_pause

echo [DEBUG] Step 6: Python package check
echo [DEBUG] Checking MediCafe package...
python -c "import pkg_resources; print('MediCafe=='+pkg_resources.get_distribution('medicafe').version)" 2>nul
if errorlevel 1 (
    echo [ERROR] MediCafe package not found or error accessing
) else (
    echo [DEBUG] MediCafe package found
)

echo [DEBUG] Press Enter to continue...
pause >nul

echo [DEBUG] Step 7: Configuration file check
set "config_file=MediBot\json\config.json"
echo [DEBUG] Checking for config file: %config_file%
if exist "%config_file%" (
    echo [DEBUG] Config file exists
) else (
    echo [WARNING] Config file not found
)

echo [DEBUG] Press Enter to continue...
pause >nul

echo [DEBUG] Step 9: Update script check
set "upgrade_medicafe_local=MediBot\update_medicafe.py"
set "upgrade_medicafe_legacy=F:\Medibot\update_medicafe.py"

echo [DEBUG] Checking for update scripts...
echo [DEBUG] Local path: %upgrade_medicafe_local%
echo [DEBUG] Legacy path: %upgrade_medicafe_legacy%

if exist "%upgrade_medicafe_local%" (
    echo [DEBUG] Local update script found
) else (
    echo [DEBUG] Local update script not found
)

if exist "%upgrade_medicafe_legacy%" (
    echo [DEBUG] Legacy update script found
) else (
    echo [DEBUG] Legacy update script not found
)

echo [DEBUG] Press Enter to continue...
pause >nul

if defined NON_INTERACTIVE goto skip_simple_menu_test
echo [DEBUG] Step 10: Simple menu test
echo [DEBUG] Testing menu functionality...
echo.
echo [DEBUG] Simple Menu Test
echo [DEBUG] 1. Test option 1
echo [DEBUG] 2. Test option 2
echo [DEBUG] 3. Exit
echo.
set /p test_choice="Enter test choice (1-3): "

if "!test_choice!"=="1" (
    echo [DEBUG] Test option 1 selected
) else if "!test_choice!"=="2" (
    echo [DEBUG] Test option 2 selected
) else if "!test_choice!"=="3" (
    echo [DEBUG] Test exit selected
    goto debug_exit
) else (
    echo [DEBUG] Invalid choice: !test_choice!
)

echo [DEBUG] Press Enter to continue...
call :maybe_pause

:skip_simple_menu_test
echo [DEBUG] Step 11: Python module import test
echo [DEBUG] Testing Python module imports...
python -c "import sys; print('Python version:', sys.version)" 2>nul
if errorlevel 1 (
    echo [ERROR] Python import test failed
) else (
    echo [DEBUG] Python import test passed
)

echo [DEBUG] Press Enter to continue...
call :maybe_pause

echo [DEBUG] Step 12: MediCafe module test
echo [DEBUG] Testing MediCafe module import...
python -c "import MediCafe; print('MediCafe module imported successfully')" 2>nul
if errorlevel 1 (
    echo [ERROR] MediCafe module import failed
) else (
    echo [DEBUG] MediCafe module import passed
)

echo [DEBUG] Press Enter to continue...
call :maybe_pause

echo [DEBUG] Step 13: Final test - command execution
echo [DEBUG] Testing command execution...
echo [DEBUG] This will test if we can execute a simple command
echo [DEBUG] Command: echo Hello World
echo Hello World
if errorlevel 1 (
    echo [ERROR] Command execution failed
) else (
    echo [DEBUG] Command execution successful
)

echo [DEBUG] Press Enter to continue...
pause >nul

echo [DEBUG] ========================================
echo [DEBUG] All debug tests completed successfully
echo [DEBUG] ========================================
echo [DEBUG] Press Enter to exit...
call :maybe_pause

:debug_exit
echo [DEBUG] Exiting debug version
echo [DEBUG] Press Enter to exit...
call :maybe_pause
exit /b 0 

:maybe_pause
if defined NON_INTERACTIVE goto :eof
pause >nul
goto :eof