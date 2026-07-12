# CLAUDE.md

Guidance for working in this repo (`bin101/ha-blueprints`, public GitHub repo).

## What this repo is

A collection of custom Home Assistant **blueprints**, each importable
directly into a Home Assistant instance via a raw-GitHub-URL import link.
The repo is public specifically so `raw.githubusercontent.com` links work
in HA's "Open in Home Assistant" import flow.

## Repo structure convention

```
blueprints/
└─ <domain>/            # e.g. automation, script, template
   └─ <blueprint-name>/
      ├─ <blueprint-name>.yaml   # the blueprint itself
      └─ README.md               # detailed docs, import link, inputs
```

Every new blueprint gets its own subfolder with its own `.yaml` + its own
`README.md`, following this pattern. `source_url` inside the blueprint's
`blueprint:` metadata and the import links in both READMEs must point to
`https://github.com/bin101/ha-blueprints/...` / `https://raw.githubusercontent.com/bin101/ha-blueprints/main/...`.

## Documentation language: English only

**All** documentation must be in English — this includes not just the
`README.md` files, but also every user-facing string inside the blueprint
YAML itself: `blueprint.name`, `blueprint.description`, section `name`s,
input `name`s/`description`s, and default message texts (e.g.
`message_close`, `notify_title`). Inline YAML comments should be English
too. Do not leave German text in any committed file.

## Root README requirements

The root `README.md` is the entry point on GitHub and must, for every
blueprint:
- Have its own short description directly at root level (not buried
  inside a table cell — use a subsection per blueprint), and
- Include that blueprint's own "Open in Home Assistant" import badge/link
  right there, not only inside the blueprint's own `README.md`.

Each per-blueprint `README.md` also keeps its own import button (for
people who land there directly, e.g. via a link from elsewhere).

## Validating changes before committing

Run before every commit that touches `blueprints/**`:

```bash
yamllint -c .yamllint.yml blueprints/
```

This mirrors the `.github/workflows/validate.yml` CI job (yamllint +
a Python parse-check that registers a `!input` YAML constructor, since
plain YAML parsers don't know that Home Assistant tag). If `pyyaml`/
`yamllint` aren't installed, use an isolated venv rather than touching
system Python (`python3 -m venv /tmp/ha_lint_venv && /tmp/ha_lint_venv/bin/pip install pyyaml yamllint`).

## Git commits require GPG signing via a hardware token — do not use subshells

Global git config here has `commit.gpgsign=true`, and the signing key
lives on a hardware token (YubiKey/PIV/OpenPGP smartcard) that needs a
PIN/touch via `pinentry`. Running `git commit` wrapped in a subshell or
command substitution (e.g. `git commit -m "$(cat <<'EOF' ... EOF)"`)
breaks pinentry's ability to prompt and the command hangs until timeout.

**Always commit like this instead** (confirmed working):
```bash
# write the message to a file first (Write tool, not a heredoc in Bash)
git add <files>
git commit -F <path-to-message-file>
```

Never bypass signing with `--no-gpg-sign` unless the user explicitly asks
for it in that specific instance.

## Blueprint design conventions established in this repo

These came out of building the first blueprint (`lueften` — airing
reminder) and apply to future blueprints with similar needs:

- **Push notification targeting:** resolve the actual `device_id` from a
  `person` entity's `device_trackers` attribute (`state_attr(person,
  'device_trackers')` → `device_id(tracker_entity)`), then call
  `notify.send_message` with `target: {device_id: ...}`. **Do not** guess a
  `notify.mobile_app_<slugified_device_name>` service name — device
  display names don't reliably slugify to the real service/entity id and
  this breaks in practice.
- **Arbitrary number of push recipients:** use a single multi-select
  `person` entity selector rather than a fixed number of "slots". A person
  with multiple linked devices (phone + tablet, etc.) should receive the
  notification on all of them — loop over all `device_trackers`, dedupe
  resolved device ids with `unique`.
- **On-demand testing without extra helper entities:** give the
  TTS-sending and the push-sending steps their own named actions
  (`alias: Send TTS announcement` / `alias: Send push notification`) as
  siblings in the top-level `action:` sequence, gated by a single
  surrounding condition — not duplicated inside multiple `choose` branches.
  This lets a user test either step individually from the Home Assistant
  automation editor's built-in per-action **Run** button. Do **not**
  implement "test buttons" via `input_button` helper entities that the
  user has to create themselves — the built-in per-action Run button is
  the expected mechanism. Use a `trigger is defined` check (plus a
  dedicated `test_message` input) to distinguish a real automatic run from
  a manual per-action test run, and fall back sensibly (e.g. push ignores
  the "home" presence filter on a manual test run, so delivery can be
  verified while away).
- **Critical gotcha with per-action testing:** Home Assistant's per-action
  "Run" test (editor → action → ⋮ → Run) does **not** carry over
  `variables:` defined outside the action being run — only a top-level
  automation `variables:` block or an earlier sibling action's variables
  don't exist during that isolated test (see [Testing and troubleshooting
  automations](https://www.home-assistant.io/docs/automation/troubleshooting/)).
  We initially computed `message`/`notify_targets` etc. once in the
  top-level `variables:` block, and the push action silently sent to zero
  devices whenever tested via the per-action Run button (empty
  `for_each`, no error). The fix: give every individually-testable action
  its **own** `variables:` step as the first item of its own `sequence:`,
  re-declaring anything it needs via `!input` (duplication across actions
  is the acceptable trade-off here, not a mistake to "clean up"). Only put
  something in the shared top-level `variables:` block if it's *only*
  used by conditions/actions that are never meant to be run in isolation
  (e.g. the outer gate that decides whether to run at all).
- **"Once per period" without helpers:** use template triggers on genuine
  state transitions (e.g. outdoor temp crossing indoor temp ± hysteresis)
  combined with a `for:` debounce, instead of `input_boolean` helpers to
  track "already announced today". Each transition naturally fires only
  once per half-day.
