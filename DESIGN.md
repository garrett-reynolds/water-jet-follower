---
name: water-jet-follower
description: Bench controls for a water and light strip that follows people. Read from across the room, stop from anywhere.
colors:
  ink: "#16353a"
  paper: "#edf5f3"
  panel: "#ffffff"
  water: "#087e8b"
  water-deep: "#06707c"
  light: "#d9fff5"
  danger: "#b9382f"
  danger-deep: "#9e2f27"
  line: "#b7cbc8"
  line-strong: "#789b9c"
  muted: "#587276"
  warn: "#fff3d6"
  warn-line: "#e6c77a"
  bad: "#ffe4df"
  bad-ink: "#7d211b"
  lock: "#fff6f4"
  lock-line: "#e9c2bd"
  status: "#dce9e6"
  hover-wash: "#f2f8f7"
  amber: "#f3b61f"
  map: "#092f35"
  map-grid: "#17474d"
  map-tool: "#123f45"
  map-tool-line: "#3e686c"
  map-ink: "#d7efeb"
  scope: "#111111"
  scope-ink: "#dddddd"
  scope-live: "#00ff66"
  scope-lost: "#ff4444"
  scope-dead: "#666666"
typography:
  display:
    fontFamily: "monospace"
    fontSize: "48px"
    fontWeight: 700
    lineHeight: 1.15
  headline:
    fontFamily: "\"Segoe UI\", Arial, sans-serif"
    fontSize: "22px"
    fontWeight: 650
  title:
    fontFamily: "\"Segoe UI\", Arial, sans-serif"
    fontSize: "17px"
    fontWeight: 650
  body:
    fontFamily: "\"Segoe UI\", Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.35
  label:
    fontFamily: "\"Segoe UI\", Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 400
  readout:
    fontFamily: "\"Segoe UI\", Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 650
  scope:
    fontFamily: "monospace"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.4
rounded:
  sm: "4px"
  md: "6px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "22px"
components:
  button:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "8px 11px"
    height: "40px"
  button-hover:
    backgroundColor: "{colors.hover-wash}"
  button-primary:
    backgroundColor: "{colors.water}"
    textColor: "{colors.panel}"
    rounded: "{rounded.sm}"
    padding: "8px 11px"
    height: "40px"
  button-primary-hover:
    backgroundColor: "{colors.water-deep}"
  button-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.panel}"
    rounded: "{rounded.sm}"
    padding: "8px 11px"
    height: "40px"
  button-danger-hover:
    backgroundColor: "{colors.danger-deep}"
  slider:
    textColor: "{colors.ink}"
    typography: "{typography.readout}"
    height: "44px"
  section:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "16px"
  header:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.panel}"
    padding: "12px 22px"
    height: "62px"
  nav-link:
    textColor: "{colors.light}"
    rounded: "{rounded.sm}"
    padding: "8px 12px"
  nav-link-hover:
    backgroundColor: "{colors.map-tool}"
  select:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "8px"
  status:
    backgroundColor: "{colors.status}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "10px"
    height: "40px"
  status-bad:
    backgroundColor: "{colors.bad}"
    textColor: "{colors.bad-ink}"
  warn-banner:
    backgroundColor: "{colors.warn}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "10px 12px"
  jet-chip:
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "9px 10px"
    height: "44px"
  jet-chip-checked:
    backgroundColor: "{colors.light}"
  scope-readout:
    backgroundColor: "#000000ee"
    textColor: "{colors.panel}"
    typography: "{typography.display}"
    padding: "10px 16px"
  scope-readout-stale:
    textColor: "{colors.scope-dead}"
---

# Design System: water-jet-follower

## Overview

**Creative North Star: "The Bench Instrument"**

This is a control panel on a bench next to real water and real 24 V hardware. The person using it is often standing, sometimes wet, sometimes across the room. The design does one job: make the state of the machine obvious and the stop reachable. Nothing is decorative. Every colour means something.

There are two surfaces and they are meant to look different. The **paper surfaces** (settings and test pages) are calm teal ink on pale mint paper, flat, bordered, with generous touch targets. The **scope surfaces** (the live viewer page and the map canvas inside settings) are dark instrument screens: deep teal or near-black, with bright signal colours for tracks and jets. Dark means "this shows what the sensor sees". Light means "this is what you can change".

