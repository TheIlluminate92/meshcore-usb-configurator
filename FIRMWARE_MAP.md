# Firmware reference

Primary reference: [official MeshCore repository](https://github.com/meshcore-dev/MeshCore).
Initial command audit: [Companion 1.17.1 MyMesh.cpp](https://github.com/meshcore-dev/MeshCore/blob/companion-v1.17.1/examples/companion_radio/MyMesh.cpp).
The connected build reported v1.17.1-d929643; the release tag is the baseline, not proof that every build option matches.

| Export area | Firmware command path | Editor direction |
| --- | --- | --- |
| Radio | SET_RADIO_PARAMS (11), APP_START (1), DEVICE_QUERY (22) | Preserve repeat mode alongside grouped radio edits. |
| Location | SET_ADVERT_LATLON (14), APP_START | Fixed coordinates; check GPS behavior before expanding controls. |
| Other settings | SET_OTHER_PARAMS (38), APP_START | Preserve telemetry and acknowledgement fields when changing contact or location policy. |
| Channels | GET_CHANNEL (31), SET_CHANNEL (32) | Slot, name and 16-byte secret; do not infer retention support from browser JSON. |
| Auto-add | GET_AUTOADD_CONFIG (59), SET_AUTOADD_CONFIG (58) | Decode flags before exposing controls; maximum hop value is capped at 64. |

These groups now have editor controls and read-back checks. GPS controls use reported custom variables; path-hash mode uses its dedicated command. Firmware-only preferences and browser metadata are not automatically editable. Private identity is excluded from fleet profiles. Both original exports stay local.
