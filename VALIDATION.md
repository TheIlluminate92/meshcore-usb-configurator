# Validation status

Current application version: **0.5.0**. Latest completed local run: **81 automated tests passed**, plus portable executable startup with 23 controls and history initialization. Documentation maintenance does not constitute a new application test run.

| Area | Evidence / remaining work |
| --- | --- |
| Settings and profile validation | Automated coverage for supported values, groups, scope preservation and malformed input |
| Batch selection and profiles | Automated coverage for checkbox state, review invalidation, removed USB rows, profile refresh and individual overrides |
| Failure and cancellation | Simulated read continuation, write-stop behavior, saved per-device results and interrupted-run handling |
| UI | Populated settings pages checked at minimum/full-screen sizes; batch footer fit; theme switching and battery ordering tested |
| Portable application | Built EXE starts with bundled dependencies; existing desktop data copied to the local handoff folder, originals retained |
| USB reading | Prior T114 v1.17.1 read: 22 settings, 40 channel slots, no optional read errors |
| Hardware writes | Expanded real-device writes and multi-radio batches still need bench testing |
| Bluetooth | Code and simulated transport tests exist; live connection/read/write unvalidated |
| Restart persistence | Identity matching and expected-value comparison tested with synthetic reads; real power-cycle persistence unvalidated |
| T1000-E | Magnetic USB and board-specific behavior unvalidated |
| Updates | Version/digest/path/redirect safeguards tested; portable startup passes. Live authenticated download, replacement and restart still need end-to-end validation |
| Release pipeline | Workflow is committed; publishing completion is not asserted by the local test results |

## Next bench checks

Use the T114 bench unit first: make one deliberate setting change, review it, apply, verify, restart manually, and check the saved expectations. Then test a two-radio batch with unique names and a deliberate unavailable connection. Validate BLE and T1000-E separately. Keep resulting snapshots and reports local.

An update test needs a newer published release and repository access. Confirm that the version changes after restart and profiles/history remain intact. Retain the previous executable until this succeeds.
