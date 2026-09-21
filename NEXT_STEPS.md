# Next steps

Last updated 2026-09-21.

## Where the plan actually lives

**GitHub issue #1** is the map and the canonical plan: `gh issue view 1`. This file is a
pointer and a cold-start summary, not a second source of truth. Decisions live in
`DECISIONS.md` and in each ticket's resolution comment. Do not restate them here.

## State

Every decision that can be made in a conversation has been made. **16 of 22 issues are closed.**
The design is settled, every part is owned, and **the whole chain has now run end to end with
water in the air.** The ten measured control points are verified with the first module. The
current live build uses those ten jets. The settings layout gives every configured jet its own
movable point. Do not propose connecting the second module unless Garrett changes that decision.

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
| Cost to finish | CAD $1,780.67 before tax, duty, and shipping |

Reach the Pi with `ssh pi@water-jets` (key-based, no password). OLA's web UI is at
`http://water-jets:9090`. The scan viewer is at `http://water-jets:8080/` while
`tracker.run live` is running.

## Open tickets

- **#17 to #22 — Hardware stop, response tuning, long-run tracking, and idle animations.**
- **#37 — Active area rectangle on `/settings`.** Done and closed 2026-09-21. The four
  `roi_*` numbers are live-editable, the map draws the rectangle with corner handles, and a
  path point outside is refused. iPad check passed: a corner drag moves the area, a walker
  outside it raises no track.
- **#38 — Shut down and reboot the Pi.** Built 2026-09-21 (see `DECISIONS.md`): two plain
  buttons, now in the Power box of the new **System page** `/system`, which also shows the
  Pi's health and the show's state. `/actions/reboot` and `/actions/shutdown`,
  zero-and-verify first, refuse otherwise. A refused command shows Resume. The four Active
  area sliders came off `/settings` the same day; the map's corner handles are the control.
  153 tests pass on the laptop and the Pi. Garrett checked the System page on the iPad
  2026-09-21: every value fills in.
  **Not yet done:** Garrett must install the sudoers rule (`README.md` Setup step 6; it needs
  the Pi password), then the bench check in the ticket: Reboot from the iPad, log ends in
  `ALL ZERO`, Pi comes back on SSH; Shut down, green LED out, power-cycle by hand.
- **#25 — Design system for the control pages.** `DESIGN.md` ("The Bench Instrument") and
  `PRODUCT.md` are committed. #24 and the five `/settings` fixes #26 to #30 are done (unlock
  target, amber on Apply, dead map on link drop, phone room for sliders, bar on one row). The
  fixes are on the Pi, the show is restarted, and all five were checked by hand on the phone.
  `/test` scored 26/40 on 2026-09-20 (snapshot in `.impeccable/critique/`); five fix tickets
  #32 to #36. #32 (sticky bar), #33 (Past the end) and #34 (held jet, lost tracks) are done
  and on the Pi. Remaining: fix #35 and #36, review `/`,
  move the shared CSS to one served file, re-run the document pass. Refinement only.

Issue #22 is complete. Chase passed on the real lights. Fade and Breathe have repeatable
software tests. Issue #21 still needs its low-water bench check. Idle water defaults to off.

Issue #16 was closed on 2026-09-19 because Garrett ruled out connecting the second module.

**#12 was closed on 2026-09-05, with no closing comment.** Items 1-6 were done and item 7 half
done: one unit is enough, a standing person is held 99% of the time, and position jitter is
7-13 mm against a 50 mm jet pitch. Item 3 closed on 2026-09-04 when DMX value 5 on channel 5 made
jet 1 spray — but **that result was never written into the ticket**, so #12's last checklist
still reads *"blocked: modules not connected"*. Item 7's absolute accuracy was never measured; it
is step 3 below.

## Done since the last update

- **2026-09-21:** #37 built, deployed, checked on the iPad, and closed (active area). #38
  built (Pi power control); waits on the sudoers rule and the bench check.
  Profile version is now 4; a saved JSON from before is refused by version.

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

## Bench session 2026-09-20: test mode, live-apply, sliders

The show ran with water again. Three operator problems came out of it and are fixed, deployed
to the Pi, and covered by tests (123 pass on the laptop and the Pi). See `DECISIONS.md` for
the two entries and `tracker/README.md` for the pages.

