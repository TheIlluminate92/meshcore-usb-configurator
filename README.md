# MeshCore USB Configurator

Double-click **Start Configurator.cmd** on this Windows laptop. Close the browser's serial connection first. Select the USB COM port, click **Read device**, and confirm the displayed name, model and firmware.

Hover over any setting label, input or **?** for a short explanation. Click **?** (or Tab to it and press Space/Enter) to keep the explanation open in a dialog. Help also covers channel fields, the USB port and action buttons, and remains available before a device is read.

Every read saves a JSON snapshot under `snapshots`. Optional read errors are recorded rather than presented as a complete backup. Edit fields or load a profile, then use **Review & apply** to inspect changes. Nothing is written by reading or loading a file. Applying checks identity and stale settings, saves a report, sends supported Companion commands, and rereads for verification. On a write error, some settings may already have changed; read again. There is no automatic retry or rollback.

## What is supported

- Serial port enumeration; protocol identification after selecting a port.
- Read device/self information, custom variables, contacts and channels (up to 64 reported slots).
- 23 setting controls across Device & Radio, Location & GPS, Contact Discovery and Telemetry tabs. These include name, radio parameters, fixed coordinates, location sharing, GPS controls, contact discovery mode and type filters, replacement policy, discovery reach, telemetry permissions, extra acknowledgements and path-hash size.
- Edit channel names and explicit 16-byte keys by numbered slot; verify both after writing. Keys are hidden in the editor.
- Frequency dropdown: US/Canada 910.525 MHz, EU/UK narrow 869.618 MHz, EU/UK alternative 869.525 MHz. Bandwidth dropdown: 7.8 through 500 kHz common LoRa choices. Both allow typed custom values. Frequency suggestions change only frequency, not the other radio parameters; they are network examples, not a regulatory certification.
- Versioned JSON profiles and import of the two supplied browser export structures.
- Snapshot export and per-apply verification reports.

Controls are enabled only for recognized values successfully read from the device. GPS interval is conditional on the device reporting it. Fixed-coordinate controls are disabled while GPS is enabled. Unknown custom variables, contact records and browser-specific metadata remain read-only. Firmware flashing, private-key changes, direct flash-file editing and batch writes are not included.

Profile version 2 includes supported settings and optional channel slots; version 1 remains readable. Browser import maps radio, location, other settings, auto-add settings and channels. It explicitly reports skipped fields/metadata and requires review of channel order. Loading an export never restores identity or writes the device.

On the T114 bench unit, the expanded reader retrieved 22 supported settings and 40 channel slots without optional read errors. Expanded hardware writes still require validation.

## Architecture and units

`model.py` owns profile validation and unit conversion. Browser exports report frequency in kHz and bandwidth in Hz; profile/command values use MHz and kHz respectively. `device.py` uses the meshcore Python library's framed Companion serial protocol at 115200 baud. Firmware internal JSON storage is not accessed. `app.py` handles the GUI and sends serial work to a background worker. The adapter accepts an explicit port and can later be used by a multi-device queue; each device will need its own read, capability checks, identity binding and result.

This first implementation uses known Companion commands and fields that are present in responses; this is not general firmware capability discovery. Firmware remains the authority on board-specific radio limits. TX power is conservatively limited to 0–22 dBm and the reported maximum, whichever is lower. Hardware compatibility, persistence across power cycles and T1000-E magnetic USB behavior still require bench validation.

## Windows setup from GitHub

Install Python 3.12 with Tcl/Tk and the Python launcher. Download or clone this repository, run **Setup Windows.cmd** once, then **Start Configurator.cmd**. Setup creates a local virtual environment and installs `requirements.txt`. The launcher prefers that environment. The original development computer can also use its bundled runtime and ignored local dependencies; these are not shipped through GitHub.

Run tests with `.venv\Scripts\python.exe -m unittest discover -v`. GitHub Actions runs the same tests on Windows. Fixtures are synthetic and do not require the private exports or a physical radio.

## Local reference exports

Device exports, JSON profiles, snapshots, reports, local dependencies and secrets are excluded from Git. The original pre-upgrade and post-upgrade exports remain local references. See `PROJECT_CONTEXT.md` for their role in guiding the next development steps.

## Protocol references

- https://github.com/meshcore-dev/meshcore_py
- https://github.com/meshcore-dev/meshcore_py/blob/main/src/meshcore/commands/device.py

Snapshots may contain channel secrets, PINs, contact details and location. Keep them local with your configuration backups.
