@echo off
setlocal
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%~dp0manage_shortcuts.ps1" -Action Install %*
exit /b %errorlevel%
