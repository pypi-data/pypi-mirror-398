@echo off
setlocal enabledelayedexpansion

echo ========================================
echo MediBot Crash Diagnostic Tool
echo ========================================
echo.
echo This tool will help identify where MediBot.bat is crashing
echo on the XP production machine.
echo.
echo Press Enter to start diagnostics...
call :maybe_pause

:: Test 1: Basic batch functionality
echo.
echo ========================================
echo Test 1: Basic Batch Functionality
echo ========================================
echo Testing basic batch commands...
echo Current directory: %CD%
echo Current time: %TIME%
echo Current date: %DATE%
echo.
echo Testing variable expansion...
set "test_var=Hello World"
echo Test variable: %test_var%
echo Delayed expansion test: !test_var!
echo.
echo Test 1 PASSED - Basic batch functionality works
echo Press Enter to continue...
call :maybe_pause

:: Test 2: Python installation
echo.
echo ========================================
echo Test 2: Python Installation
echo ========================================
echo Testing Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found or not in PATH
    echo Current PATH: %PATH%
    echo.
    echo Test 2 FAILED - Python not available
    echo Press Enter to continue anyway...
    call :maybe_pause
) else (
    echo Python found successfully
    python --version
    echo.
    echo Test 2 PASSED - Python installation OK
    echo Press Enter to continue...
    call :maybe_pause
)

:: Test 3: Directory structure
echo.
echo ========================================
echo Test 3: Directory Structure
echo ========================================
echo Testing directory structure...
echo Current directory contents:
dir /b
echo.
echo Testing MediBot directory:
if exist "MediBot" (
    echo MediBot directory exists
    echo MediBot contents:
    dir /b MediBot
) else (
    echo WARNING: MediBot directory not found
)
echo.
echo Test 3 PASSED - Directory structure checked
echo Press Enter to continue...
call :maybe_pause

:: Test 4: F: drive access
echo.
echo ========================================
echo Test 4: F: Drive Access
echo ========================================
echo Testing F: drive access...
if exist "F:\" (
    echo F: drive exists
    if exist "F:\Medibot" (
        echo F:\Medibot directory exists
        echo F:\Medibot contents:
        dir /b "F:\Medibot" 2>nul || echo Cannot list F:\Medibot contents
    ) else (
        echo F:\Medibot directory does not exist
    )
) else (
    echo F: drive does not exist
)
echo.
echo Test 4 PASSED - F: drive access checked
echo Press Enter to continue...
call :maybe_pause

:: Test 5: Python package access
echo.
echo ========================================
echo Test 5: Python Package Access
echo ========================================
echo Testing Python package access...
echo Testing pkg_resources import...
python -c "import pkg_resources" 2>nul
if errorlevel 1 (
    echo ERROR: pkg_resources not available
) else (
    echo pkg_resources import successful
)

echo Testing MediCafe package...
python -c "import pkg_resources; print('MediCafe=='+pkg_resources.get_distribution('medicafe').version)" 2>nul
if errorlevel 1 (
    echo ERROR: MediCafe package not found or error accessing
) else (
    echo MediCafe package found
)
echo.
echo Test 5 PASSED - Python package access checked
echo Press Enter to continue...
call :maybe_pause

:: Test 6: Configuration file
echo.
echo ========================================
echo Test 7: Configuration File
echo ========================================
echo Testing configuration file access...
set "config_file=MediBot\json\config.json"
echo Checking for config file: %config_file%
if exist "%config_file%" (
    echo Config file exists
) else (
    echo WARNING: Config file not found
)
echo.
echo Test 7 PASSED - Configuration file checked
echo Press Enter to continue...
call :maybe_pause

:: Test 8: Update script files
echo.
echo ========================================
echo Test 8: Update Script Files
echo ========================================
echo Testing update script files...
set "upgrade_medicafe_local=MediBot\update_medicafe.py"
set "upgrade_medicafe_legacy=F:\Medibot\update_medicafe.py"

