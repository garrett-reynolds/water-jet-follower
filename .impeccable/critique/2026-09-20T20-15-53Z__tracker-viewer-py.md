---
target: /settings
total_score: 29
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 4
target_identity: "file:C:\\Users\\garrett.reynolds\\Projects\\Personal\\Electronics\\water-jet-follower\\tracker\\viewer.py"
target_fingerprint: "sha256:9216c9fed5f39024d4c7d68d5d0d91730ba750c498c0f919ab9975b1b09667fa"
target_path: "C:\\Users\\garrett.reynolds\\Projects\\Personal\\Electronics\\water-jet-follower\\tracker\\viewer.py"
timestamp: 2026-09-20T20-15-53Z
slug: tracker-viewer-py
---
# Critique: /settings (tracker/viewer.py) — 2026-09-20

Method: dual-agent (A: design review · B: detector). Refinement scope only (#25).

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|---|---|---|
| 1 | Visibility of System Status | 2 | Map keeps painting stale tracks after the link drops; status box says "Edits apply as you make them." while test mode says nothing is sent; changed hard maximum gets no Amber on Apply |
| 2 | Match System / Real World | 3 | cm beside DMX, jets numbered as on the strip. "Idle" where CONTEXT.md says attract, "person" for walker |
| 3 | User Control and Freedom | 3 | Undo/Reset/Load are previewed; Undo steps back one 250 ms auto-apply burst (settings.py:140), not one edit |
| 4 | Consistency and Standards | 2 | Viewer HUD numbers jets from 0, settings map and test page from 1; bar wraps to two rows against DESIGN.md "one row" |
| 5 | Error Prevention | 4 | Lock on hard max, coupled slider ranges, ALL OFF forces test mode, Remove point guarded |
| 6 | Recognition Rather Than Recall | 3 | Only the current one of four colours is visible |
| 7 | Flexibility and Efficiency | 2 | 0.01 s steps on lead time and follow response on a 16 px native thumb: precision gestures for wet hands |
| 8 | Aesthetic and Minimalist Design | 3 | Solid on desktop; on phone overlays cover jets 10 and 1, header wraps to 84 px |
| 9 | Error Recovery | 4 | Every failure names the next physical action ("Cut the 24 V.") |
| 10 | Help and Documentation | 3 | Profile note is right; nothing explains Lights only or Follow response |
| **Total** | | **29/40** | **Good; fix the four P1s** |

## Design Specificity
Authored for this product. The paper/scope split, the jet-numbered strip on the map, the cm-per-DMX readouts, the single Lock Wash control, and "All 512 slots are zero" could not ship on another product. Native ranges/selects/wheel are deliberate stdlib choices.

Detector: source scan 9 advisory findings, 2 on this page (viewer.py:262 `.map-view` radius 5 px off the 4/6 scale; :263 `#47777b` border undocumented). Served-page scan: 3 findings, 1 warning `design-system-font "ui"` which is a tokeniser false positive on the `font:` shorthand (proved by longhand control). Browser overlay skipped: no interactive browser automation.

## Priority Issues
- [P1] Unlock target is 20 px. `<label class="slider lock">` (viewer.py:305-306) wraps output, range, and the checkbox; the label binds to `<output>`, so tapping "Unlock this safety limit" does nothing. Fix: own `<label for="unlock">` row, min-height 40 px.
- [P1] Changed hard maximum gives no Amber on Apply. `pending` only set by Load/Reset; `autoApply` (378) strips height_max silently. Fix: toggle `.bar.pending` when `height_max` differs from `original`; clear in `apply()`.
- [P1] Map does not look dead on link drop. `pollState` catch (382) sets the pill only; never clears `liveFrame` or redraws. Fix: `liveFrame=null; draw();` and mirror the text in the status box.
- [P1] Phone letterbox. `.map { height:52vh }` (287) + two-row sticky bar leaves ~200 px (≈100 px with the test banner) for a ~2,800 px controls column. Fix: 38vh and the bar fix below.
- [P2] Bar wraps and moves ALL OFF. `.bar .status { flex:1 1 220px }` (283) wraps even at 1280 px. Fix: `flex:1 1 120px; min-width:0` on status; on phone give status its own row so the three buttons share one row, ALL OFF bottom-right.

Out of scope (behaviour): Undo granularity; 0-based jets on the viewer page.

## Persona Red Flags
- Wet, phone, next to the strip: 20 px unlock; one or two sliders visible; header wraps; map overlays cover jets 10 and 1.
- Across the room, laptop: only section titles readable; link health is a 13 px pill on the dark map; canvas keeps green walkers after a drop.
- Bench, tuning: 0.01 s steps; clamps set only in `fill()` (366) so a slider can refuse to travel with no message; no Amber cue after moving the hard max.

## Minor
Header 84 px at 390 px (spec 62); test-mode status text on load; Lights only not annotated in test mode; "Reverse jet order" label Muted 13 px vs 14 px Ink sliders; colour level sliders squeezed to ~280 px beside the wheel; swatch has no visible label; canvas point selection has no keyboard path; terminology drift (Idle/attract, person/walker).

Unverifiable in one-shot headless: bar stays put while scrolling; jet chip toggle.

## Questions
- Why is the one control that can raise water above the cap the smallest target and the only one with no Amber?
- On a phone, is the map worth half the screen, or is the phone for sliders and the stop?
- Should "LiDAR not available" ever live only in a 13 px pill on the dark surface?
