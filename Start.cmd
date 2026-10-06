@echo off
setlocal
title Organize
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start.ps1" %*
if errorlevel 1 (
    echo.
    echo Organize could not start. See the message above and README.md for help.
    pause
    exit /b 1
)
