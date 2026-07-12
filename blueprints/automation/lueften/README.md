# Airing Reminder – Open/Close Windows (Summer Cooling)

Reminds you **once in the morning** to close the windows (outside is warmer
than inside), and **once in the evening** to open them for airing out
(outside is cooler than inside). Optionally via TTS announcement on any
number of media players and/or push notification to all persons who are
home. Window sensors are optional.

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

- **Trigger:** Two template triggers compare outdoor and indoor
  temperature. "Close" fires exactly once when the outdoor temperature
  crosses the indoor temperature (plus hysteresis) from below to above;
  "Open" fires exactly once when it crosses it (minus hysteresis) from
  above to below. The required hold duration (`for:`) prevents brief
  outliers from triggering it. Because these are genuine state transitions,
  each of the two triggers naturally fires only once per half-day — no
  extra helper entities are needed.
- **Time window:** The configured morning/evening windows must also be
  respected, so that, for example, a temperature drop in the middle of the
  night doesn't trigger an announcement.
- **Window sensors (optional):** If configured, "close" is only announced
  when at least one sensor reports "open", and "open" only when at least
  one reports "closed". Without sensors, this check is skipped.
- **Push:** From the list of selected `person` entities, all those
  currently `home` are filtered out. For each of them, every linked
  `device_tracker` is resolved to its owning device via the device registry
  (`device_trackers` → `device_id`), and `notify.send_message` is called
  targeting that `device_id` directly. Any number of persons can be
  selected, and a person with multiple devices (e.g. phone and tablet) gets
  notified on all of them.
- **TTS:** If a TTS engine and at least one media player are configured,
  `tts.speak` is played on all selected players.

## Inputs

| Input | Required | Description |
|---|---|---|
| `indoor_temp` / `outdoor_temp` | yes | Indoor/outdoor temperature sensors |
| `hysteresis` | no (default 1 °C) | Buffer against flapping |
| `min_indoor_open` | no (default 22 °C) | Indoor temperature above which "open" makes sense in the evening |
| `debounce_minutes` | no (default 5) | Minimum hold duration of the temperature condition |
| `morning_start` / `morning_end` | no (05:00–11:00) | Time window for "close" |
| `evening_start` / `evening_end` | no (18:00–23:59) | Time window for "open" |
| `notify_persons` | no | Persons who receive a push notification while home |
| `tts_engine` / `tts_media_players` | no | TTS announcement target |
| `window_sensors` | no | Window/door contacts for plausibility checking |
| `notify_title`, `message_close`, `message_open` | no | Customizable texts |

## Known limitations

- Requires Home Assistant **2024.6 or newer**, since push notifications are
  sent via the generic `notify.send_message` action targeting a
  `device_id` — this only works for notify targets that have been migrated
  to notify entities (the `mobile_app` integration was one of the first).
- Resolving the push target assumes the person's device tracker(s) come
  from the `mobile_app` integration (i.e. the Home Assistant companion app
  was installed and set up on that device). With trackers from other
  sources (e.g. `owntracks`/`gpslogger` without an associated `mobile_app`
  device), no device is found for that person and nothing gets sent —
  silently, with no error. In that case, check under *Settings → Devices &
  Services → Devices* whether the person's tracker(s) belong to a
  `mobile_app` device.
- No `input_boolean`/helper is required; if Home Assistant restarts while
  the temperature condition is already met, the trigger may fire again
  depending on the remaining `for:` state (standard behavior of template
  triggers with `for:`).

## Verification after import

1. Create an automation from the blueprint and fill in all required
   fields.
2. In *Developer Tools → Template*, check both trigger templates against
   current sensor values.
3. Run the automation once manually via *"Run"* (this skips trigger
   conditions but still evaluates the `choose` conditions and actions).
4. Observe over a day or two (via automation traces) that only one
   announcement occurs per half-day.
