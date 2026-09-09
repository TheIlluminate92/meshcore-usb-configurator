# Validation status

Current application version: **0.5.2**. Latest completed local run: **94 automated tests passed**, plus portable executable startup with 23 controls and history initialization. Documentation maintenance does not constitute a new application test run.

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
| Updates | Version/digest/path/redirect safeguards and tampered/independent staging tested. Disposable Windows helper test passes: parent exit wait, EXE replacement, restart, retained backup and user data. Anonymous v0.5.1 release lookup and EXE download passed with SHA-256 verification against public GitHub. Local replacement helper passes separately; one combined app-driven update remains unvalidated |
| Release pipeline | Workflow is committed; publishing completion is not asserted by the local test results |

## Next bench checks

Use the T114 bench unit first: make one deliberate setting change, review it, apply, verify, restart manually, and check the saved expectations. Then test a two-radio batch with unique names and a deliberate unavailable connection. Validate BLE and T1000-E separately. Keep resulting snapshots and reports local.

An update test needs a newer published release; public access requires no token. Confirm that the version changes after restart and profiles/history remain intact. Retain the previous executable until this succeeds.

The explicit `integration_update_probe.py` check compiles harmless Windows executables in a temporary folder and runs the real replacement helper. It never opens radios or reads the user workspace. Fault-injection unit tests additionally cover interrupted/concurrent saves, preference write failures, newer database schemas, post-write identity/channel mismatches and disconnect errors.
