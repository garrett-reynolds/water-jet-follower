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
| Sensor | Slamtec RPLIDAR A2M8, one unit, Boost mode, motor PWM 800 (**see the correction below**) |
| Controller | Raspberry Pi 5, Raspberry Pi OS Lite 64-bit (Debian 13 Trixie), headless |
| DMX out | Enttec DMX USB Pro Mk2 via OLA's `usbserial` plugin, universe 1 |
| Software | Plain Python in `~/wj-venv`, not ROS. Tracker and viewer written, see `tracker/README.md` |
| Power | Pi's own supply plus a **powered USB hub** for the LiDAR — not optional, see `DECISIONS.md` |
| Cost to finish | CAD $0 |

Reach the Pi with `ssh pi@water-jets.local` (key-based, no password). OLA's web UI is at
`http://water-jets.local:9090`. The scan viewer is at `http://water-jets.local:8080/` while
`tracker.run live` is running.

## Open tickets

- **#12 — Prototype: does one RPLIDAR A2 survive two walkers crossing?** **Items 1, 2, 4, 5
  and 6 done; 7 half done.** One unit is enough, a standing person is held 99% of the time,
  and position jitter is 7-13 mm against a 50 mm jet pitch. **Only item 3 is outstanding**, and
  it needs the water modules connected.
- **#10 — Write the build-ready spec.** Blocked by #12.

## Done since the last update

1. ~~Write the tracker.~~ Done. `tracker/` — LiDAR driver, background subtraction, clustering,
   leg pairing, constant-velocity Kalman tracking, record and replay. 16 unit tests pass on the
   laptop and the Pi.
2. ~~Write a web scan viewer.~~ Done. `tracker.run live` serves it on port 8080.
3. **Two walkers out of one walker.** `tracker.run merge` combines two one-person clips into
   the scan two people would have made, by keeping the nearer return on every ray. This is how
   #12 item 5 gets answered without a second person.
4. **USB hub swap checked.** The udev names held and the over-current fault stopped at the
   swap. See `DECISIONS.md`.
5. **The baseline no longer needs an empty room.** It takes a low percentile of each bearing's
   returns instead of the nearest, so a person walking about while it records does not become
   part of the room. See `DECISIONS.md`.

Verified on hardware 2026-09-04: `live` runs at 16.18 Hz against the real A2M8. Two 20-second
clips of the same still bench, baseline built from the first and the tracker run on the
second: **2 false people without the baseline, 0 with it**. And on a 60-second clip of the
real room, **one real person was held as a single track in 78% of scans**, longest hold 17.1 s
over 4.81 m. **Two people crossing is still unverified** — that needs clips 2 and 3 merged.

## Do next, in order

1. **Record the remaining clips, alone.** Garrett has no second person, and does not need
   one. All the commands are in `tracker/README.md`.
   1. ~~The room, 60 s, with him walking about in it.~~ **Done 2026-09-04.**
      `~/data/room.jsonl`, 924 scans, baseline at `~/data/baseline.json` and
      `data/room-baseline.json` in this repo. 360/360 bins filled, 16.2 moving points per
      scan, and it held him as a single track 78% of the time. See `DECISIONS.md`.
   2. ~~Walk left to right, 30 s.~~ **Done.** `~/data/walk-left-right.jsonl`, 433 scans.
   3. ~~Walk right to left, 30 s.~~ **Done.** `~/data/walk-right-left.jsonl`, 432 scans.
      Merged into `~/data/crossing.jsonl`, which **answered #12 item 5**.
   4. ~~Stand still at three spots on the line.~~ **Done.** `~/data/standing.jsonl`, 596
      scans. **Answered #12 item 6 and the precision half of item 7.**

   Check any baseline by replaying its own clip through `tracker.run offline` and reading
   `moving points per scan`: over 10 is good, under 3 means the walker was absorbed.

   Clips 2 and 3 then merge into a two-person crossing with `tracker.run merge`, and
   `--shift-b` slides where they cross. One pair of recordings gives the whole occlusion
   sweep. See the merge entry in `DECISIONS.md` for why this is faithful and not a fudge.
2. **Measure absolute accuracy.** Tape the real distance between the three standing spots and
   from the sensor to one of them, and compare against `DECISIONS.md`. Precision is already
   measured at 7-13 mm; only the absolute offset is open, and the A2's mirror is not at the
   centre of its case.
