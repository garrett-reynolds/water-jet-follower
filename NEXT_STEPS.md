# Next steps

Last updated 2026-09-19.

## Where the plan actually lives

**GitHub issue #1** is the map and the canonical plan: `gh issue view 1`. This file is a
pointer and a cold-start summary, not a second source of truth. Decisions live in
`DECISIONS.md` and in each ticket's resolution comment. Do not restate them here.

## State

Every decision that can be made in a conversation has been made. **11 of 13 tickets closed.**
The design is settled, every part is owned, and **the whole chain has now run end to end with
water in the air.** The first ten jets are calibrated and verified with both lights and water.
The final build uses all 20 jets. Jets 10 through 19 still need calibration and verification.

| | |
|---|---|
| Sensor | Slamtec RPLIDAR A2M8, one unit, Boost mode, motor PWM 800 (**see the correction below**) |
| Controller | Raspberry Pi 5, Raspberry Pi OS Lite 64-bit (Debian 13 Trixie), headless |
| DMX out | Enttec DMX USB Pro Mk2 via OLA's `usbserial` plugin, universe 1 |
| Software | Plain Python in `~/wj-venv`, not ROS. Tracker, viewer, DMX and wave all written, see `tracker/README.md` |
| The show | `tracker.run show` — hills follow walkers, colour by speed. `--dry-run`, `--lights-only`, or real |
| Height | **7.62 mm per DMX unit**, measured. Cap is DMX 40 = 30 cm. DMX 255 would be 1.94 m |
| Stopping | Software zero works **only while the chain is alive**. The modules latch. The 24 V switch is the only real stop |
| Power | Pi's own supply plus a **powered USB hub** for the LiDAR — not optional, see `DECISIONS.md` |
| Cost to finish | CAD $0 |

Reach the Pi with `ssh pi@water-jets` (key-based, no password). OLA's web UI is at
`http://water-jets:9090`. The scan viewer is at `http://water-jets:8080/` while
`tracker.run live` is running.

## Open tickets

- **#10 — Write the build-ready spec.** Garrett approved `docs/BUILD_SPEC.md` on 2026-09-19.
  The final build uses all 20 jets. The first ten are verified. The last ten still need
  calibration.

**#12 was closed on 2026-09-05, with no closing comment.** Items 1-6 were done and item 7 half
done: one unit is enough, a standing person is held 99% of the time, and position jitter is
7-13 mm against a 50 mm jet pitch. Item 3 closed on 2026-09-04 when DMX value 5 on channel 5 made
jet 1 spray — but **that result was never written into the ticket**, so #12's last checklist
still reads *"blocked: modules not connected"*. Item 7's absolute accuracy was never measured; it
is step 3 below.

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

1. ~~**Calibrate where the strip actually is.**~~ **Done 2026-09-19.**

   Garrett measured one LiDAR x/y target point for each of jets 0 through 9. The tracker uses
   a joined path through all ten points and interpolates between adjacent jets. The mapping is
   in `Config.strip_points` and is covered by unit tests. Garrett verified the live viewer map,
   light aim, and water aim for jets 0 through 9 on 2026-09-19. The live show used a peak of
   DMX 30. It stopped cleanly and read back all 512 DMX slots at zero. The final build uses all
   20 jets. Jets 10 through 19 still need measured points and the same bench check.

   <details><summary>Old straight-line calibration notes</summary>

   The software works. It is pointed at the wrong place. `config.py` says jet 0 sits at
   **(0.10, 0.00)** and jet 19 at **(1.05, 0.00)** — a line straight out in front of the LiDAR,
   starting 10 cm away. Standing at jet 0 on the real bench reads about **(0.3, 0.8)**. So the
   strip is roughly 30 cm out and **80 cm off to one side** of where the software thinks it is.
   Every hill lands in the wrong place until this is fixed, and the tracker is not at fault.

   **The jet 9 reading was never taken.** One number is not enough — two points are needed to
   place a line, and the angle matters as much as the offset.

   To finish it: run `show --lights-only`, open `http://water-jets.local:8080/`, stand at jet 0
   and then at jet 9, and read the x/y off the viewer at each. Then write both into a config
   file and pass it with `--config`:

   ```
   ~/wj-venv/bin/python -m tracker.run --config ~/strip.json show --baseline ~/data/baseline.json --lights-only
   ```

   `Config.save()` writes the whole dataclass as JSON, so the quickest route is to dump a
   default, edit `strip_start` and `strip_end`, and keep it on the Pi.

   **Current scope:** use only the first module and jets 0 through 9. The second module stays
   unused. `config.py` defaults to a 1 x 10 line with 50 mm pitch.

   </details>

