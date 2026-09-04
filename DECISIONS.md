# Decisions

General mode: `## [YYYY-MM-DD] <title>` — what was decided or tried, the outcome, and why.

## [2026-09-04] Issue tracking on GitHub, default triage labels

Set up with `/setup-matt-pocock-skills`. Issues live in GitHub Issues for `garrett-reynolds/water-jet-follower` (private). Triage labels are the five defaults. Domain docs are single-context. Decision logging is General mode.

## [2026-09-04] Wayfinder map charted: spec for a following wave

Map is GitHub issue #1 ("Map: water-jet strip that follows people in a hallway") with nine child tickets. Destination is a build-ready spec, not a prototype. Follow behaviour is a wave, not a single jet. Scope is the control path only; water, pump, basin, and mains power are out. The strip sits in a raised basin and uses both jets and pixels. Hallway size is unknown and is a ticket.

## [2026-09-04] Hallway assumed 10 ft by 10 ft; parts check after technology choice

No hallway measurements will come, so the map assumes 10 ft long by 10 ft wide, people on both sides of the strip. Garrett will list owned parts only after the sensing method and control path are chosen, so the inventory ticket now follows those two choices instead of blocking them.

## [2026-09-04] Wave defined: 5-jet hill, colour by walker speed

Wave is a 5-jet hill that follows each walker, with one hill per walker, an attract roll when empty, and hold when a walker stops. Hill colour follows walker speed, slow blue to fast white, on a dim base. This adds two sensor rules: track two people at once, and give speed. Detail is on GitHub issue #7.
