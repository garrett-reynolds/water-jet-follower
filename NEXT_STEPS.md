# Next steps

Last updated 2026-09-04.

## Where the plan actually lives

**GitHub issue #1** is the map and the canonical plan: `gh issue view 1`. This file is a
pointer and a cold-start summary, not a second source of truth. Decisions live in
`DECISIONS.md` and in each ticket's resolution comment. Do not restate them here.

## State

Every decision that can be made in a conversation has been made. **10 of 13 tickets closed.**
The design is settled and every part is owned.

| | |
|---|---|
| Sensor | Slamtec RPLIDAR A2M8, one unit, Boost mode, motor PWM 800 |
| Controller | Raspberry Pi 5, Raspberry Pi OS Lite 64-bit (Debian 13 Trixie), headless |
| DMX out | Enttec DMX USB Pro Mk2 via OLA's `usbserial` plugin, universe 1 |
| Software | Plain Python in `~/wj-venv`, not ROS |
| Power | Pi's own supply plus a **powered USB hub** for the LiDAR — not optional, see `DECISIONS.md` |
| Cost to finish | CAD $0 |

Reach the Pi with `ssh pi@water-jets.local` (key-based, no password). OLA's web UI is at
`http://water-jets.local:9090`.

## Open tickets

- **#12 — Prototype: does one RPLIDAR A2 survive two walkers crossing?** Open and unblocked.
  Carries a nine-item bench checklist; items 1, 2 and 4 are done.
- **#10 — Write the build-ready spec.** Blocked by #12.

## Do next, in order

1. **Write the tracker.** Needs no hardware from Garrett and is the largest remaining piece.
   Read the A2M8 over `/dev/ttyLIDAR` in Boost mode, cluster the scan points, pair clusters into
   legs, follow the pairs by nearest neighbour, and derive speed by differentiating position.
   Use `angusleigh/leg_tracker` as a reference for the algorithm and its parameters, **not** as a
   dependency — it targets ROS 1 Noetic, which reached end of life in May 2025.
2. **Write a web scan viewer.** Choosing Lite means there is no local plotting window, so the
   scan has to be served from the Pi and opened on a laptop. Nothing in #12 items 5-7 can be
   judged by eye without it.
3. **Connect the water modules** and complete #12 item 3: set module 1 channel 5 and watch jet 1
   move. This is the only untested link in the whole chain.
4. **Then #12 items 5-7**, and #10 unblocks.

## Known unknowns

- **Jet rise time.** How long from the DMX height channel changing to the water reaching full
  height. Never measured, absent from the module datasheet. It may be slower than the sensor,
  in which case it, not the LiDAR, sets how closely the wave can follow — and it retroactively
  justifies or overturns the motor PWM 800 choice.
- **Whether the water columns appear as targets in the LiDAR scan.** Garrett owns the physical
  protection and mounting and ruled this out as a selection criterion. It remains open for the
  tracker's filtering.
- **Whether one A2M8 covers two crossing walkers**, or a second unit is needed. This is what
  #12 exists to answer.
- **Whether the modules answer standard E1.20 RDM.** The Enttec does RDM, so commissioning may
  need neither the HB-Laser dongle nor a Windows machine. Untested.

## Traps that already cost time

- **`pyrplidar` does not drain its serial buffer on `stop()`.** It throws
  `PyRPlidarProtocolError: sync bytes are mismatched` on reconnect. Production code needs
  connect-retry and an explicit flush, or the installation will fail to start at random.
- **Stale `/var/lock/LCK..ttyUSB*` files silently stop OLA opening the port.** Clear them at
  boot. See `DECISIONS.md`.
- **Boost mode is mandatory.** Standard mode is 2,000 samples/s, giving 2.6 degrees and about
  137 mm of error at 3 m — nearly three jet pitches.

## Missing from this repo

There is no `README.md`. Global CLAUDE.md requires it be produced with the `create-readme`
skill rather than hand-written. Worth doing once the tracker exists and there is something to
describe running.