2. ~~**Record the remaining clips, alone.**~~ **Done.** Garrett has no second person, and does not need
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
3. **Measure absolute accuracy.** Tape the real distance between the three standing spots and
   from the sensor to one of them, and compare against `DECISIONS.md`. Precision is already
   measured at 7-13 mm; only the absolute offset is open, and the A2's mirror is not at the
   centre of its case.
4. **Decide the motor PWM.** PWM 800 measures 16.25 Hz, which is outside the A2M8's rated
   5-15 Hz band; PWM 760 gives 15.09 Hz. See the correction entry in `DECISIONS.md`.
5. ~~**Connect the water modules**~~ **Done.** #12 item 3: set module 1 channel 5 and watch jet 1
   move. ~~This is the only untested link in the whole chain.~~

   **The DMX path is proven end to end, 2026-09-04.** `tracker.run jog --channel 1 --max 40`
   lit **nozzle 1's red LED**, confirmed by Garrett at the bench. That settles four things at
   once: the Pi to Enttec to cable to module chain carries DMX; **module 1 is at DMX address
   1**, so no readdressing is needed; the datasheet's channel map is right, with channel 1 as
   red; and `olad` held `slots: 512 nonzero: [(1, 40)]` while it was lit, so the full-frame
   send works against a real fixture. **#12 item 3 is closed.** `jog --channel 5` at DMX value **5** produced *"a very little
   spray"* from jet 1, confirmed by Garrett at the bench 2026-09-04. The Pi now drives water.
   Every link in the chain - LiDAR, tracker, Pi, OLA, Enttec, DMX, module, pump - has been
   exercised on real hardware. The DMX-value-to-height mapping is being measured; see below.

   **Stop layer (a) is proven on real hardware.** Garrett killed the jog process with the LED
   lit and the LED went out. So the tool's zero-on-exit reaches a real fixture, not just
   `olad`. Layer (b), `tracker.run zero`, is the same code path and the same frame.

   **Still open: what happens when `olad` itself dies.** The first attempt ran in the wrong
   order - the tracker was killed first, which zeroed the universe, so stopping `olad`
   afterwards proved nothing. Redone properly: channel 1 set to 40 and left lit, then `olad`
   stopped underneath it. Note that `sudo -n` works on this Pi without a password, so this is
   scriptable. The answer was not read back before the test moved on.

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
6. ~~**Write the wave and the DMX output.**~~ **Written 2026-09-04.** `tracker/wave.py` and
   `tracker.run show`. Hills that follow each walker, one per person, combined with **max and
   never sum** so two overlapping hills cannot climb past the cap. Hold falls out for free - a
   stopped walker still has a track. Colour runs slow blue to fast white over a dim base, with
   the speed smoothed so it does not strobe. Attract is written but **off by default**.

   **69 tests pass** on the laptop. The earlier 65-test suite passed on the Pi, and the show has
   been run against the recorded two-walker
   crossing clip. **No water has been through it yet** - `--lights-only` is the next step, and
   it forces every fountain channel to zero so the pixels can be watched chasing a walker with
   nothing wet.

   The venv trap is fixed too: `include-system-site-packages` is `true`, the old file is at
   `~/wj-venv/pyvenv.cfg.bak`, and the venv imports `ola` and `pyrplidar`.

7. **A contactor on the 24 V, dropped by a watchdog.** New, and it is a build-spec item rather
   than a bench one. The modules latch their last value forever when DMX stops, so a software
   crash with jets up is a flood and no software stop can prevent it. An unattended hallway
   needs the 24 V switched by something that drops when the control software stops
   heartbeating. `cfg.resend_seconds` already re-sends a frame twice a second so that a
   watchdog has a heartbeat to watch. Nothing else exists yet. **Attract mode must stay off
   until this is built.** Raise as its own ticket against #10.