- **ALL OFF looked dead.** It zeroed, then the next scan put the walker's own hill straight
  back. ALL OFF now halts the live show (enters test mode) until **Resume live show**.
- **Jet tests moved to `http://water-jets.local:8080/test`.** Opening it enters test mode: output
  zeroed, live show muted, tracking still running so the page shows which jet the tracker sees
  under the walker. Only the Resume button leaves test mode; a closed tab does not.
- **Settings apply live.** Every edit goes out about 250 ms after the last change. The hard
  maximum, Load JSON, and Reset defaults still wait for Apply profile. Every number field on
  both pages is now a slider with a readout, for the iPad.

## Design system 2026-09-20 (evening)

`DESIGN.md` and `.impeccable/design.json` capture the pages' tokens and rules from
`tracker/viewer.py`. `PRODUCT.md` holds the durable product facts (one user, client hallway,
standard library only, the 24 V switch is the only real stop). The live viewer stays a dark
scope on purpose. The pages themselves did not change. Ticket #25 holds the follow-up.

## Design pass 2026-09-20 (night)

- **#24 done and committed** (`e474254`): the settings map draws tracks in the viewer's colours.
  Checked on the real LiDAR: a walker is green on both pages.
- **#23 closed**: not a software bug. Debris in jets 1 and 2. Garrett cleared it.
- **`/settings` scored 29/40.** Snapshot in `.impeccable/critique/`. Five fix tickets, #26 to
  #30, all small edits in `tracker/viewer.py`, same look. The four P1s sit on the safety-limit
  unlock and on the phone layout. Decided: on a phone the map shrinks and the sliders and the
  stop get the room.
- **#26 to #30 done, committed `cf96d38`** (see `DECISIONS.md`). The Pi has the files but the
  show that was running (`--lights-only`, PID 30644) still serves the old page; restart it with
  the `setsid nohup` line below. Checked by hand on the phone 2026-09-20: the unlock words tick
  the box; the hard maximum turns Apply amber; a normal slider still live-applies with the cap
  pending. The header still wraps to two lines at 390 px; the title and nav are too wide for
  one row at any font size.
- **#31 done, committed `3814bd8`.** Pulling the LiDAR USB used to exit the whole process.
  Now the show zeroes once, shows "LiDAR not available" on every page, and reconnects when the
  plug goes back. Garrett pulled the plug on the Pi and it came back; the log shows one zero,
  five failed attempts, then "lidar: back". This is also the #28 check, done. Show running
  lights-only (PID 38048) with the fix; the cap is back at 40 and test mode is off after the
  restart.
- **Pi folders `~/tracker` and `~/tracker/tests` were `r-x`**, so a new file could not be
  copied in. Fixed with `chmod u+w` on both (owner is `pi`, no sudo). Existing files always
  copied fine, which is why it was never noticed.
- **`/test` scored 26/40** (2026-09-20 evening, dual-agent, dry-run replay of `crossing.jsonl`
  on the laptop at port 8090). One P0: no sticky bar, so Stop test and the status box scroll
  apart on a phone. Three P1s: the readout leads with the clamped jet number; no "jet held"
  state and lost tracks look live; Resume is a one-way door. One P2: the readout wraps and
  jitters. Tickets #32 to #36, all small edits in `tracker/viewer.py`. See `DECISIONS.md`.
- **#32 done.** `/test` ends in the same sticky bar as `/settings`: status on the left, Stop
  test bottom-right. Resume live show moved into the yellow test-mode box at the top; the
  Leave test mode section is gone. `DESIGN.md` Layout and the Stop Never Scrolls Rule now name
  the page's stop, not ALL OFF, so it matches `DECISIONS.md`. 130 tests pass on the laptop and
  the Pi. Checked at 390 px on a dry-run replay: the bar pins to the bottom on a short and a
  tall viewport. Checked on the real iPad 2026-09-20: the bar holds while scrolling, Resume
  sits in the mode box, Stop test answers in place.
- **#33 done.** The `/test` readout uses `jet_position`, not the clamped `jet`. Off the strip it
  reads "Past the end". Dry-run replay of `crossing.jsonl`: `s=-0.18`, `-1.07`, `3.89` read
  Past the end; `s=3.06` reads Jet 10. 131 tests pass on the laptop and the Pi. Checked on the
  real strip 2026-09-20: standing on jet 1 reads Jet 1, off the end reads Past the end.
