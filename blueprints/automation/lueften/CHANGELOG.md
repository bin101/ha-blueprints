# Changelog

All notable changes to this blueprint are documented here. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this blueprint follows [Semantic Versioning](https://semver.org/).

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
