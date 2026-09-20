# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

One user: Garrett, the builder. He opens the three pages from a laptop or a phone, on the same
network as the Pi. He is often standing next to the strip, sometimes wet, sometimes across the
room reading the big readout. Nobody else opens the pages. Site staff at the client venue do not
use them; the only control they get is the physical 24 V switch.

The people the strip reacts to are visitors walking past in a hallway. They never see the pages.

## Product Purpose

A strip of twenty water jets and twenty RGBW pixels that follows people along a hallway. One
LiDAR finds walkers by their legs; a hill of water rises under each one and moves with them.
The web pages exist so Garrett can see what the sensor sees, shape the water and light, test one
jet at a time, and stop everything from wherever he is standing.

Success for the pages: the state of the machine is obvious at a glance, a change lands live
while he watches the water, and the stop is always one tap away.

## Positioning

Not a product for sale. A one-off installation by Garrett for a client venue. The pages are the
bench instrument for that installation: plain Python, standard library only, served from the Pi
with no build step, no framework, and no dependency that can break on a headless Pi.

## Operating Context

- **Hardware:** Raspberry Pi 5 (headless, Raspberry Pi OS Lite), Slamtec RPLIDAR A2M8, Enttec
  DMX USB Pro Mk2, two HB-Laser 3D HydroMatrix HD modules on 24 V DC. See `README.md`.
- **Pages:** three, all served by `tracker/viewer.py` on `http://water-jets:8080/`:
  `/` live viewer, `/settings`, `/test`. Reached over SSH-adjacent LAN from a laptop or phone.
- **Final home:** a public hallway at a client venue. The pages run on the site network. The
  venue is confirmed; its name and network details are not recorded here.
- **Safety:** the modules latch their last value when DMX stops. Software stops work only
  while the chain is alive. The physical 24 V switch is the only real stop. A hardware watchdog
  contactor is specified in `docs/BUILD_SPEC.md` and not yet built. The system is not for
  unattended use until it is.
- **Rituals:** settings edits go live as they are made; the hard maximum height, Load JSON, and
  Reset defaults wait for Apply profile. Test mode holds one jet with the live show paused.
  First power-up of any actuator starts at the lowest value.

## Capabilities and Constraints

- Follow, hold, two walkers, colour by speed, and idle animations, as listed in `README.md`.
- Profiles are versioned JSON with validation and an undo stack (`tracker/settings.py`).
- Jets 0 to 9 are calibrated and verified with light and water. Jets 10 to 19 are not. The
  second module is not connected; do not propose connecting it unless Garrett changes that
  decision (`NEXT_STEPS.md`).
- Height is 7.62 mm per DMX unit, measured. The cap is DMX 40, which is 30 cm.
- Standard library only. No npm, no bundler, no CDN fonts. The pages must work when the Pi has
  no internet.
- Terminology is fixed in `CONTEXT.md` (jet, pixel, strip, walker, wave, hill, attract, hold,
  track, scan plane, shadow). Use those words in UI copy.

## Brand Commitments

None. There is no logo, no client mark on the pages, and no house style to match. The pages are
an internal tool.

## Evidence on Hand

- `README.md`, `docs/BUILD_SPEC.md`, `DECISIONS.md`, `NEXT_STEPS.md`, `tracker/README.md`:
  the full record of what works, what is measured, and what is decided.
- `docs/water-jet-follower.png` and `.html`: the signal chain diagram (archify output, not UI).
- Recorded LiDAR clips in `data/` for dry-run replay on the laptop.
- No screenshots of the pages are committed. No testimonials, customers, or press exist and
  none should be invented.

## Product Principles

1. **The stop wins.** Any layout that moves ALL OFF or the status line out of view is wrong.
2. **Live state must look live.** A dropped link greys the readout. Stale numbers never pass
   for real ones.
3. **Read from the strip.** The user is standing, wet, or across the room. Big numbers,
   big targets, no precision gestures.
4. **Edits land while you watch.** The loop is slider, water, eyes. Anything that adds a step
   between a change and the water needs a safety reason.
5. **Nothing the Pi cannot serve.** No dependency the headless Pi cannot host on its own.

## Accessibility & Inclusion

No product-specific requirement was established. The one user has no stated needs. Keep the
existing floor: 40 px controls, 44 px sliders, a visible focus ring, and `aria-live` status.
