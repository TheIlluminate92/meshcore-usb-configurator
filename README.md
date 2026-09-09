# MeshCore USB Configurator — first version

Double-click **Start Configurator.cmd** on this Windows laptop. Close the browser's serial connection first. Select the USB COM port, click **Read device**, and confirm the displayed name, model and firmware.

Every read saves a JSON snapshot under `snapshots`. Optional read errors are recorded rather than presented as a complete backup. Edit fields or load a profile, then use **Review & apply** to inspect changes. Nothing is written by reading or loading a file. Applying checks identity and stale settings, saves a report, sends supported Companion commands, and rereads for verification. On a write error, some settings may already have changed; read again. There is no automatic retry or rollback.

## What is supported

- Serial port enumeration; protocol identification after selecting a port.
- Read device/self information, custom variables, contacts and channels (up to 64 reported slots).
- Edit name, frequency, bandwidth, spreading factor, coding rate, TX power and coordinates when returned by the device.
- Versioned JSON profiles and import of the two supplied browser export structures.
- Snapshot export and per-apply verification reports.

Channels, contacts, telemetry and custom settings are currently read-only. No firmware flashing, private-key import/export, direct flash-file editing, or batch-write UI is included. Profile import intentionally imports only the eight implemented settings. It does not restore an entire browser backup or identity.

## Architecture and units

`model.py` owns profile validation and unit conversion. Browser exports report frequency in kHz and bandwidth in Hz; profile/command values use MHz and kHz respectively. `device.py` uses the meshcore Python library's framed Companion serial protocol at 115200 baud. Firmware internal JSON storage is not accessed. `app.py` handles the GUI and sends serial work to a background worker. The adapter accepts an explicit port and can later be used by a multi-device queue; each device will need its own read, capability checks, identity binding and result.

This first implementation uses known Companion commands and fields that are present in responses; this is not general firmware capability discovery. Firmware remains the authority on board-specific radio limits. TX power is conservatively limited to 0–22 dBm and the reported maximum, whichever is lower. Hardware compatibility, persistence across power cycles and T1000-E magnetic USB behavior still require bench validation.

## Windows setup from GitHub

Install Python 3.12 with Tcl/Tk and the Python launcher. Download or clone this repository, run **Setup Windows.cmd** once, then **Start Configurator.cmd**. Setup creates a local virtual environment and installs `requirements.txt`. The launcher prefers that environment. The original development computer can also use its bundled runtime and ignored local dependencies; these are not shipped through GitHub.

Run tests with `.venv\Scripts\python.exe -m unittest -v test_configurator test_serial_cleanup`. GitHub Actions runs the same tests on Windows. Fixtures are synthetic and do not require the private exports or a physical radio.

## Local reference exports

Device exports, JSON profiles, snapshots, reports, local dependencies and secrets are excluded from Git. The original pre-upgrade and post-upgrade exports remain local references. See `PROJECT_CONTEXT.md` for their role in guiding the next development steps.

## Protocol references

- https://github.com/meshcore-dev/meshcore_py
- https://github.com/meshcore-dev/meshcore_py/blob/main/src/meshcore/commands/device.py

Snapshots may contain channel secrets, PINs, contact details and location. Keep them local with your configuration backups.
