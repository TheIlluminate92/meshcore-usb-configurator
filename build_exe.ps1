# Run with the project virtual environment activated after Setup Windows.
$ErrorActionPreference = 'Stop'
python -m pip install pyinstaller==6.22.2
if ($LASTEXITCODE -ne 0) { throw 'Packaging setup failed.' }
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "! MeshCore Configurator" --collect-all meshcore --collect-all bleak --hidden-import serial.tools.list_ports_windows desktop_entry.py
if ($LASTEXITCODE -ne 0) { throw 'Executable build failed.' }
