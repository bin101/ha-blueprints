# ha-blueprints

A collection of custom [Home Assistant](https://www.home-assistant.io/)
**blueprints** for automations. Each blueprint lives in its own subfolder
under `blueprints/<domain>/<name>/` with its own `README.md` and can be
imported directly into Home Assistant via an import link.

## Available blueprints

### [Airing Reminder – Open/Close Windows](blueprints/automation/lueften/README.md) (automation)

Announces once in the morning to close the windows and once in the evening
to open them, based on indoor/outdoor temperature. Optional TTS
announcements on any number of media players, push notifications to
persons who are home, and optional window sensors for plausibility
checking. See the [blueprint's README](blueprints/automation/lueften/README.md)
for all inputs and details.

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2Fbin101%2Fha-blueprints%2Fmain%2Fblueprints%2Fautomation%2Flueften%2Flueften.yaml)

## Structure

```
blueprints/
└─ <domain>/            # e.g. automation, script, template
   └─ <blueprint-name>/
      ├─ <blueprint-name>.yaml   # the actual blueprint
      └─ README.md               # detailed docs, import link, inputs
```

New blueprints are added following the same pattern: their own subfolder,
their own YAML file, their own README, plus a new section above with a
short description and its own "Open in Home Assistant" import button.

## Manual import (alternative)

If the import button doesn't work, in Home Assistant go to *Settings →
Automations & Scenes → Blueprints → Import Blueprint* and paste the raw URL
of the desired `.yaml` file, e.g.:

```
https://raw.githubusercontent.com/bin101/ha-blueprints/main/blueprints/automation/lueften/lueften.yaml
```

## Validation / CI

On every push/PR touching `blueprints/**`, a GitHub Action
(`.github/workflows/validate.yml`) checks:
- `yamllint` (config in `.yamllint.yml`) against all blueprint files,
- that every `.yaml` file is valid YAML (including Home Assistant's
  `!input` tag) and has a `blueprint.domain` set.

Run locally:

```bash
pip install yamllint pyyaml
yamllint -c .yamllint.yml blueprints/
```

## License

[MIT](LICENSE)
