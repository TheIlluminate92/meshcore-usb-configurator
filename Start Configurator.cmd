@echo off
cd /d "%~dp0"
set "CONFIG_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe"
if exist ".venv\Scripts\pythonw.exe" set "CONFIG_PYTHON=%~dp0.venv\Scripts\pythonw.exe"
if exist "%CONFIG_PYTHON%" (
  start "" "%CONFIG_PYTHON%" "%~dp0launch.py"
) else (
  start "" pyw -3 "%~dp0launch.py"
)
exit /b
