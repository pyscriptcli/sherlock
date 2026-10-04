@echo off
chcp 65001 >nul
title Sherlock Visual Scrape
setlocal enabledelayedexpansion

if "%~1"=="" (
    echo ===================================================================
    echo                SHERLOCK LIVE VISUAL SCRAPER
    echo ===================================================================
    echo  Phase 1: Multi-engine search scout to discover primary sources
    echo  Phase 2: Headed Chromium browser opens on screen to validate DOM
    echo ===================================================================
    echo.
    set /p USER_QUERY="Enter search query to scout and visually scrape: "
    if "!USER_QUERY!"=="" (
        echo [!] No query entered. Exiting.
        exit /b 1
    )
    python "%~dp0\sherlock_scrape.py" "!USER_QUERY!"
) else (
    python "%~dp0\sherlock_scrape.py" %*
)

if errorlevel 1 (
    echo.
    echo [!] Sherlock Scrape finished with errors or interruptions.
)