3. **Decide the motor PWM.** PWM 800 measures 16.25 Hz, which is outside the A2M8's rated
   5-15 Hz band; PWM 760 gives 15.09 Hz. See the correction entry in `DECISIONS.md`.
4. **Connect the water modules** and complete #12 item 3: set module 1 channel 5 and watch jet 1
   move. This is the only untested link in the whole chain.

   **Start low, and have three ways to stop it.** Garrett's rule, 2026-09-04. Channel 5 is
   0-255 against a 5 cm to 1.5 m throw, and the mapping is RDM-calibrated and unread, so open
   at about 5-10 and step up. Three kill layers, because the first two are unproven: (a) the
   test tool traps SIGINT and `atexit` and sends an all-zero frame before exit; (b) a second
   terminal holds a ready zero command, verified to clear all 50 channels rather than assumed
   to; (c) a physical switch on the 24 V supply's mains lead, in arm's reach. Layers (a) and
   (b) both assume `olad` stops holding the last frame and that the modules do not latch on
   signal loss — **test that on purpose**: command a low value, kill the client, watch whether
   the jet drops or holds.

   **The tool is written and the stop path is proven.** `tracker.run jog --channel N` and
   `tracker.run zero`, in `tracker/dmx.py`. Verified on the Pi 2026-09-04: `zero` reports
   `slots_held=512 ALL ZERO`, and a `jog` holding channel 512 at 10 went back to all-zero
   after a `SIGHUP`. Channel 512 was used so nothing on the modules could move. The bench
   order — RDM discover, then prove the stop on nozzle 1's **red LED** (channel 1), then the
   pump (channel 5) — is in `tracker/README.md`. **Nothing non-zero has been sent to a
   module.** The `~/wj-venv` `include-system-site-packages` trap is fixed; it is now `true`
   and the venv imports both `ola` and `pyrplidar`.

   The test basin is 24 in x 16 in with 9 cm of water, which clears the 8 cm minimum by 1 cm —
   roughly 2 L of splash margin before the pumps are below their rated level. The module
   drawing shows a "Water level sensor M3" on board; whether it cuts the pumps when dry is
   **unverified** and worth checking, because it would settle the margin question.
5. **Write the wave and the DMX output.** Blocked on nothing but ordering. ~~`~/wj-venv` was
   made with `include-system-site-packages = false`, so `import ola` fails inside it.~~
   **Fixed 2026-09-04**: the flag is `true`, the old file is kept at `~/wj-venv/pyvenv.cfg.bak`,
   and the venv imports `ola` and `pyrplidar`. `tracker/dmx.py` already has the send, fetch and
   zero primitives the wave needs.

Once step 4 lands, #12 closes and #10 unblocks.

## Known unknowns

- **Jet rise time.** How long from the DMX height channel changing to the water reaching full
  height. Never measured, absent from the module datasheet. It may be slower than the sensor,
  in which case it, not the LiDAR, sets how closely the wave can follow — and it retroactively
  justifies or overturns the motor PWM 800 choice.
- **Whether the water columns appear as targets in the LiDAR scan.** Garrett owns the physical
  protection and mounting and ruled this out as a selection criterion. It remains open for the
  tracker's filtering.
- ~~Whether one A2M8 covers two crossing walkers.~~ **Answered 2026-09-04: one is enough.**
  Two solo walks merged by nearest-return held both tracks through five different crossings,
  ids intact, closest pass 0.05 m at under 1 m from the sensor.
- **How the baseline stays fresh in an unattended hallway.** A baseline captured at boot goes
  stale the moment anything moves, and each stale object becomes a permanent person. Wants a
  rolling baseline. Not built.
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
- **A baseline goes stale the moment the room changes**, and every changed object becomes a
  permanent person. Build each clip's baseline from that clip — except standing clips, which
  must use a walking clip's baseline. See `DECISIONS.md`.
- **The Pi still has the default `raspberry` password**, and its own login banner says so. It
  needs changing at the same time as SSH moves to key-only, before this goes in a wall.

## Missing from this repo

There is no `README.md`. Global CLAUDE.md requires it be produced with the `create-readme`
skill rather than hand-written. Worth doing once the tracker exists and there is something to
describe running.
