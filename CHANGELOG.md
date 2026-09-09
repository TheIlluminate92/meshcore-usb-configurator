# Changelog

## Bug hunt — 2026-09-09

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
