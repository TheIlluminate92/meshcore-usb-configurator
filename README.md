# MeshCore Configurator

A portable Windows app for configuring MeshCore Companion radios over USB or Bluetooth. Profiles use JSON; the app communicates through supported Companion commands, never by editing internal flash files.

## Run the portable app

Open **! MeshCore Configurator.exe**. Move or back up the **whole portable folder** to carry your information to another PC. Python is bundled; no separate installation is needed.

All persistent files live in **User Data**, beside the executable. This supporting folder is hidden in Explorer by default so the EXE is easy to find. Enable **View → Show → Hidden items** to inspect it. Keep the portable folder somewhere writable, such as Documents or a USB drive.

The header provides **Light / Dark / System** and **App updates**. The app remembers the theme and window placement. Battery symbols appear before their descriptions and indicate relative cost within that setting—not remaining charge or measured runtime. Suggestions never change settings automatically.

## Configure one radio

1. Select USB or Bluetooth, find the connection and choose **Read device**. Close other apps holding the same radio connection.
2. Edit supported fields, load a JSON profile, or choose a saved profile. Device values and profile values are displayed separately.
3. Use **Review & apply** to inspect the proposed changes before writing. The app checks identity and stale values, sends commands, then rereads to verify.

Every read saves a snapshot. Optional read errors are retained; a partial snapshot is not presented as a complete backup. On a write failure, some values may already have changed: reread before trying again. There is no automatic device rollback or retry.

The four settings pages provide 23 conditional controls covering radio settings, location/GPS, contact discovery and telemetry. Controls remain disabled when the necessary value was not reported or is unsupported. Hover over a field or select **?** for help. GPS-controlled coordinates cannot be edited as fixed positions while GPS is enabled.

Channels are edited by device slot number. **Empty slots to add** exposes additional available slots without deleting existing channels. Clearing a slot requires an explicit empty name and zero key, followed by review. Channel keys remain hidden in comparison views.

## Configure a batch

Open **Batch editor** from the main connection row or a saved profile.

1. Use the header's USB/Bluetooth picker and **Find**. Newly discovered connections are checked by default. Individual checkboxes and **All devices** control the targets.
2. Choose **Read**. Each checked connection is tried; a read failure does not prevent the next connection from being tried. Uncheck unreadable connections before reviewing writes.
3. Choose a **Profile for checked radios**, or **Edit shared**. **Compare** shows differences between already-read radios and the shared profile.
4. Use **More → Individual names & positions** when needed. Review also opens this step if individual values are incomplete. A profile can provide a naming prefix and starting number; names can still be edited individually.
5. **Review** shows the exact changes in **Review changes / results**. **Apply** asks for final confirmation, then processes devices sequentially and verifies each write.

Shared profiles omit personal names and coordinates from the batch document; the individual step handles them. Private device identity is never cloned. Copying all channel slots from the first radio can clear slots on other radios; those changes appear in review. Unsupported settings block the affected target.

A write failure stops the remaining batch. **Stop after current device** lets the current operation finish. Completed changes are not rolled back. Read again before another batch. Actual selection changes invalidate review; duplicate selection notifications do not.

**More → Save shared profile** saves reusable shared settings and naming defaults. Edited profiles are marked in the picker. Numbering restarts from the saved number each time; numbers are not reserved across the entire fleet.

## Profiles, comparison and history

**Saved profiles** supports preview, field/channel scope, load, update, import/export, rename and archive. JSON versions 1 and 2 are readable; known browser export formats are mapped with skipped fields reported. Loading a file never writes a radio.

**History** retains public device identities, previous connections, run targets and per-device results in SQLite. Results can be exported to CSV. Unfinished runs are not resumed automatically or marked verified. A no-change target is labeled **No changes at review**, rather than freshly verified.

For a persistence check, restart a radio yourself, choose its current connection, select its saved run in History, then use **Verify selected radio after restart**. This reads without writing and matches public identity even if the COM port changed. It checks saved expectations and records your restart confirmation separately; the app cannot independently prove a restart occurred.

## App updates

**App updates** checks the latest published stable GitHub release. The repository is currently private: enter a GitHub token with **Contents: read** access to this repository. It stays in memory for that dialog and is never saved or bundled. A public repository can be checked without a token.

After you approve **Install & restart**, the app verifies the release asset's SHA-256 digest and replaces only the executable after exit. User Data stays intact. A previous executable and `update.log` are retained in `User Data/Updates`. If replacement fails, the existing EXE remains; consult the log. Update checks are separate from radio work and are blocked while device operations or batch work are active.

A source commit is not itself an installable update. The release build must complete and publish the Windows asset. The disposable Windows replacement test passes, including exit waiting, restart, backup and data preservation. Authenticated GitHub download plus app installation still needs live validation.

## Validation and limitations

The latest local suite passed **94 tests**, and the portable EXE passed its startup check. A prior read-only Heltec T114 check on firmware v1.17.1 returned **22 settings, 40 channel slots and zero optional read errors**; GPS interval was not reported.

Live Bluetooth configuration, real multi-radio writes, persistence after radio restart, and Seeed SenseCAP T1000-E magnetic USB compatibility remain unvalidated. See [VALIDATION.md](VALIDATION.md), [CHANGELOG.md](CHANGELOG.md), [SETTINGS_AUDIT.md](SETTINGS_AUDIT.md) and [FIRMWARE_MAP.md](FIRMWARE_MAP.md).

Frequency suggestions are network examples, not regulatory certification. Frequency, bandwidth, spreading factor and coding rate must match the intended mesh. The reader implements known supported commands rather than general firmware capability discovery. Firmware flashing and private-key changes are outside the app's scope.

## Development

On Windows, install Python 3.12 with Tcl/Tk, then run **Setup Windows.cmd** and **Start Configurator.cmd**. Source runs retain data in the project folder. Run tests with `.venv\Scripts\python.exe -m unittest discover -q`.

With the project virtual environment activated, run `build_exe.ps1` to create the windowed EXE in `dist`. Increase `app_version.py` and push to main to trigger the Windows release workflow, which tests, builds and publishes a versioned EXE and portable ZIP. Published version assets are not overwritten. A documentation-only change does not require a new application version.

Private exports, snapshots, profiles, databases, reports, credentials, bundled runtimes and build outputs are excluded from Git. These local files can contain channel secrets, contacts and locations; published release packages contain only the application.

Protocol references: [MeshCore firmware](https://github.com/meshcore-dev/meshcore), [MeshCore Python client](https://github.com/meshcore-dev/meshcore_py). See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for implementation boundaries.
