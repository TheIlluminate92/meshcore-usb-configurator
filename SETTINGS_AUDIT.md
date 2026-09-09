# Settings audit — 2026-09-09

Reviewed all 23 setting controls and channel editing against the official
[Companion 1.17.1 command implementation](https://github.com/meshcore-dev/MeshCore/blob/companion-v1.17.1/examples/companion_radio/MyMesh.cpp),
NodePrefs definitions and EnvironmentSensorManager implementation at that tag.
This checks command semantics and stored-value verification, not measured RF performance.

| Controls | Checked behavior and limits |
| --- | --- |
| Name | 1–31 UTF-8 bytes; no embedded null. |
| Frequency, bandwidth | MHz and kHz in profiles; integer kHz and Hz on the wire. Rounded to nearest wire unit. App bandwidth floor 7.8 kHz is narrower than firmware's 7 kHz acceptance floor; board-specific RF support still applies. |
| Spreading factor, coding rate | Whole numbers 5–12 and 5–8. Radio writes preserve reported repeat mode and verify the complete radio group. |
| Transmit power | Signed byte, −9 dBm minimum; app ceiling 22 dBm and reported device maximum. Fixed unsigned library decoding and negative-value encoding. |
| Latitude, longitude | Signed microdegrees, rounded to six decimal places; bounds ±90/±180. Fixed position changes require GPS off. |
| GPS receiver, GPS interval | Only editable when reported as custom variables. Release sensor implementation reports GPS but does not enumerate the interval, despite accepting an interval setter. Interval therefore stays disabled on this T114. App interval range 1–86400 seconds is an application limit. |
| Share location in adverts | Values 0/1; independent of telemetry. |
| Device, location, environment telemetry | Values 0 deny, 1 per-contact flags, 2 all. Requester must pass device/base telemetry permission before location/environment data is returned. Shared command fields are preserved and reread. |
| Contact discovery mode | Automatic-all overrides individual type filters. Selected/manual mode enables those filters. |
| Replace oldest; companion, repeater, room, sensor filters | Bits 1/2/4/8/16. Unknown bits preserved; read-back checks entire flag byte. Replacement is independent of type-selection mode. |
| Discovery reach | 0 unlimited; 1 direct; values 2–64 allow up to value−1 relay hops. |
| Extra acknowledgement transmissions | App offers 0–3; this is an intentional application limit, not the firmware byte's full range. |
| Path hash size | Wire values 0/1/2 represent 1/2/3 bytes. |
| Channels | Only successfully read numbered slots; maximum 64 in app. Names up to 31 UTF-8 bytes, explicit 16-byte keys. Hash-prefixed names do not silently replace imported keys. Changed slots checked for staleness and reread after writing. |

Additional corrections:

- Verification distinguishes adjacent wire units: 1 kHz frequency differences and 1 microdegree coordinate differences no longer pass as equal.
- Configurator profiles with conflicting declared units are rejected.
- Post-apply snapshots identify refreshed settings, reread channel slots, retained channel data and omitted contacts. Use Read device for a fresh full snapshot.
- Unsupported or out-of-range values remain in device data but are not enabled as editable settings.

Validation: 31 automated tests pass, including shared-field preservation, repeat mode,
signed power read/write, coordinate packets, rejection/staleness/mismatch behavior,
channel keys, profile units and serial-handle cleanup. GUI state checks exercised
pending changes, GPS/type-filter dependencies and disabled unsupported fields;
layout checks passed at 1180×850 and 1080×790. The native screenshot tool did not
expose the test window, so visual inspection through that tool was unavailable.

A fresh read of the connected T114 (v1.17.1-d929643) returned 22 editable settings
and 40 channel slots with no optional read errors. GPS interval was not reported.
No hardware settings were written during this audit. Actual write/power-cycle
persistence and T1000-E magnetic USB compatibility still need bench validation.
