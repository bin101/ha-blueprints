# Airing Reminder – Open/Close Windows (Summer Cooling)

**Current version:** 1.0.1 ([CHANGELOG](CHANGELOG.md))

Reminds you **once in the morning** to close the windows (outside is warmer
than inside), and **once in the evening** to open them for airing out
(outside is cooler than inside). Optionally via TTS announcement on any
number of media players and/or push notification to any number of
directly selected notify targets. Window sensors are optional. Both the
TTS and the push step can be tested on demand straight from the automation
editor.

## Import

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2Fbin101%2Fha-blueprints%2Fmain%2Fblueprints%2Fautomation%2Flueften%2Flueften.yaml)

Click the button above to open the blueprint import dialog directly in your
Home Assistant instance. If it doesn't work, import manually in Home
Assistant under *Settings → Automations & Scenes → Blueprints → Import
Blueprint* using this URL:

```
https://raw.githubusercontent.com/bin101/ha-blueprints/main/blueprints/automation/lueften/lueften.yaml
```

## How it works

- **Trigger & alternation:** Two template triggers compare outdoor and
  indoor temperature. "Close" fires when the outdoor temperature crosses
  the indoor temperature (plus hysteresis) from below to above; "Open"
  fires when it crosses it (minus hysteresis) from above to below. The
  required hold duration (`for:`) prevents brief outliers from triggering
  it. These triggers only ever *start* a single self-sustaining wait loop,
  which then drives itself: it announces "close", then blocks waiting for
  the "open" threshold before it can announce "close" again — and vice
  versa. So announcements strictly **alternate** close → open → close and
  the same reminder is never sent twice in a row, even if the sensor flaps
  repeatedly around one threshold (the redundant triggers are dropped by
  `mode: single` while the loop is waiting). No helper entities are needed
  — the loop's position *is* the memory of which side was announced last.
- **Time window (TTS only):** The TTS announcement additionally respects
  the configured morning/evening windows, so that, for example, a
  temperature drop in the middle of the night doesn't trigger a spoken
  announcement. The push notification is **not** time-restricted — it
  goes out whenever the underlying temperature/window-sensor condition is
  met, any time of day.
- **Window sensors (optional):** If configured, "close" is only announced
  when at least one sensor reports "open", and "open" only when at least
  one reports "closed". Without sensors, this check is skipped.
- **Push:** You pick the `notify` entities to send to directly (e.g.
  `notify.mobile_app_yourphone`) — no guessing of service names, no
  detour through a person's device trackers. For each selected target, on
  a real automatic run, the blueprint looks up its device and only sends
  if that device has a linked `device_tracker` reporting `home`; a target
  without a linked tracker, or that isn't home, is skipped.
  `notify.send_message` is called with `target: {entity_id: ...}` for each
  target that passes this check.
- **TTS:** If a TTS engine and at least one media player are configured,
  `tts.speak` is played on all selected players.
- **On-demand testing:** Each send step is its own named, independently
  gated action — "Send TTS announcement (close windows)", "Send push
  notification (close windows)", and the "(open windows)" equivalents — no
  helper entities required. They live inside the wait loop, but Home
  Assistant lets you run any individual action step in isolation: open the
  automation, find the step, and use its **Run** button (⋮ menu) to fire it
  immediately. A step run this way has no trigger context, so its gate's
  "no trigger context" fallback clause makes it run regardless of
  temperature/time, it falls back to the separate `test_message` text, and
  the push steps fall back to notifying *all* configured notify targets
  regardless of presence (so you can verify delivery even while away). Each
  send step declares everything it needs (message text, notify targets) in
  its *own* `variables:` step, because Home Assistant's per-action "Run"
  test does not carry over variables defined outside the action being
  run — see [Testing and troubleshooting automations](https://www.home-assistant.io/docs/automation/troubleshooting/).
  (Running the *whole* automation manually instead of a single step does
  nothing on purpose — the loop is a no-op without a real trigger, so it
  won't hang on the first wait.)

## Inputs

| Input | Required | Description |
|---|---|---|
| `indoor_temp` / `outdoor_temp` | yes | Indoor/outdoor temperature sensors |
| `hysteresis` | no (default 1 °C) | Buffer against flapping |
| `min_indoor_open` | no (default 22 °C) | Indoor temperature above which "open" makes sense in the evening |
| `debounce_minutes` | no (default 5) | Minimum hold duration of the temperature condition |
| `morning_start` / `morning_end` | no (05:00–11:00) | Time window for "close" |
| `evening_start` / `evening_end` | no (18:00–23:59) | Time window for "open" |
| `notify_targets` | no | Notify entities to send push notifications to (only while their linked device is home) |
| `tts_engine` / `tts_media_players` | no | TTS announcement target |
| `window_sensors` | no | Window/door contacts for plausibility checking |
| `notify_title`, `message_close`, `message_open` | no | Customizable texts |
| `test_message` | no | Message text used when manually running the TTS/push action for testing |

## Known limitations

- Requires Home Assistant **2024.6 or newer**, since push notifications are
  sent via the generic `notify.send_message` action, which needs the
  target to be exposed as a `notify` entity (not just a legacy
  `notify.mobile_app_<name>` service). If your phone doesn't show up when
  picking `notify_targets`, check under *Settings → Devices & Services →
  Entities* (filter: "notify") whether it has such an entity yet.
- Presence-gating requires a `device_tracker` linked to the target's
  device that reports `home`. On a real automatic run, a target is
  skipped whenever no such tracker is found — including if the device
  registry doesn't link one the way you'd expect. If push isn't arriving,
  check under *Settings → Devices & Services → Devices* that the target's
  device has an associated `device_tracker` entity and that it correctly
  shows `home` while you're there.
- No `input_boolean`/helper is required. The alternation memory lives in
  the running wait loop, so it does not survive a Home Assistant restart or
  an automation reload: after a restart the loop relaunches and always
  begins by waiting for the *close* threshold. If a restart happens between
  the evening "open" and the next morning's "close", the first "open" it
  would have announced that following evening is skipped once — normal
  alternation resumes from the next "close". This is a deliberate trade-off
  for staying helper-free; it never causes a *duplicate* notification, only
  (rarely, right after a restart) one skipped one.

## Verification after import

1. Create an automation from the blueprint and fill in all required
   fields.
2. In *Developer Tools → Template*, check both trigger templates against
   current sensor values.
3. Open the automation in the editor and run the individual "Send TTS
   announcement (…)" and "Send push notification (…)" steps (⋮ → **Run**)
   to confirm TTS and push each reach their targets, independent of the
   current temperature/time.
4. Observe over a day or two (via automation traces) that announcements
   strictly alternate close → open → close, i.e. only one announcement per
   half-day and never the same side twice in a row.
