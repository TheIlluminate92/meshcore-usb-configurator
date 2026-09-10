# Next work

Current release: **0.7.0**. See [release notes](CHANGELOG.md) and [validation status](VALIDATION.md).

## Hardware work first

1. Connect a Repeater over USB, collect its exported JSON, confirm role detection and audit its supported CLI responses.
2. Repeat for Room Server firmware. Build direct read/edit/write/verify support against observed capabilities. Existing server presets are reference-only.
3. Bench-test restoration after a deliberate setting change and a two-radio batch with distinct names.
4. Validate live Bluetooth, power-cycle persistence, and SenseCAP T1000-E magnetic USB behavior separately.

## Community ideas to review

The [community findings](COMMUNITY_REQUESTS.md) cite public Reddit and forum discussions. Candidate work includes region/scoping guidance, firmware-aware power-saving controls and contact-list review. These are proposals, not approved implementation commitments.

## Completed in this round

- Identity-bound restore of previous changed settings, with reread/review/verification.
- Sanitized diagnostics and a support ZIP with a GitHub issue handoff.
- Per-device compatibility review and three built-in role starting points.
- Read-only firmware role detection, editable profile notes and dry-run exports.
- Verified portable backups with consistent SQLite history copies.
- Release notes in the updater and a tested packaged restart flow.
