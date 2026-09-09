# MeshCore Configurator — USB & Bluetooth

Double-click **Start Configurator.cmd**. The launcher starts Python without a persistent command window. Choose **USB** or **Bluetooth**, click **Find devices**, select your radio, then **Read device**. Close other browser/phone connections first. Startup errors are shown in a dialog and saved in local `startup-error.log`.

Hover over any setting label, input or **?** for a short explanation. Click **?** (or Tab to it and press Space/Enter) to keep the explanation open in a dialog. Help also covers channel fields, the USB port and action buttons, and remains available before a device is read.

Every read saves a JSON snapshot under `snapshots`. Optional read errors are recorded rather than presented as a complete backup. Edit fields or load a profile, then use **Review & apply** to inspect changes. Nothing is written by reading or loading a file. Applying checks identity and stale settings, saves a report, sends supported Companion commands, and rereads for verification. On a write error, some settings may already have changed; read again. There is no automatic retry or rollback.

## What is supported

- USB port enumeration and Bluetooth discovery; protocol identification after selecting a device. Windows handles Bluetooth pairing/PIN prompts. BLE connection/read/write remains pending live hardware validation.
- Read device/self information, custom variables, contacts and channels (up to 64 reported slots).
- 23 setting controls across Device & Radio, Location & GPS, Contact Discovery and Telemetry tabs. These include name, radio parameters, fixed coordinates, location sharing, GPS controls, contact discovery mode and type filters, replacement policy, discovery reach, telemetry permissions, extra acknowledgements and path-hash size.
- Edit channel names and explicit 16-byte keys by numbered slot; verify both after writing. Keys are hidden in the editor.
- Frequency dropdown: US/Canada 910.525 MHz, EU/UK narrow 869.618 MHz, EU/UK alternative 869.525 MHz. Bandwidth dropdown: 7.8 through 500 kHz common LoRa choices. Both allow typed custom values. Frequency suggestions change only frequency, not the other radio parameters; they are network examples, not a regulatory certification.
- Versioned JSON profiles and import of the two supplied browser export structures.
- Snapshot export and per-apply verification reports.

Controls are enabled only for recognized values successfully read from the device. GPS interval is conditional on the device reporting it. Fixed-coordinate controls are disabled while GPS is enabled. Unknown custom variables, contact records and browser-specific metadata remain read-only. Firmware flashing, private-key changes and direct flash-file editing are not included. Reviewed batch writes are available through Saved profiles.

Profile version 2 includes supported settings and optional channel slots; version 1 remains readable. Browser import maps radio, location, other settings, auto-add settings and channels. It explicitly reports skipped fields/metadata and requires review of channel order. Loading an export never restores identity or writes the device.

On the T114 bench unit, the expanded reader retrieved 22 supported settings and 40 channel slots without optional read errors. Expanded hardware writes still require validation.

## Architecture and units

`model.py` owns profile validation and unit conversion. Browser exports report frequency in kHz and bandwidth in Hz; profile/command values use MHz and kHz respectively. `device.py` uses the meshcore Python library's framed Companion serial protocol at 115200 baud. Firmware internal JSON storage is not accessed. `app.py` handles the GUI and sends serial work to a background worker. The adapter accepts an explicit port and can later be used by a multi-device queue; each device will need its own read, capability checks, identity binding and result.

This first implementation uses known Companion commands and fields that are present in responses; this is not general firmware capability discovery. Firmware remains the authority on board-specific radio limits. TX power is conservatively limited to −9–22 dBm and the reported maximum, whichever is lower. Hardware compatibility, persistence across power cycles and T1000-E magnetic USB behavior still require bench validation.

## Windows setup from GitHub

Install Python 3.12 with Tcl/Tk and the Python launcher. Download or clone this repository, run **Setup Windows.cmd** once, then **Start Configurator.cmd**. Setup creates a local virtual environment and installs `requirements.txt`. The launcher prefers that environment. The original development computer can also use its bundled runtime and ignored local dependencies; these are not shipped through GitHub.

Run tests with `.venv\Scripts\python.exe -m unittest discover -v`. GitHub Actions runs the same tests on Windows. Fixtures are synthetic and do not require the private exports or a physical radio.

## Local reference exports

Device exports, JSON profiles, snapshots, reports, local dependencies and secrets are excluded from Git. The original pre-upgrade and post-upgrade exports remain local references. See `PROJECT_CONTEXT.md` for their role in guiding the next development steps.

