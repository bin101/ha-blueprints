# Changelog

All notable changes to this blueprint are documented here. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this blueprint follows [Semantic Versioning](https://semver.org/).

## [1.0.3] - 2026-07-16

### Fixed

- The wait loop now checks the current outdoor-vs-indoor temperature on its
  first pass instead of always starting by waiting for the "close"
  threshold. If it is already cooler outside than inside (open threshold
  met) when the loop starts — e.g. after a restart or fresh setup in the
  evening — it announces "open" straight away rather than waiting until the
  next morning's "close". Warmer/equal or mid-range starts are unchanged
  (normal close-first cycle), and alternation is still guaranteed.

## [1.0.2] - 2026-07-16

### Fixed

- Automation failed to set up in Home Assistant ("extra keys not allowed
  ... ['if'] / ['then']"): the 1.0.1 send steps illegally combined a
  `variables:` key with `if:`/`then:` in the same action step. Each send
  step is now a `sequence:` whose first item declares its own variables,
  with the gate and the send as separate sub-steps - valid, and still
  individually testable via the editor's per-action **Run** button.
- A freshly created (or reloaded) automation now starts its wait loop on
  its own: the old template triggers only fired on a threshold *crossing*,
  so an automation set up while the condition was already met (and with no
  Home Assistant restart) never started. Triggers are now `homeassistant
  start` plus a 10-minute `time_pattern` safety net; the loop itself does
  all the temperature detection and debouncing via `wait_template`.

## [1.0.1] - 2026-07-16

### Fixed

- The same reminder could be sent several times a day when the outdoor
  temperature flapped around a single threshold: each of the two
  independent template triggers re-armed on its own, so a brief dip below
  and back above the "close" threshold fired "close windows" again without
  an "open" ever happening in between. Announcements now run through a
  single self-sustaining wait loop that strictly alternates close -> open
  -> close, so the same side can never be announced twice in a row. After
  announcing "close" the loop blocks on the "open" threshold (and vice
  versa), and `mode: single` drops the redundant flapping triggers while it
  waits. Still no helper entities required, and all inputs are unchanged.

## [1.0.0] - 2026-07-12

### Added

- Temperature-based airing reminders: announces once in the morning when
  windows should be closed, and once in the evening when they should be
  opened, based on indoor vs. outdoor temperature (with configurable
  hysteresis and minimum hold duration).
- Optional TTS announcement on any number of media players, restricted to
  a configurable morning/evening time window.
- Optional push notification to any number of directly selected `notify`
  entities, sent only while the target's linked device reports `home` -
  not restricted by the time window, so it always goes out when the
  underlying condition is met.
- Optional window/door sensors to only announce "close" while a window is
  open, and "open" while one is closed.
- On-demand testing: the TTS and push steps are independent, named,
  individually-gated actions that can each be run directly from the
  automation editor's per-action **Run** button, with a dedicated test
  message and no extra helper entities required.