echo Checking local update script: %upgrade_medicafe_local%
if exist "%upgrade_medicafe_local%" (
    echo Local update script found
) else (
    echo Local update script not found
)

echo Checking legacy update script: %upgrade_medicafe_legacy%
if exist "%upgrade_medicafe_legacy%" (
    echo Legacy update script found
) else (
    echo Legacy update script not found
)
echo.
echo Test 8 PASSED - Update script files checked
echo Press Enter to continue...
call :maybe_pause

:: Test 9: Python module imports
echo.
echo ========================================
echo Test 9: Python Module Imports
echo ========================================
echo Testing Python module imports...
echo Testing sys module...
python -c "import sys; print('Python version:', sys.version)" 2>nul
if errorlevel 1 (
    echo ERROR: sys module import failed
) else (
    echo sys module import successful
)

echo Testing MediCafe module...
python -c "import MediCafe" 2>nul
if errorlevel 1 (
    echo ERROR: MediCafe module import failed
) else (
    echo MediCafe module import successful
)
echo.
echo Test 9 PASSED - Python module imports checked
echo Press Enter to continue...
call :maybe_pause

:: Test 10: Command execution
echo.
echo ========================================
echo Test 10: Command Execution
echo ========================================
echo Testing command execution...
echo Testing simple command...
echo Hello World
if errorlevel 1 (
    echo ERROR: Simple command execution failed
) else (
    echo Simple command execution successful
)

echo Testing Python command execution...
python -c "print('Python command execution test')" 2>nul
if errorlevel 1 (
    echo ERROR: Python command execution failed
) else (
    echo Python command execution successful
)
echo.
echo Test 10 PASSED - Command execution checked
echo Press Enter to continue...
call :maybe_pause

:: Test 11: File operations
echo.
echo ========================================
echo Test 11: File Operations
echo ========================================
echo Testing file operations...
echo Creating test file...
echo Test content > test_file.txt
if exist "test_file.txt" (
    echo Test file created successfully
    echo Test file contents:
    type test_file.txt
    echo Deleting test file...
    del test_file.txt
    if not exist "test_file.txt" (
        echo Test file deleted successfully
    ) else (
        echo ERROR: Could not delete test file
    )
) else (
    echo ERROR: Could not create test file
)
echo.
echo Test 11 PASSED - File operations checked
echo Press Enter to continue...
pause >nul

:: Test 12: Menu functionality
if not defined NON_INTERACTIVE (
  echo.
  echo ========================================
  echo Test 12: Menu Functionality
  echo ========================================
  echo Testing menu functionality...
  echo.
  echo Test Menu:
  echo 1. Option 1
  echo 2. Option 2
  echo 3. Exit
  echo.
  set /p menu_choice="Enter choice (1-3): "
  if "!menu_choice!"=="1" (
      echo Option 1 selected
  ) else if "!menu_choice!"=="2" (
      echo Option 2 selected
  ) else if "!menu_choice!"=="3" (
      echo Exit selected
  ) else (
      echo Invalid choice: !menu_choice!
  )
  echo.
  echo Test 12 PASSED - Menu functionality checked
  echo Press Enter to continue...
  call :maybe_pause
)

:: Final summary
echo.
echo ========================================
echo DIAGNOSTIC SUMMARY
echo ========================================
echo.
echo All diagnostic tests completed.
echo.
echo If the batch file is still crashing, the issue is likely:
echo 1. A specific command or operation not tested here
echo 2. A timing issue or race condition
echo 3. A specific file or path that doesn't exist
echo 4. A Python module dependency issue
echo 5. A Windows XP compatibility issue
echo.
echo Recommendations:
echo 1. Run the debug version (MediBot_debug.bat) to see exactly where it fails
echo 2. Check Windows Event Viewer for any error messages
echo 3. Try running the batch file from a command prompt to see error output
echo 4. Check if any antivirus software is blocking the execution
echo.
echo Press Enter to exit...
call :maybe_pause
exit /b 0

:maybe_pause
if defined NON_INTERACTIVE goto :eof
pause >nul
goto :eof