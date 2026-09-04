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

## [2026-09-04] Kit contents: 5-pin XLR, 24 V supply, two USB DMX dongles

The modules terminate in 5-pin XLR. A 24 V supply came with the system, rating unread. Two USB dongles shipped: an HB-Laser USB-DMX-RDM and a MADRIX USB ONE. This may remove the need to buy any DMX interface, so the control path research ticket now covers both dongles and MADRIX as an option. Detail on GitHub issue #11.

## [2026-09-04] Sensing and control path research salvaged; C4001 ruled out

Both research tickets were resolved from sources recovered out of killed agents' transcripts, not from fresh fetching. Sensing shortlist: HLK-LD2450 radar, then VL53L5CX 8x8 ToF, then RealSense D435. The DFRobot C4001 Garrett already owns is ruled out because it reports distance and speed with no angle, so it cannot separate two walkers; the two-hill wave decision is what disqualifies it. Control path: ESP32 with esp_dmx into RS-485, unless an owned dongle proves OLA-drivable, in which case Raspberry Pi with OLA wins. QLC+, TouchDesigner and Enttec S-Play ruled out. Detail on GitHub issues #5 and #6.