- **#34 done.** `SettingsControl.held` records the held jet test; `/state` carries `test_mode`
  and `held`, and the test page's mode box renders from that every poll ("TEST MODE. Holding
  jet 7 at 30 (22.9 cm). Stop test to drop it."). Tracks with `seen:false` render Muted with
  "(lost)". 133 tests pass on the laptop and the Pi. Dry-run replay: held text and lost
  tracks both seen at 390 px. **The held half is not checked on the Pi:** `test_jet` refuses
  while lights-only is on, so it needs a water session. The lost half was checked on the real
  iPad 2026-09-20: stepping out of view turns the entry grey with (lost), then it vanishes.
- **Next in the design work:** fix #35 and #36, critique `/`, then move the shared CSS to one
  served file, then `/impeccable document`.
- **Not ticketed, Garrett's call:** `/test` has a red "Stop test" and `/settings` a red
  "ALL OFF" in the same slot, both calling `/actions/all-off`. Renaming a safety button is not
  a refinement.
- `data/crossing.jsonl` is now on the laptop too (git ignores it), so the replay above runs
  without the Pi. Re-run the `/test` critique against a `localhost` URL target, not
  `tracker/viewer.py`: the file slug belongs to the `/settings` run and would mix the trends.
- **Pi state at close (2026-09-21, about 10:50):** the show is **running** in `--lights-only`
  (PID 12397, started with the standard `setsid nohup` line) with the #38 and System page files. Test mode off,
  cap 40. Stop it with the anchored `pkill` line below; power off needs Garrett's
  `ssh -t pi@water-jets "sudo poweroff"` until the sudoers rule from `README.md` Setup step 6
  is installed, after which the page's Shut down Pi button does it. Nothing on the
  pages saves to disk, so any restart puts the profile back to the config defaults.
- **Both iPad eyeball checks passed 2026-09-20:** the bottom bar stays on screen while
  scrolling, and a tapped jet tile turns green. Garrett checked both on the real iPad.
- **Loose files in the tree, not committed:** `bom/` holds ROM Raptors estimate spreadsheets
  that look like they belong to another project; `AGENTS.md` is the Codex copy; `.claude/` is
  local tooling. Decide whether `bom/` moves out or gets a `.gitignore` rule.
- **Git prints "failed to delete .git/worktrees/agent-…: Permission denied" on commit.** Stale
  agent worktrees with a locked folder. Harmless so far; `git worktree prune` from a shell
  with no agent running should clear it.
- **Local replay for design checks:** port 8080 on the laptop is taken by another project's
  `server/server.py`. Use `python -m tracker.run --viewer-port 8090 show --replay <clip>
  --baseline data/room-baseline.json --dry-run --loop` (the flag goes before `show`). Walker
  clips live on the Pi under `~/data/`; `crossing.jsonl` works. Chrome headless clamps the
  window to ~500 px, so a real phone layout needs an iframe wrapper at 390 px. To screenshot
  a state the page only reaches after an action (a held jet), serve the wrapper over http, have
  it POST the action from a timer, and hold its own load event with a slow `<img>`; Chrome's
  `--virtual-time-budget` fast-forwards the timers past the network and shows the stale page.
  Use `--timeout` and real time instead.

## UI pass 2026-09-20 (afternoon)

A design review of the three pages, run against a dry-run replay on the laptop with headless
Chrome at desktop and phone widths. Eight fixes, same look, deployed to the Pi, 123 tests pass.
See `DECISIONS.md` ("The stop button never leaves the screen") and `tracker/README.md`.

- **ALL OFF, Apply profile, Lights only, and the status line sit in a bar stuck to the bottom
  of the screen.** The test-mode banner sits in the same bar. Undo applied and Reset defaults
  moved from the map corner into the Profile box.
- **Heights show DMX and cm** on both pages, using the measured 0.762 cm per unit.
- **The live viewer** has a viewport tag, a Test jets link, the tallest-jet line in the stats
  box (it was drawn under it), and a grey readout with dashes when the Pi drops.
- Colour level and White level have readouts and a swatch. Header links are buttons.

Left running when the session closed: the show in `--lights-only` (no water), started from
the laptop at about 11:55 with the standard `setsid nohup` line below. The previous run was
stopped by SIGTERM at 11:52:40 with the hard maximum at **156** (about 119 cm); on restart the
cap read 40 again, so the unlocked value did not survive the restart.

