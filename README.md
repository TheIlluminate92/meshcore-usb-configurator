# MeshCore Configurator — USB & Bluetooth

For the standalone Windows build, double-click **MeshCore Configurator.exe**; Python and a command window are not required. The packaged app stores profiles, history and reports under `%LOCALAPPDATA%/MeshCore Configurator`. Existing source-app profiles remain in the original `profiles` folder and can be imported through Saved profiles.

For the source version, double-click **Start Configurator.cmd**. The launcher starts Python without a persistent command window. Choose **USB** or **Bluetooth**, click **Find devices**, select your radio, then **Read device**. Close other browser/phone connections first. Startup errors are shown in a dialog and saved in local `startup-error.log`.

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

Validation: 44 selected regression tests pass, including 10 new profile/batch tests covering persistence, archives, unsupported targets, duplicate identities, cancellation, no-op labels and partial failure. Additional UI checks covered field-selection defaults, saved-profile loading, two simulated devices and close-during-operation handling. No real multi-device writes were performed. BLE hardware validation is still pending; the Bluetooth dependency issue from that run has since been repaired; see the bug-hunt validation below.

## Batch editor with individual names

The main **Batch editor** button works without creating a saved profile first. Find and select the plugged-in devices, then **Read selected**. **Edit shared settings** opens a form containing settings reported by every selected radio. Checked fields use one value across the batch; unchecked fields stay unchanged. Initial values come from the selected saved profile, or the first device for a new batch. Each board's limits still apply.

Shared channels can be left unchanged, taken from the profile, or copied from the first device. Copying all slots includes empty slots and may clear other devices' channels, explicitly shown at review.

**Next: individual devices** opens a page for each radio showing its connection, model, current name and abbreviated public identity. Keep or edit each name, or use a prefix to number them (Tracker-01, Tracker-02, etc.). Names must be distinct within the selection. Optional fixed coordinates are set per device only when GPS is off. Private identities/keys are never copied. Personal name/position values from saved profiles are omitted from the shared batch document; this walkthrough handles them instead.

Previous/Next only stage edits. Finish opens the combined shared-plus-individual review, then **Apply reviewed** performs the writes. Selecting another device or editing shared values invalidates approval. Rereading clears staged individual values. Cancelling the naming popup discards its draft without writing. Individual values are tied to the device identity, not the COM port. **Save shared profile** saves reusable shared settings without the individual names/positions.

Validation: 50 selected regression tests pass, including shared-plus-individual plan composition, duplicate names, wrong override fields, per-device coordinates, numbering through two simulated radios, cancellation and supported-field filtering. Real multi-radio writing remains a bench-validation task.

Setting dropdowns in the main and shared batch editors open when clicking anywhere in the field. Typing while the list is open returns focus to the field and replaces its value; picking a listed option still works normally. Known option labels are case-insensitive. Values still pass the existing validation before review/apply; unreported fields remain disabled.

## Bug-hunt fixes

- Invalid typed numbers such as NaN/infinity no longer crash battery hints. Applying still rejects them.
- Channels-only profiles and intentionally unchecked shared settings no longer automatically expand into radio-setting changes when reopened.
- Malformed profile names/identifiers are reported as unreadable files without breaking the library.
- Updating a saved profile retains its channel-slot scope, and refuses to silently drop settings/slots not read by the current editor.
- Batch writes preflight all channel slots included in the shared profile, including unchanged ones, to catch changes since review.
- The local inaccessible Bluetooth dependency was replaced with a freshly extracted project-local copy. The launcher prefers `bluetooth_libs/` when present; downloaded dependencies stay excluded from Git. Normal Windows setup still installs requirements into the virtual environment.

Current validation: all 60 tests pass, including scanner filtering and the new regression cases. A read-only COM4 check returned 22 settings and 40 channels with zero read errors. Bluetooth now loads correctly, but Windows still reports its scanner unavailable/off. No hardware writes were performed; live Bluetooth connections and multi-radio writes still need bench validation.

## Compare, naming and saved history

Use **Preview** in Saved profiles to see included values and channel names. **Compare** checks the current radio against a profile; **Compare devices** in the batch editor compares the selected, already-read radios side by side. Differences and missing values are highlighted, with a differences-only filter. Channel keys are compared but never displayed in these views. Read again when you need fresh comparison data.

Each saved profile can carry a simple naming prefix and starting number. For example, prefix `Truck` and start `10` proposes `Truck-10`, `Truck-11`, and so on when you use numbering in the individual-device wizard. You can still edit each name before review. Numbering starts from the saved value each time; it does not reserve fleet-wide numbers. JSON import/export preserves these optional naming defaults.

A small local SQLite database at `data/history.sqlite3` remembers public device identities, last-seen connections, run targets and per-device results. Profiles remain portable JSON; the database needs no server or additional installation. A radio can be recognized after its COM port changes. History can export results to CSV. Progress is displayed per device; completed results remain available after reopening the app. An unfinished run is never automatically resumed or marked verified: reread before starting a new review.

For a persistence check, restart the radio yourself, select its current connection, choose the saved run in **History**, then choose **Verify selected radio after restart**. Confirm that you restarted it. The app rereads without writing, matches the public identity, and checks the requested settings/channels against the saved expectations. It records matches, mismatches and your restart confirmation separately from immediate write verification; it cannot independently prove a restart occurred.

The main editor asks before discarding pending changes when loading another profile, changing connections, rereading, opening batch work or closing. The batch window keeps its progress and stop controls visible at its minimum size.

The local database can contain configuration values, including channel keys. Keep `data/` private along with profiles, reports and snapshots; all are excluded from Git.

## Building the Windows executable

After installing the project requirements in a Python 3.12 Windows environment with Tcl/Tk, run `build_exe.ps1`. The standalone windowed executable is produced under `dist`. Build outputs and private data are excluded from Git. The packaged entry point sets up bundled Tcl/Tk before importing the GUI library.
