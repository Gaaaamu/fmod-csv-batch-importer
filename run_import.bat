@echo off
REM FMOD Batch Import Launcher
REM Double-click to run. No CLI input required.

cd /d "%~dp0"
python -m fmod_batch_import
pause
