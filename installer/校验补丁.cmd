@echo off
powershell.exe -NoProfile -File "%~dp0Manage-Patch.ps1" -Action Verify
pause