## Protocol references

- https://github.com/meshcore-dev/meshcore_py
- https://github.com/meshcore-dev/meshcore_py/blob/main/src/meshcore/commands/device.py

Snapshots may contain channel secrets, PINs, contact details and location. Keep them local with your configuration backups.

## Interface and settings audit

The light interface uses a navy header, teal action buttons, hover/click help, highlighted pending edits and a pending-change count. Unsupported controls stay disabled. See [SETTINGS_AUDIT.md](SETTINGS_AUDIT.md) for the full settings review, corrections and validation limits.


## Recommendations and battery hints

Every setting has a short suggestion beside a narrower profile input. Five small battery icons show **relative power cost within that setting**: more filled icons means greater cost, not remaining charge. Indicators are omitted where impact is minor, uncertain or unavailable; recommendations stay visible. These are qualitative app heuristics, not measured hours or additive scores. Radio hints describe transmissions, not idle consumption. Traffic, board, GPS duty cycle and battery determine real runtime. Recommendations never change values automatically. Keep frequency, bandwidth, SF and CR matched to your mesh.

Radio airtime guidance follows [Semtech's LoRa FAQ](https://www.semtech.com/design-support/faq/faq-lora) and [modulation tradeoffs](https://www.semtech.com/design-support/faq/P100). Exact five-level thresholds are app heuristics, not Semtech ratings.

## Channels

Existing channels remain visible. **Empty slots to add** exposes that many available slots, each with its actual number. The device maximum and successfully read/empty counts are shown. Reducing the count hides unused rows only; edited rows stay visible. Clear a channel explicitly using an empty name and 32 zero key digits, then review/apply. Profile imports reveal edited slots even beyond the selected count.

## Bluetooth

Requires a working Windows Bluetooth adapter, the installed Bleak dependency and BLE-enabled Companion firmware. A USB-only image cannot be made Bluetooth-capable by this app; see the [MeshCore FAQ](https://docs.meshcore.io/faq/). Pairing is handled by Windows, and PINs are not saved in profiles. The same protocol verification and identity checks apply over either transport. JSON stays the interchange format.

Windows support libraries are installed in the local project. A scanner check on this PC reported Bluetooth unavailable/off, so a real BLE connection and write have not been tested. Discovery filtering, routing and failed-connection cleanup are tested with simulations. USB remains usable.

The compact layout opens at 1180×820 and supports 1100×800. Suggestions align before smaller battery indicators, with no placeholder on unrelated settings.

## Saved profiles and multiple devices

Open **Saved profiles** to keep named profiles inside the app. **Save editor** lets you choose the included settings; name and fixed coordinates start unchecked. Existing named/keyed channels and explicit channel clears can be included, while unchanged empty slots are omitted from editor saves. **Update** replaces a selected profile with the chosen editor values. You can also load, rename, import, export or remove a profile. Removed profiles move into a local archive. Profiles are JSON stored under `profiles/`, including any channel keys; they are excluded from Git. No device identity/private key is included.

Select a saved profile and choose **Apply profile to multiple devices**:

1. Find USB or Bluetooth devices and select targets with Ctrl/Shift, or Select all.
2. Read selected devices. Each target gets its own snapshot and identity.
3. Review changes. Every selected target must report the requested settings/channel slots and satisfy its power limit. Selecting the same radio through two connections is blocked. Exact setting changes and channel names/key-change notices appear in the review.
4. Apply reviewed. The existing single-device adapter checks identity and stale values again, sends changes, and verifies by rereading. Devices are processed sequentially.

A failed device stops the batch; subsequent devices are marked Not attempted. Stop takes effect between devices, so an in-progress operation can finish and report its result. Completed changes are not rolled back. Batch summaries and individual apply reports remain local in `reports/`. A no-change target is labeled No changes at review, not freshly verified. Read again before another batch. Changing selection or rereading invalidates the previous review.

Validation: 44 selected regression tests pass, including 10 new profile/batch tests covering persistence, archives, unsupported targets, duplicate identities, cancellation, no-op labels and partial failure. Additional UI checks covered field-selection defaults, saved-profile loading, two simulated devices and close-during-operation handling. No real multi-device writes were performed. BLE hardware validation is still pending; the existing local BLE dependency was inaccessible to this session, so its separate scanner test was excluded from this run.