Once the calibration lands, the show is real and #10 unblocks.

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
- **Whether the modules answer standard E1.20 RDM.** ~~Untested.~~ **Half answered 2026-09-04,
  and the half that landed is good news.** `ola_rdm_discover -u 1 -f` returns an empty UID list,
  but `systemctl status olad --no-pager -n 40` shows discovery really running on the wire and
  **being answered**: DUB packets go out through `EnttecUsbProWidget`, wide UID ranges come back
  `BranchComplete, got 0`, and the branch narrowing on `2421:2112018x` comes back
  `BranchComplete, got 25`. Answering some ranges and not others is a real responder, not an
  open line picking up noise. **ESTA manufacturer ID 0x2421 is "HB-Laserkomponenten GmbH"** —
  the modules' own maker. So they are connected, powered, and speaking RDM.

  What fails is resolving a UID. The preamble byte is wrong and varies (`0x14`, `0x36`, `0x92`,
  `0xcb`) where a DUB reply should start `0xFE`, and every run ends `Discovery tree is
  corrupted`. Two readings, not yet separated: two responders sharing one UID from the factory
  (the datasheet's auto-addressing makes that plausible), or a non-standard DUB encoding. **The
  test is physical:** power only one module and rerun discovery. A UID that resolves means the
  first reading and RDM is usable one module at a time. Still corrupt on one module means the
  second, and the next thing to check is a 120 ohm terminator at the end of the DMX line.

  The two modules are **hardwired together**, so powering one alone is not possible and that
  test is off the table. Two routes were then tried and closed off from the laptop:
  `ola_rdm_get -u 1 --uid 2421:21120181 DEVICE_INFO` returns `Error: The RDM device could not
  be found` — OLA will not address a UID that discovery never resolved — and
  `/etc/ola/ola-usbserial.conf` has no RDM or timing knobs for this widget
  (`tri_use_raw_rdm` is for the RDM-TRI, not the Pro Mk2).

  What is left, if RDM is ever wanted: a **120 ohm terminator** across pins 2 and 3 of a
  5-pin XLR on the last module's DMX out, which is the usual cure for corrupted RDM on an
  unterminated bus; and OLA's Python `RDMGet` / `SendRawRDMDiscovery`, which may address a UID
  the CLI refuses, and could send a directed `DISC_MUTE` to silence responders one at a time —
  the same-UID test without unplugging anything. Also worth knowing for diagnosis: whether the
  two modules are joined by the manufacturer's longitudinal connector or by a cable splice, and
  whether that splice is a chain or a Y. A Y-wired bus corrupts RDM while still passing one-way
  DMX perfectly well.

  **This blocks nothing and is not worth chasing now.** Plain DMX is one-way and does not care.
  It only blocks reading the stored fountain-height calibration, which is why the jog ceiling
  stays a DMX number rather than a height in cm.

## Check this first, next time you are at the bench

The Pi went unreachable at the end of the last session — `water-jets.local` stopped resolving —
before its final DMX state could be confirmed. The last thing run against it was
`show --lights-only`, which forces every fountain channel to zero, so **no jet can have been
left up**. The pixels may be holding a colour, because the modules latch. Powering the Pi back
on does not clear them by itself; `olad` starts with an empty universe and sends nothing, and
the modules keep whatever they last received. Run this once the Pi answers again:

```
ssh pi@water-jets "cd ~ && ~/wj-venv/bin/python -m tracker.run zero"
```

Expect `slots_held=512 ALL ZERO`. If the interface is not plugged in it will say so plainly
rather than reporting success.

**Still unreachable on 2026-09-05.** `ping water-jets.local` from the laptop returns
`Ping request could not find host water-jets.local`. That is a name-resolution failure on
Windows, so it does **not** prove the Pi is off — but **no IP address for the Pi is recorded
anywhere in this repo**, so there is no second way in. Get it from `arp -a` on the laptop or from
the router, and **write it into this file**, so the next session is not stopped by the same
thing.

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

~~There is no `README.md`.~~ **Written with the `create-readme` skill.** It carries the setup
from zero, the wiring, the quickstart and the troubleshooting table. Regenerate it with the same
skill rather than hand-editing, and never overwrite a newer `create-readme` stamp than your own.

There is still no `hardware/` directory and no BOM. Every part is owned and nothing needs buying,
so a BOM would be a list of things already on the bench. Worth adding if this is ever rebuilt.

**One README claim is reconstructed rather than re-run:** the `apt install ola ola-python` line
in Setup step 1. OLA is installed and working on the Pi, and `ola-python` is the package that
puts `ola` in `/usr/lib/python3/dist-packages`, but the original install command was not run
again to confirm it. Everything else in Setup comes from `DECISIONS.md` or was checked live.

## Tooling, sorted 2026-09-05

None of this touched the jets. It is here so the same time is not spent twice.

- **`AGENTS.md` will stop reappearing.** It was never a Claude Code hook or skill -- the Codex
  desktop app was copying `CLAUDE.md` over it on every launch. The sync is off and the file is
  gone. **Untested across a Codex restart**; if `AGENTS.md` comes back, the toggle has to be set
  inside the Codex app instead. Full evidence in `DECISIONS.md`.
- **Global config cleaned.** A stale block in `C:\Users\garrett.reynolds\.claude\settings.json`
  had been telling agents that `DECISIONS.md` is an SR&ED evidence trail that must never be
  rewritten, which contradicts this project's **General** mode. Removed, with two other stale
  items. See `DECISIONS.md`.
- **Restart Claude Code** to pick up the edited settings; they are read at session start.