Checked on the real iPad 2026-09-20: the bottom bar stays put while scrolling, and a tapped
jet tile turns green.

**Design tickets:** #32, #33, #34 are done; #37 (active area) is built and awaits the iPad
drag check. Next is **#35** (a way back into test mode after
Resume; the mode box is its obvious home, see the ticket comment), then #36 (readout typesetting;
expect to update #34's test assertions when the spans change).

**Do first, next session:**

1. **Prove test mode with a real walker.** Every check so far ran on a replay or an empty
   hallway. Walk, get a hill up, open `/test` on the iPad: the water must drop and stay down
   while walking, and the `show.log` line must read `TEST`. (`/settings` loads on the iPad
   and the bottom bar with ALL OFF stays on screen while scrolling: checked 2026-09-20.)
2. **Check the held-jet text with water** (#34's unverified half). Lights-only off, hand on the
   24 V switch, Start test on `/test`: the yellow box must read "Holding jet N at H (cm)", and
   Stop test must clear it. `test_jet` refuses while lights-only is on, so this needs water.
   (#23, the first two jets not reacting, was debris; closed.)
3. **iPad as the only control surface.** Garrett asked for the app to be functional on the
   iPad. The pages are now touch-sized and reachable at `http://water-jets.local:8080/`. Still
   open: starting and stopping `show` needs SSH from the laptop. The pages work in iPad
   Safari (checked 2026-09-20). Decide whether a start/stop control belongs on the Pi (a
   service plus a button) before charting anything.

Restart the show from the laptop, in PowerShell:

```
ssh pi@water-jets "pkill -f '^/home/pi/wj-venv/bin/python -m tracker'"
ssh pi@water-jets "cd ~ && setsid nohup ~/wj-venv/bin/python -m tracker.run show --baseline data/baseline.json > ~/show.log 2>&1 < /dev/null & disown"
```

The old `pkill -f 'python -m tracker'` also kills the SSH shell that runs it; use the anchored form.

## Do next, in order

1. ~~**Calibrate where the strip actually is.**~~ **Done 2026-09-19.**

   Garrett measured one LiDAR x/y target point for each of jets 0 through 9. The tracker uses
   a joined path through all ten points and interpolates between adjacent jets. The mapping is
   in `Config.strip_points` and is covered by unit tests. Garrett verified the live viewer map,
   light aim, and water aim for jets 0 through 9 on 2026-09-19. The live show used a peak of
   DMX 30. It stopped cleanly and read back all 512 DMX slots at zero. The ten points define
   the full path. Issue #15 now starts all 20 output jets across it without more measurements,
   then lets the operator move every jet point on the layout.

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
   The first-module live follow passed on 2026-09-19 with `lead_seconds=0.50`,
   `follow_response=0.0`, `hill_peak=30`, and `height_max=40`. The jet rise time itself was not
   measured, so issue #18 stays open.
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
   stopped underneath it. (An earlier note here said `sudo -n` works on this Pi without a
   password. It does not, checked 2026-09-21; see `README.md` Setup step 6.) The answer was not read back before the test moved on.

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
   watchdog has a heartbeat to watch. The DIN rail design now selects a Siemens
   `3UG5651-1CW30` pulse watchdog, a Siemens `3RT2026-1BB40` 24 VDC contactor, and a BDMICRO
   `OPTO-4` isolator. The selected parts cost CAD $1,434.04 before tax, duty, and shipping.
   Nothing is ordered or built. The GPIO17 heartbeat code is on the Pi, and all 97 tests pass
   there. The 10 A fuse and 14 AWG wire are selected. The five live fault results remain open in issue #17. **Attract
   mode must stay off until this is built.**

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

The Pi is reachable as `pi@water-jets`. The settings page is at
`http://water-jets.local:8080/settings` while the show runs. The 20-point layout was confirmed
in the browser on 2026-09-19. Profiles still live in the browser as JSON files; a Pi restart
loads the default 10-jet profile until the operator loads and applies a saved profile.
The Water jet tester selects one jet and height, holds that test, and uses **Stop water test** to
send and verify all zero. Live first-module follow passed with a 0.50 s lead and the DMX 40 cap.

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