**Key Characteristics:**
- Flat. One-pixel borders and tonal fills. No shadows anywhere.
- One accent (water teal) for action, one alarm (danger red) for stop, one amber for "look here" (focus, unapplied change, selected point).
- Touch first: every control is at least 40 px tall; sliders are 44 px.
- Big numbers are big on purpose. The readout is read from across the room.
- The stop button and the status line never scroll away.

## Colors

A muted teal family on pale mint paper, with a small set of loud signal colours reserved for state.

### Primary
- **Water** (`water`): the one action colour. Primary buttons, slider tracks, checkbox fill, text selection, the border on a checked jet chip.
- **Water Deep** (`water-deep`): primary button hover only.
- **Mint Light** (`light`): header nav link text, and the fill of a checked jet chip. The "on" wash.

### Alarm
- **Danger Red** (`danger`): the ALL OFF and Stop test buttons. Nothing else is this red.
- **Danger Deep** (`danger-deep`): danger button hover.
- **Bad Wash** (`bad`) on **Bad Ink** (`bad-ink`): a status box or mode box that reports a failure or "off".
- **Warn Wash** (`warn`) with **Warn Line** (`warn-line`): a banner for a state you must notice but that is not a fault (test mode on, hold-one-jet warning).
- **Lock Wash** (`lock`) with **Lock Line** (`lock-line`): the one safety-limit slider that needs an unlock. Paler than Bad; a caution, not a fault.

### Attention
- **Amber** (`amber`): the focus ring on every page, the outline on Apply when a change is pending, and the selected strip point on the settings map. It is the only colour shared by the paper and scope surfaces.

### Neutral (paper surfaces)
- **Ink** (`ink`): body text, headings, the header bar background, dark map tool bar.
- **Paper** (`paper`): page background and the sticky bottom bar.
- **Panel** (`panel`): section cards, buttons, selects, and the text on dark fills.
- **Muted** (`muted`): labels, notes, unit suffixes. Secondary text.
- **Line** (`line`): section borders, chip borders, select borders, the bar's top rule.
- **Line Strong** (`line-strong`): button borders and the scrollbar thumb. A shade darker so buttons read as pressable.
- **Status Wash** (`status`): the neutral status box fill.
- **Hover Wash** (`hover-wash`): plain button hover.

### Neutral (scope surfaces)
- **Map** (`map`): the settings map canvas and the colour wheel cursor ring.
- **Map Grid** (`map-grid`): half-metre grid lines on the map.
- **Map Tool** (`map-tool`) with **Map Tool Line** (`map-tool-line`) and **Map Ink** (`map-ink`): the zoom toolbar that floats on the map, and header nav link borders and hover.
- **Scope** (`scope`) with **Scope Ink** (`scope-ink`): the live viewer page and canvas background, and its default text.
- **Scope Live** (`scope-live`), **Scope Lost** (`scope-lost`), **Scope Dead** (`scope-dead`): a confirmed and seen track, a confirmed track the sensor lost, and a stale readout.

### Named Rules
**The One Red Rule.** Danger red is for the buttons that stop water. It never colours text, borders, or decoration.

**The Amber Means Look Rule.** Amber marks the thing that needs your eye next: focus, a pending Apply, a selected point. It is never a fill.

**The Dead Looks Dead Rule.** When the link to the Pi drops, the readout turns Scope Dead and the border turns Scope Lost, and the settings map wipes its scan and tracks and says so in the status box. On the test page a track the LiDAR did not see this scan renders in Muted with "(lost)". Stale numbers and stale dots must not pass for live ones.

## Typography

**Body Font:** Segoe UI (with Arial, sans-serif)
**Scope Font:** monospace (the system default)

**Character:** Plain and legible. The paper surfaces use the OS UI font at 15 px so they look like a native settings panel. The scope surfaces use monospace so numbers line up and feel like a terminal readout.

