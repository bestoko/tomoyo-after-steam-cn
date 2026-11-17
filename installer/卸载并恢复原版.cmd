@echo off
powershell.exe -NoProfile -File "%~dp0Manage-Patch.ps1" -Action Uninstall
if errorlevel 1 echo Restore failed. See the message above.
pause
