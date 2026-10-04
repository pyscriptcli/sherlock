@echo off
title Sherlock Investigation Studio
python "%~dp0sherlock_ui.py" %*
if errorlevel 1 pause
