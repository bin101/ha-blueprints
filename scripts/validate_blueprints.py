#!/usr/bin/env python3
"""Validate Home Assistant automation blueprints against HA's own schemas.

Unlike the lightweight YAML parse-check (which only confirms the file is
parseable and has a `blueprint:`/`domain:` key), this uses the real Home
Assistant code to:

1. Validate the blueprint metadata with HA's automation BLUEPRINT schema.
2. Substitute auto-generated dummy input values (derived from each input's
   selector) and validate the resulting concrete automation - triggers,
   conditions and actions - against HA's own TRIGGER/CONDITION/SCRIPT
   schemas.

Step 2 is the layer that catches structural mistakes an offline YAML parser
cannot, e.g. an action step that illegally mixes `variables:` with
`if:`/`then:`.

Requires the `homeassistant` package (`pip install homeassistant`), which
pins a recent Python (<= 3.13 at time of writing).

Usage:
    python scripts/validate_blueprints.py blueprints/          # all *.yaml
    python scripts/validate_blueprints.py path/to/one.yaml     # a single file
"""
from __future__ import annotations

import asyncio
import glob
import os
import sys
from typing import Any

import voluptuous as vol

# Neutralize the deprecation-usage reporter, which otherwise raises
# "Frame helper not set up" when invoked outside a running HA instance.
# We only care about schema *structure* here, not deprecation warnings.
from homeassistant.helpers import frame as _frame

_frame.report_usage = lambda *a, **k: None  # type: ignore[assignment]

from homeassistant.components.automation import config as autoconfig
from homeassistant.components.blueprint import models
import homeassistant.helpers.config_validation as cv
from homeassistant.util.yaml import load_yaml_dict


def _dummy_for(name: str, definition: dict[str, Any]) -> Any:
    """Build a schema-valid dummy value from an input's selector."""
    selector = definition.get("selector") or {}
    default = definition.get("default")
    if not selector:
        return default if default not in (None, "") else "dummy"

    kind = next(iter(selector))
    opts = selector[kind] or {}

    if kind == "entity":
        domains = opts.get("domain")
        if isinstance(domains, list) and domains:
            domain = domains[0]
        elif isinstance(domains, str) and domains:
            domain = domains
        else:
            domain = "sensor"
        value = f"{domain}.dummy_{name}"
        return [value] if opts.get("multiple") else value
    if kind == "device":
        value = "0123456789abcdef0123456789abcdef"
        return [value] if opts.get("multiple") else value
    if kind == "area":
        value = "dummy_area"
        return [value] if opts.get("multiple") else value
    if kind == "number":
        if default is not None:
            return default
        return opts.get("min", 1)
    if kind == "boolean":
        return bool(default) if default is not None else False
    if kind == "time":
        return default or "12:00:00"
    if kind == "text":
        value = default or "dummy"
        return [value] if opts.get("multiple") else value
    if kind == "select":
        options = opts.get("options") or []
        if options:
            first = options[0]
            return first["value"] if isinstance(first, dict) else first
        return default or "dummy"
    if kind == "duration":
        return {"hours": 0, "minutes": 1, "seconds": 0}
    if kind == "target":
        return {"entity_id": ["sensor.dummy_target"]}
    return default if default not in (None, "") else "dummy"


def _get(cfg: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in cfg:
            return cfg[key]
    return None


def _validate_one(path: str) -> None:
    data = load_yaml_dict(path)

    bp = models.Blueprint(
        data,
        expected_domain="automation",
        schema=autoconfig.AUTOMATION_BLUEPRINT_SCHEMA,
    )

    inputs = {name: _dummy_for(name, definition) for name, definition in bp.inputs.items()}
    bi = models.BlueprintInputs(
        bp, {"use_blueprint": {"path": os.path.basename(path), "input": inputs}}
    )
    bi.validate()
    substituted = bi.async_substitute()  # sync despite the name

    actions = _get(substituted, "actions", "action")
    triggers = _get(substituted, "triggers", "trigger")
    conditions = _get(substituted, "conditions", "condition")

    async def _run_schemas() -> None:
        # The Template validator needs a `hass` registered in the running
        # loop's thread; constructing HomeAssistant registers it.
        from homeassistant.core import HomeAssistant

        HomeAssistant("/tmp/ha_validate_config")

        cv.SCRIPT_SCHEMA(actions)
        cv.TRIGGER_SCHEMA(triggers)
        if conditions:
            vol.Schema([cv.CONDITION_SCHEMA])(conditions)

    asyncio.run(_run_schemas())


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: validate_blueprints.py <blueprint.yaml | directory> ...")
        return 2

    paths: list[str] = []
    for arg in argv:
        if os.path.isdir(arg):
            paths.extend(sorted(glob.glob(os.path.join(arg, "**", "*.yaml"), recursive=True)))
        else:
            paths.append(arg)

    if not paths:
        print("No blueprint YAML files found.")
        return 1

    failed = False
    for path in paths:
        try:
            _validate_one(path)
            print(f"VALID  {path}")
        except vol.Invalid as exc:
            print(f"INVALID {path}: {exc}")
            failed = True
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR  {path}: {type(exc).__name__}: {exc}")
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
