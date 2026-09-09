@echo off
cd /d "%~dp0"
set "CONFIG_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist ".venv\Scripts\python.exe" set "CONFIG_PYTHON=%~dp0.venv\Scripts\python.exe"
if exist "%CONFIG_PYTHON%" (
  "%CONFIG_PYTHON%" launch.py
) else (
  py -3 launch.py
)
if errorlevel 1 pause