### Hierarchy
- **Display** (bold 700, 48px, 1.15): the live x / y / jet readout only. Drops to 32 px under 600 px wide.
- **Headline** (650, 22px): the page title in the header bar.
- **Title** (650, 17px): section headings.
- **Body** (400, 15px, 1.35): everything else on paper surfaces. Buttons and selects inherit it.
- **Readout** (650, 14px, tabular numerals): the slider value `<output>`. Its unit suffix is 13 px, weight 400, Muted. On the test page the readout grows to 20 px and the tracked-jet line to 22 px, because that page is read while standing on the strip.
- **Label** (400, 13px, Muted): slider names, notes, the live-state pill on the map.
- **Scope** (400, 13px, 1.4, monospace): the live viewer HUD and nav. Canvas labels are 10 px and 12 px monospace.

### Named Rules
**The Tabular Numbers Rule.** Any number that changes while you watch uses `font-variant-numeric: tabular-nums` so it does not jitter.

## Layout

Two column widths, one bar.

- **Settings page:** a two-column grid, map on the left (`minmax(360px, 1.35fr)`), controls on the right (`minmax(340px, 1fr)`), filling the viewport below a 62 px header. The map is sticky at full remaining height. Under 850 px it stacks: map on top at 38 vh, controls below. On a phone the page is for the sliders and the stop; the map is the laptop's job.
- **Test page:** one column, max 640 px, centred, 18 px padding, filling the viewport below the header so the bar sits at the bottom even when the page is short. Resume live show lives inside the yellow test-mode box at the top, never next to the stop.
- **Live viewer:** a full-bleed canvas with fixed overlays pinned to corners at 8 px (HUD top-left, readout top-right, nav bottom-right at 12 px). Under 600 px the HUD drops below the readout.
- **Inside sections:** a two-column control grid (`repeat(2, minmax(0, 1fr))`, gap 10 px by 14 px). Sliders span both columns. Jet chips use `auto-fill, minmax(96px, 1fr)` at 6 px gaps.
- **Rhythm:** 4 / 6 / 8 / 10 / 12 / 14 / 16 / 18 / 22 px. Section padding 16 px; sections stack at 14 px; controls stack at 18 px; header padding 12 px by 22 px.
- **The bar:** every paper page ends in a bar stuck to the bottom of its column: the status line on the left, the page's stop (ALL OFF or Stop test) bottom-right in Danger, and any page-level actions between them. On the settings page that is status, Lights only, Apply profile, ALL OFF, with the test-mode banner above; under 850 px the status takes its own row and the three buttons share one row. On the test page it is status and Stop test. It has a top rule in Line and the page's Paper fill so it reads as part of the page, not a toast.

### Named Rules
**The Stop Never Scrolls Rule.** On every page, the stop button (ALL OFF, Stop test) and the status line are always in the viewport. A stop you have to scroll to is not a stop, and a stop whose answer you cannot see is not verified.

## Elevation & Depth

No shadows. Depth is tonal and bordered. A section is Panel white on Paper with a 1 px Line border. A button is Panel white with a 1 px Line Strong border, one shade darker than a section, so it reads as pressable. Overlays on the dark surfaces use a translucent dark fill (`#08272ccc` on the map, `#000a` and `#000e` on the viewer) with a 1 px border so they sit on the canvas without floating above it.

### Named Rules
**The Flat Bench Rule.** Nothing casts a shadow. If a thing needs to stand out, it gets a border or a wash, not a lift.

## Shapes

Small, even corners. Buttons, selects, chips, inputs, status boxes, and banners are 4 px. Section cards are 6 px. The map toolbar is 5 px. Nothing is a pill and nothing is square. Borders are always 1 px except the live readout, which is 2 px so the state colour reads from a distance. The focus ring is a 3 px Amber outline with 2 px offset on every focusable thing on every page.

## Components

