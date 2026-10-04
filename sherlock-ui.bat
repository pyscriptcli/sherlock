@echo off
setlocal enabledelayedexpansion
title Sherlock Investigation Studio

echo ===================================================================
echo             SHERLOCK INVESTIGATION STUDIO (Local Web UI)
echo ===================================================================
echo  Checking port 7860...

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":7860" ^| findstr "LISTENING" 2^>nul') do (
    echo  Stopping existing server process (PID %%a)...
    taskkill /f /pid %%a >nul 2>&1
)

echo  Starting local server at http://localhost:7860 ...
echo  Live CDP browser screencast, anti-slop linter, and fact cache active.
echo ===================================================================
echo.

python "%~dp0\sherlock_ui.py"

if errorlevel 1 (
    echo.
    echo [!] Sherlock UI server stopped or encountered an error.
    pause
)
