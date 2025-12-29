@echo off
REM StegVault TUI Quick Launcher
REM This script launches the StegVault Terminal UI

echo ========================================
echo   StegVault TUI Launcher
echo ========================================
echo.

REM Check if virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    echo [*] Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [!] Virtual environment not found at .venv
    echo [*] Using system Python...
)

REM Launch StegVault TUI
echo [*] Launching StegVault TUI...
echo.
python -m stegvault tui

REM Keep window open on error
if errorlevel 1 (
    echo.
    echo [!] Error: StegVault TUI exited with error code %errorlevel%
    pause
)
