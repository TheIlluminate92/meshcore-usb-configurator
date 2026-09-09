# Changelog

## Batch bug hunt — 2026-09-09

- Fixed newly saved shared profiles missing from the batch picker; saving now refreshes the list and active name. Loading rechecks the library and reports removed/unreadable profiles clearly.
- Marked edited shared settings in the picker so they are not mistaken for an unchanged saved profile.
- USB Find now removes disconnected ports and their stale snapshots while retaining Bluetooth discoveries. New row IDs remain unique after removals.
- Added a device-list scrollbar for larger fleets and keyboard focus when clicking device checkboxes.
- Duplicate selection notifications no longer discard a valid review; actual checkbox changes still invalidate it.
- Validation: 75 tests passed, including failed-port read continuation, refresh/identity-row handling, profile changes, selection guards and existing stop/failure checks. No hardware writes; live BLE and multi-radio writes remain unvalidated.

## Batch editor cleanup — 2026-09-09

- Consolidated discovery into a header transport picker with Find and Read. Newly discovered devices are checked by default; Read tries all checked connections and continues past read failures.
- Added per-device checkboxes and a master checkbox; selection is locked during operations.
- Added a saved-profile picker for shared settings and naming defaults. Personal names and coordinates remain in the individual step.
- Kept Edit shared and Compare visible; moved naming and saving into More. Review and Apply sit beside a smaller labeled review/results area.
- Validation: 71 tests pass, including checkbox behavior, profile scope and minimum batch-window layout. Packaged executable startup passed. No hardware writes.

## Equal columns on settings pages — 2026-09-09

- Applied equal-width columns to Device & radio, Location & GPS, Contact discovery and Telemetry. Device values and setting labels now wrap, removing the fixed-width truncation. Suggestions and battery symbols share a reserved column.
- Validation: 70 tests pass; all four populated pages fit at 1100x800 and 1920x1032, including long choice labels. Rebuilt the Windows executable.

## First-page cleanup and Windows executable — 2026-09-09

- Added a standalone windowed Windows executable with bundled Python and dependencies; packaged user data lives in LocalAppData.
- Expanded Device & radio suggestions with larger, wrapping text and reserved space for battery symbols; other pages retain their layout.
- Fixed bundled Tcl/Tk initialization order during executable launch testing.
- Validation: 70 automated tests passed, including minimum-window layout. Packaged startup opened all 23 settings and initialized history. No radio writes.

## Fleet workflow — 2026-09-09

- Added profile previews and side-by-side comparisons with missing-value and differences-only views; channel keys remain hidden.
- Added per-profile naming prefixes and starting numbers, preserved through JSON import/export.
- Added local SQLite history, recognition by public identity across connection changes, per-device progress and CSV result exports. Profiles remain JSON.
- Added read-only verification against saved expectations after a user-confirmed radio restart. Restart confirmation and reread results are recorded separately.
- Added pending-edit discard prompts and reserved space for batch progress/stop controls at the minimum window size.
- Validation: automated persistence, comparison, naming, failure, identity and restart-check tests; live hardware writes, restart persistence and Bluetooth remain pending bench validation.

## Bug hunt â€” 2026-09-09

Fixes shipped in commit [af76e77](https://github.com/TheIlluminate92/meshcore-usb-configurator/commit/af76e77c4efd105498f83d479bc29c6c26e5f234).

### Fixed

- **Battery hint crashes:** typing non-finite numbers such as `NaN`, `inf`, or `1e999` could throw an error while updating the power-cost display. The hint now hides for those inputs; configuration validation still rejects them.
- **Unexpected shared settings:** reopening a channels-only profile or an intentionally empty shared selection could select radio settings automatically. The batch editor now preserves the chosen scope.
- **Profile library loading:** malformed profile names could break sorting and prevent the library from opening. Invalid names and identifiers are now listed as unreadable files, leaving valid profiles usable and the files untouched.
- **Profile updates changing scope:** updating a saved profile could add unrelated channel slots or omit settings unavailable on the current device. Updates now retain the existing channel-slot scope and refuse to silently drop unread settings or slots.
- **Batch channel staleness:** profile channels that already matched at review were omitted from the checks before writing other changes. All included profile channels are now checked for changes since review before a batch device is written.
- **Local Bluetooth dependency loading:** the installed Bluetooth package was inaccessible on the development PC. A fresh local copy was extracted, and the launcher now prefers `bluetooth_libs/` when available. Downloaded dependencies remain outside Git; normal Windows setup installs them from `requirements.txt`.

### Validation

- All **60 automated tests passed**, including new regression cases for these failures.
- A read-only T114 check returned **22 settings and 40 channel slots**, with **zero read errors**.
- No hardware settings were written during the bug hunt.

### Still needs validation

- Windows reports Bluetooth scanning unavailable/off on the development PC. A live BLE connection and configuration write remain untested.
- Real multi-device writes and persistence after restarting the radios still require bench testing.