### Buttons
- **Shape:** 4 px corners, 1 px border, min-height 40 px (48 px on the test page).
- **Plain:** Panel fill, Ink text, Line Strong border. Hover: Hover Wash.
- **Primary:** Water fill and border, white text, weight 650. Hover: Water Deep. One per page (Apply profile, Start test).
- **Danger:** Danger fill and border, white text, weight 650. Hover: Danger Deep. Reserved for ALL OFF and Stop test.
- **Map tool:** Map Tool fill, Map Tool Line border, white text, min-width 38 px. Lives only on the dark map.
- **Focus:** 3 px Amber outline, 2 px offset.
- **Pending:** when a profile change is waiting, Apply gets the same Amber outline without focus.

### Slider (signature)
- **Style:** a label row (name left, value right) above a full-width native range. The row is Ink at 14 px; the value is 650 weight with a Muted 13 px unit suffix.
- **Track:** `accent-color` Water, 44 px tall, `touch-action: pan-y` so a thumb drag does not scroll the page.
- **Locked variant:** Lock Wash fill, Lock Line border, 10 px by 12 px padding, disabled until its unlock checkbox is ticked. The unlock is its own 40 px label row inside the wash, not part of the slider label. While the cap differs from what is live, Apply is Pending.

### Jet chips
- **Style:** a checkbox inside a bordered label, 44 px min-height, 4 px corners, Line border, Ink 14 px text.
- **Checked:** Mint Light fill, Water border.

### Sections
- **Corner:** 6 px. **Fill:** Panel. **Border:** 1 px Line. **Padding:** 16 px. Stack at 14 px. Title is 17 px, 650, with 12 px below.

### Status box
- **Style:** Status Wash fill, 4 px corners, 10 px padding, 40 px min-height, `aria-live="polite"`.
- **Bad:** Bad Wash fill, Bad Ink text.
- **Mode box (test page):** same shape, 650 weight. On = Warn Wash with Warn Line border. Off = Bad Wash with Bad Ink and a `#e9b8b0` border.

### Banners
- **Warn:** Warn Wash fill, Warn Line border, Ink text, 4 px corners, 10 px by 12 px padding. Can hold an inline plain button (Resume live show).

### Selects
- **Style:** white, 1 px Line border, 4 px corners, 8 px padding, inherits body type.

### Navigation
- **Header:** Ink bar, 62 px min-height, white 22 px title left, links right.
- **Links:** Mint Light text, Map Tool Line border, 4 px corners, 8 px by 12 px padding. Hover: Map Tool fill.
- **Viewer nav:** fixed bottom-right, links are `#126b72` fill with white text, 10 px by 14 px, 4 px corners.

### Map canvas (signature)
The settings map is a dark scope inside the light page. Map fill, Map Grid lines every 0.5 m. Background scan points are `#527277` at 1.3 px; foreground points `#45dce7` at 2.2 px. The strip is a 3 px `#54d6c1` line; jets are `#45dce7` dots with white numbers. The LiDAR origin is a `#fff06a` dot. Strip points are 12 px square outlines, `#e9fffa` at rest and Amber when selected. Tracks use the viewer's set: Scope Live when confirmed and seen, Scope Lost when confirmed but occluded, `#888` when tentative. Amber on the map means only "selected point".

### Live readout (signature)
The x / y / jet block on the viewer: `#000e` fill, white Display type, 2 px Scope Live border, 10 px by 16 px padding, pinned top-right. Stale: text Scope Dead, border Scope Lost, values shown as dashes.

## Do's and Don'ts

### Do:
- **Do** keep every control at 40 px tall or more, sliders at 44 px. Wet hands miss small targets.
- **Do** keep the page's stop button and the status box in a sticky bottom bar, on every page. Never let them scroll away.
- **Do** use Amber only for "look here": focus, pending Apply, selected point.
- **Do** put one primary button per page. Everything else is plain.
- **Do** use borders and washes for depth. No shadows.
- **Do** keep the live viewer and the map canvas dark. Dark means "what the sensor sees".
- **Do** show units next to a value, in Muted at 13 px, never inside the number.

### Don't:
- **Don't** use Danger red on anything that does not stop water.
- **Don't** add a third accent. Water is the accent. Amber is attention.
- **Don't** let a stale readout keep its last numbers. Grey it and show dashes.
- **Don't** make the live viewer light to match settings. The split is deliberate.
- **Don't** add a round or pill shape. Corners are 4 px or 6 px.
