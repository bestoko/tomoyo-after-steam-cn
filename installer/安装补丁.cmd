@echo off
powershell.exe -NoProfile -File "%~dp0Manage-Patch.ps1" -Action Install
if errorlevel 1 echo Installation failed. See the message above.
pause
