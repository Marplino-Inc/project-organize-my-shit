@echo off
setlocal
title Sprig Work
powershell.exe -NoProfile -File "%~dp0Start.ps1" %*
if errorlevel 1 (
    echo.
    echo Sprig could not start. See the message above and README.md for help.
    pause
    exit /b 1
)
