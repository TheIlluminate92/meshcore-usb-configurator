# Project direction

Build a small Windows GUI for hardwired configuration of MeshCore Companion USB devices. Initial bench device: Heltec T114 nRF52840, observed firmware v1.17.1-d929643. Later validate Seeed SenseCAP T1000-E magnetic USB and support applying profiles to multiple devices.

The full pre-upgrade browser export is the working reference for the user's fleet setup, not merely a recovery backup. The post-upgrade export is a comparison reference. Neither is authorization to restore configuration or clone identity. Both original exports remain local and are excluded from Git.

Use those references and the supported protocol to determine useful controls: names, grouped radio options, channels, contact auto-add behavior, telemetry and location behavior. Avoid exposing arbitrary raw values as editable fields. Distinguish fixed coordinates from GPS-controlled position before expanding location editing. Preserve unknown or unsupported settings.

JSON is the application profile/interchange format. The application communicates using supported Companion commands, never by editing firmware flash files. Browser export JSON does not prove anything about the firmware's internal storage schema.

Current implementation provides 23 conditional setting controls plus channel editing, with grouped preservation and reread verification. The expanded USB read on the T114 returned 22 settings and 40 channel slots without errors; GPS interval was not reported. A prior write attempt failed opening COM4; a cleanup race was fixed and tested with the actual asynchronous serial transport over a loopback port. Successful hardware writing and persistence after restart have not yet been confirmed.

Next development: validate expanded writes on the T114; inspect additional hardware-specific settings only where supported protocol operations exist; then build a device-by-device batch queue with individual reports and naming rules. Channel profile handling must not copy private device identity.

2026-09-09: refreshed desktop theme and pending-edit feedback; audited all controls against Companion 1.17.1. Fixed signed power, wire precision and snapshot-scope reporting. 31 tests pass; fresh COM4 read returned 22 settings/40 channels without errors. No hardware writes performed. Details in SETTINGS_AUDIT.md.


Added no-console launcher, per-setting qualitative battery costs/recommendations, existing-plus-N-empty channel editor and USB/Bluetooth selection. Bluetooth runtime installed locally; Windows scan reports Bluetooth unavailable/off. BLE hardware validation pending. Recommendations are advisory; no automatic firmware or radio changes.

Added Saved profiles tab (local named JSON, explicit field selection, update/load/import/export/rename/archive) and modal multiple-device workflow. New profiles omit names/coordinates by default; unchanged empty channels omitted from editor saves. Per-device snapshots and reviewed plans; unsupported settings block selected targets; duplicate identities rejected. Sequential writes call existing verified adapter; stop on failure/cancel between devices; reports saved locally. Main close waits for active batch. 44 selected tests and simulated fleet UI checks pass; real batch writes/BLE still unvalidated.

Batch editor now opens directly from the main connection row, without requiring a saved profile. Shared settings editor uses reported-field intersection and per-target validation; channels unchanged/profile/copy-first options. Individual wizard cycles names, numbering prefix and optional fixed coordinates; identity-keyed overrides, duplicate-name blocking, cancellation draft isolation. Shared profile saving excludes names/coordinates. Final combined review precedes existing sequential verified writer. 50 selected tests pass.
