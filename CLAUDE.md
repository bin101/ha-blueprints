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

## Versioning: per-blueprint SemVer, driven by Conventional Commits

Each blueprint is versioned **independently** (not the repo as a whole) —
they're imported and used independently, so a change to one blueprint
should not bump another's version. `lueften` started at **1.0.0** on
2026-07-12, covering the feature set at that point (temperature-based
reminders, TTS + push, optional window sensors, independent TTS/push
gating, per-action on-demand testing). Every new blueprint added to this
repo starts its own version at `1.0.0` the same way.

**Conventional Commits determine the version bump.** Every commit that
touches a blueprint's files must use a
[Conventional Commits](https://www.conventionalcommits.org/) type; scope
the commit to the blueprint when relevant (e.g. `fix(lueften): ...`):
- `fix:` → **patch** bump (1.0.0 → 1.0.1)
- `feat:` → **minor** bump (1.0.0 → 1.1.0)
- A `!` after the type/scope, or a `BREAKING CHANGE:` footer → **major**
  bump (1.0.0 → 2.0.0) — e.g. removing/renaming an input, or changing an
  input's meaning in a way that breaks existing configured automations.
- `docs:`, `chore:`, `refactor:`, `style:`, `test:`, `ci:` → **no version
  bump** on their own (only if bundled with an actual `feat`/`fix`/
  breaking change in the same unit of work).

**Where the version is surfaced** — update all of these together on every
version-worthy change:
1. The blueprint's own `blueprint.description` in its `.yaml`, as the
   first line: `**Version:** x.y.z - see [CHANGELOG](...)`. This is what
   Home Assistant renders in the blueprint's config/info card in the UI
   when a user views or sets up an automation from it — this satisfies
   "show the version in the Blueprint UI".
2. The blueprint's own `CHANGELOG.md` (next to its `.yaml`/`README.md`),
   following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
   format — add a new `## [x.y.z] - YYYY-MM-DD` section with
   Added/Changed/Fixed/Removed subheadings as appropriate.
3. The blueprint's own `README.md` — a `**Current version:** x.y.z
   ([CHANGELOG](CHANGELOG.md))` line near the top.
4. The root `README.md`'s per-blueprint section heading (e.g. `... — v1.0.0`).

**After committing a version-worthy change, tag it**: an annotated tag
named `<blueprint-name>-v<version>` (e.g. `lueften-v1.0.0`), not a bare
`v1.0.0`, since multiple blueprints share this repo and their versions
are independent. Push tags with `git push origin <tag-name>`.

There is currently **no CI enforcement** of Conventional Commits format or
automated version bumping/tagging — this is a manually-applied convention
(by whoever/whatever is committing, including Claude), not a bot-checked
one. If asked to add enforcement later (e.g. a commit-message lint step in
`.github/workflows/validate.yml`), that's a deliberate scope expansion,
not something to assume already exists.

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

- **Push notification targeting: let the user pick `notify` entities
  directly.** Use an entity selector with `domain: notify` (`multiple:
  true`) so the user picks real, already-registered notify entities (e.g.
  `notify.mobile_app_yourphone`) straight from a dropdown, then call
  `notify.send_message` with `target: {entity_id: ...}`. We went through
  two worse approaches before landing here — **do not repeat them**:
  1. Guessing a `notify.mobile_app_<slugified_device_name>` service name
     from a device's display name — device names don't reliably slugify to
     the real service/entity id.
  2. Deriving the target from a `person` entity's `device_trackers`
     attribute (`state_attr(person, 'device_trackers')` →
     `device_id(tracker)` → `target: {device_id: ...}`) — this produced no
     usable IDs at all in practice (device_tracker → device linkage isn't
     reliable enough to build on), and the user explicitly asked not to go
     through device_trackers at all.
  If you still want "only notify while present" semantics without asking
  the user to separately pick a person, derive presence the *other*
  direction as a secondary check: from the selected notify entity,
  `device_id(entity)` → `device_entities(device_id)` → look for a
  `device_tracker.*` entity among them → check `is_state(tracker, 'home')`.
  In `lueften`, the user explicitly wants this to be a strict allow-list:
  only send if a `device_tracker` is found **and** it reports `home` —
  no tracker (or not home) means skip. This was a deliberate reversal of
  our first instinct (default to sending when presence can't be
  determined) — don't "fix" it back without asking; see the
  `notify_targets` template in `lueften.yaml`'s "Send push notification"
  action for the reference implementation.
- **Arbitrary number of push recipients:** use a single multi-select
  entity selector (see above) rather than a fixed number of "slots".
- **Different gating per notification channel is normal — don't force a
  shared gate.** In `lueften`, TTS is time-window-restricted but push is
  explicitly NOT (the user wants push to always go out regardless of time
  of day, only the spoken announcement should respect quiet hours). Model
  this as two independent top-level `action:` items, each with its **own**
  `if:` gate — not one shared gate wrapping both. Don't assume every
  notification channel needs identical conditions; ask if unclear which
  conditions (time window, presence, etc.) should apply to which channel.
- **On-demand testing without extra helper entities:** give the
  TTS-sending and the push-sending steps their own named, independently
  gated top-level actions (`alias: Send TTS announcement` / `alias: Send
  push notification`) — not duplicated inside multiple `choose` branches.
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
