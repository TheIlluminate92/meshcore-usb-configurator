# Project context

Windows desktop configurator for MeshCore Companion radios, initially a Heltec T114 nRF52840 on v1.17.1. Later bench validation should cover SenseCAP T1000-E magnetic USB. The original pre-upgrade export documents the working fleet configuration; the post-upgrade export is a comparison reference. Both remain local and do not authorize identity cloning or automatic restoration.

## Architecture

- `model.py`: supported settings, validation, unit conversion and JSON profiles. Browser radio units are converted to profile/protocol units.
- `device.py` and `serial_connection.py`: USB/BLE transport, reported settings, identity/stale checks, grouped-value preservation and reread verification.
- `app.py`, `batch_ui.py`, `batch_editor.py`: main editor, checkbox-based batch selection, shared settings, individual naming and reviewed sequential application.
- `profile_library.py`, `comparison.py`, `history_store.py`, `restart_check.py`: scoped JSON profiles, comparisons, local SQLite history and verification after user-confirmed restart.
- `app_paths.py`, `preferences.py`, `theme.py`: portable data location and appearance preferences. Packaged data stays in the adjacent hidden User Data folder; source runs use the project folder.
- `updater.py`, `update_ui.py`, release workflow: explicit GitHub release updates with anonymous public access, digest validation, retained previous EXE and deferred replacement.

## Boundaries

Use supported Companion protocol commands; never modify internal flash files. Enable only options justified by reported data and implemented protocol operations. Preserve unmodified grouped values and unknown fields. Batch names/positions are identity-bound individual overrides; a shared profile never clones device identity.

Read, edit, review, write, verify remain separate steps. Stop on batch write failure; no automatic retry, rollback or resumption of interrupted writes. A no-change plan is not a new verification. Restart confirmation is user supplied, not independently detected.

## Current handoff

Portable version 0.5.2 includes four equal-column settings pages, dark/light/system themes, checkbox batch selection, saved-profile application, comparison/history, naming defaults and update controls. User is testing the portable build; do not replace their running EXE or alter their data during documentation/maintenance work. The repository is now public; the updater uses anonymous GitHub release access.

The latest local validation is 94 passing tests, disposable Windows updater integration and packaged startup. Hardware and live-update gaps are tracked in VALIDATION.md. CHANGELOG.md retains historical bug notes; historical test counts are not the current suite count.
