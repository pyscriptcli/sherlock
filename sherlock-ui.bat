@echo off
chcp 65001 >nul
title Sherlock Investigation Studio
setlocal enabledelayedexpansion

echo ===================================================================
echo        🕵️  SHERLOCK INVESTIGATION STUDIO (Local Web UI)
echo ===================================================================
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
