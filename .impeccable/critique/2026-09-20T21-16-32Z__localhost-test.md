---
target: /test
total_score: 26
max_score: 40
na_heuristics: 
p0_count: 1
p1_count: 3
target_identity: "url:http://localhost:8090/test"
timestamp: 2026-09-20T21-16-32Z
slug: localhost-test
---
# Critique: /test (tracker/viewer.py TEST_PAGE, lines 419-474) — 2026-09-20

Method: dual-agent (A: design review · B: detector). Refinement scope only (#25). Reviewed against a dry-run replay of `crossing.jsonl` on the laptop (6-8 confirmed tracks), desktop 1280x900, phone 390x844 and 390x1600.

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|---|---|---|
| 1 | Visibility of System Status | 2 | No "jet held" state: after Start test the mode box still says "The live show is not sending" while water is up (viewer.py:461, 465). Lost tracks (`seen:false`) look the same as seen ones (468). At 390 px the status box scrolls off when you reach Stop test |
| 2 | Match System / Real World | 2 | `s=3.66 m` is code notation. The headline jet is clamped (geometry.py:137), so a person past the end reads "Jet 10" and one before the start reads "Jet 1". run.py:326 already refuses to print the clamped jet for this reason. "Nobody tracked" where CONTEXT.md says walker |
| 3 | User Control and Freedom | 2 | After Resume there is no way back into test mode except reload. Start test then fails with "open the test page first" while you are on the test page (settings.py:201) |
| 4 | Consistency and Standards | 3 | Stop test calls `/actions/all-off` (466), the same action ALL OFF calls on settings, under a different name. `#mode` loads in Bad wash with "Entering test mode." (435, 428). Nav links about 38 px (222-223). Detector: `20px` output (424) off the type ramp; `#e9b8b0` (428) near-duplicate of `lock-line` |
| 5 | Error Prevention | 3 | Bounds come from the live profile (470) and the server refuses bad jets. But `limits()` swallows failure, leaving `max="20"` (444) advertising uncalibrated jets 11-20 |
| 6 | Recognition Rather Than Recall | 3 | With 6 tracks the list reorders every 200 ms; duplicates ("Jet 2 · Jet 2") carry no id |
| 7 | Flexibility and Efficiency | 3 | One tap to start, one to stop. Moving a slider while holding does nothing until Start test again; nothing says so |
| 8 | Aesthetic and Minimalist Design | 3 | Mode box and status box say the same thing on load. `s=` values at 22 px bold compete with the jet number |
| 9 | Error Recovery | 3 | "Cut the 24 V." on every unverifiable zero is right. Raw server strings ("jet is outside the configured range") land in the status box unedited |
| 10 | Help and Documentation | 3 | The two notes are specific and true (439, 453). Nothing says a slider change needs Start test again, or what `s` is |
| **Total** | | **26/40** | **Fair; fix the P0 and the readout** |

## Design Specificity
Authored for this product in its chrome: "All 512 slots are zero", "Keep your hand on the 24 V switch", cm beside DMX, one primary button, the Warn/Bad mode box. But the page's reason to exist, "stand on a jet and read which jet the tracker says you are on", is served by a generic `join(' · ')` of `Jet N (s=x.xx m)` (viewer.py:468) that leads with the one number the project's own code says is wrong at the strip ends.

Detector: source scan 9 advisories, 2 in TEST_PAGE (viewer.py:424 `font-size:20px` off the ramp; :428 `#e9b8b0` outside DESIGN.md, a near-duplicate of `lock-line #e9c2bd`). Served-page scan: same two plus the known `design-system-font "ui"` false positive on the `font:` shorthand (216). URL-mode detect timed out because `poll()` never lets the network go idle (468). Browser overlay skipped: no interactive browser automation. Detector and review agree; the detector added nothing the review missed beyond the two token drifts.

## Overall impression
Calm, honest page. The safety copy is right. The two things it exists for, the stop and the "which jet am I on" readout, are the two weakest parts: the stop scrolls, and the readout leads with a clamped number.

## What's working
- One primary button (Start test) and one red button (Stop test), as DESIGN.md prescribes (viewer.py:448-449).
- Failure copy names the physical action every time: "Cut the 24 V." on enter, stop, and resume (464, 466, 467). `#seen` clears to "LiDAR not available." on a failed poll (468).
- Height defaults to `height_min`, sliders are clamped from the live profile (470), cm sits beside DMX in Muted small type (463).

## Priority Issues

- **[P0] Stop test and the status line scroll out of view on a phone.** No sticky bar on `/test`. At 390 px with 6 tracks, Stop test sits at y≈790-840 and Resume at y≈995; `#status` (y≈140-180) leaves the top when you scroll to either. `#seen` (430, 468) grows with the number of people, so a crowd pushes the stop further down. DESIGN.md:171 and PRODUCT.md principle 1 are page-agnostic, and `stop()` (466) calls the same `/actions/all-off` as ALL OFF. The rule applies; it was written for the settings bar and never carried here. **Fix:** add a `.bar` (`position:sticky; bottom:0; background:var(--paper); border-top:1px solid var(--line); display:flex; gap:8px`) holding `#status` (`flex:1 1 120px; min-width:0`) and `#stop`. Move Resume live show inline into `#mode` when `.on`, like the settings banner (345), and drop the Leave test mode section. Do not put Resume next to Stop test in the bar. Command: `/impeccable layout`.
- **[P1] The headline jet number is clamped and wrong at both ends of the strip.** geometry.py:137 clamps `jet` into `[0, jet_count-1]`; viewer.py:468 leads with it. Live capture: "Jet 1 (s=-0.17 m)" and "Jet 10 (s=3.66 m)" for people off the strip. The page cannot confirm the mapping with a number that reports a jet for anyone in the hallway. **Fix:** `jet_position` is already in `/state`. In `poll()`, if `jet_position < -0.5 || > jetCount-0.5` render "Past the end", else `'Jet '+(Math.round(p)+1)`. Command: `/impeccable clarify`.
- **[P1] No "jet held" state, and lost tracks look live.** After `start()` the only record is a status sentence (465); `#mode` (461) still reads "not sending" with water up. `poll()` filters `confirmed` only; `seen:false` tracks render the same as seen ones. **Fix:** on success set `#mode` to `.on` with "TEST MODE. Holding jet 7 at 30 (22.9 cm). Stop test to drop it."; clear on stop/resume. Render `seen:false` in Muted with "(lost)". Command: `/impeccable harden`.
- **[P1] Resume is a one-way door.** After `resume()` (467) Hold one jet stays enabled, Start test errors with "open the test page first" (settings.py:201), and there is no Enter test mode control. **Fix:** on `showMode(false)` disable `#start`, `#jet`, `#height` and swap the Resume slot for an "Enter test mode" plain button calling `enter()`. Keep Stop test enabled always. Command: `/impeccable harden`.
- **[P2] The tracked-jet readout is unstructured.** `#seen` (430) has no `tabular-nums` while updating every 200 ms; each entry breaks across lines at 390 px; order changes between polls; `s=` is not glossary language. **Fix:** one `<span class="track">` per track, `white-space:nowrap; display:inline-block; font-variant-numeric:tabular-nums`, jet number at 32 px, metres as a Muted 13 px suffix, sorted by `s`. Command: `/impeccable typeset`.

## Persona Red Flags
- **Wet on a phone next to the strip:** Stop test below the fold, further down the more people the LiDAR sees; the answer to Stop and Resume lands off-screen at the top; the jet list wraps to five lines and reorders under his eye.
- **Across the room on a laptop:** the jet number is 22 px, not Display size; a held jet is a 15 px status sentence; "LiDAR not available." is the same bold ink as live data.
- **Bench tuning a stuck jet:** sliding to a new jet or height does nothing until Start test again and nothing says so; the mode box says "not sending" while the jet is up; if `/settings-data` fails the slider silently offers jets 11-20 (444, 470).

## Minor
`#mode` loads as `.off` (Bad wash) with "Entering test mode." (435); Stop test and ALL OFF are one action with two names (466 vs 409); nav links about 38 px (222-223, shared); "Height (DMX)" puts the unit in the label; mode and status boxes duplicate on load; opening a second tab calls `enter()` and zeros a held jet silently (464); `#e9b8b0` (428) should be `lock-line`; slider output 20 px (424) is off the ramp and should be on it or documented.

Unverifiable in headless Chrome: real Safari viewport heights; 0-2 track rendering; the LiDAR-down path; the amber focus ring on the native range thumb.

## Questions
- If Stop test and ALL OFF are the same endpoint, why do they have different names, and why does only one get a sticky bar?
- The console already refuses to print the clamped jet (run.py:326). Why does the page built to check jet numbers lead with it?
- When Garrett taps Resume while standing on jet 3, the hill rises under him. Should the page say so before the tap?
