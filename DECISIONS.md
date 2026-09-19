# Decisions

## [2026-09-19] Use only the first 10 jets

The installation now uses jets 0 through 9 on the first HB-Laser module. The second module
stays unused. The default tracker configuration changes from 20 jets to 10 jets, so normal
show output uses only DMX channels 1 through 50. Calibration now measures jet 0 and jet 9.

## [2026-09-19] Map jets 0 through 9 to ten measured person positions

Garrett stood at the real target position for each jet and measured these LiDAR x/y points in
jet order: `(1.80, -1.64)`, `(1.80, -1.32)`, `(1.75, -1.00)`, `(1.72, -0.73)`,
`(1.65, -0.48)`, `(1.62, -0.19)`, `(1.60, 0.07)`, `(1.51, 0.47)`, `(1.55, 0.65)`, and
`(1.54, 1.20)`. The tracker now uses a joined path through all ten points. Each point maps
exactly to its jet. Positions between two points interpolate between those two jets. This is a
person-to-jet control map, not the physical nozzle spacing. Garrett walked the live path and
confirmed on 2026-09-19 that the large viewer jet label maps it correctly.

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

## [2026-09-04] Sensing method: one RPLIDAR A2, tracking legs

Sensor choice is a **Slamtec RPLIDAR A2** that Garrett already owns: one unit at one end of the strip, sweeping a level scan plane at shin height, running off-the-shelf `leg_tracker` to follow walkers by their legs. 15 Hz gives a 67 ms scan period and roughly 17–52 mm of position error across the room, against a 50 mm jet pitch. Speed comes from the tracker differentiating position, which satisfies the speed-driven hill colour from the wave decision.

The runner-up was the overhead depth camera Garrett also owns. It is faster (~11 ms of sensor latency against 67 ms), has no occlusion, and sees a person standing still. It was my recommendation. **Garrett chose the A2 instead**, and that stands. The A2 needs almost no compute, so one Raspberry Pi can run both the tracker and the DMX output — which matters for the control path ticket.

The HLK-LD2450 radar is ruled out on its own datasheet: 0.75 m distance resolution against a 1 m strip. VL53L5CX/L8CX ToF is ruled out on geometry: about 280 mm per zone from a normal ceiling, wider than the whole 250 mm hill. Neither was ruled out on water.

Two constraints fall out and are now a prototype ticket: `leg_tracker` will not open a track until a leg pair has moved 0.5 m, which fights the hold-when-stopped rule; and one end-mounted LiDAR can be blocked by the nearer of two crossing walkers, which the wave decision explicitly requires. Detail on GitHub issues #8 and #12.

## [2026-09-04] Water is out of the sensor selection criteria

Garrett: *"You have made an assumption that water is going to affect the sensor we select. Please never assume. I will make sure that the sensor is protected."* Two rounds of grilling had been built on whether a sensor could see the water columns, reasoned from automotive rain-clutter papers rather than from any test of a fountain. Physical protection and mounting are Garrett's to solve. Sensors are now selected on measured specs only — resolution, update rate, target count, interface, and what is already owned. Whether the jets appear in the scan data stays on the map as an open question for the tracker's filtering, not as a selection criterion.

## [2026-09-04] Brain is a Raspberry Pi 5 running plain Python, not ROS

The sensing choice decides the controller: LiDAR leg tracking is Linux software, so the "ESP32 on its own" option from the control-path research is dead. **Raspberry Pi 5**, already owned; RAM unknown because a heatsink covers the label, and it does not matter at this workload.

**Plain Python on Raspberry Pi OS, not ROS 2.** The package that made ROS attractive, `angusleigh/leg_tracker`, targets ROS 1 Noetic on Ubuntu 20.04, and ROS 1 reached end of life in May 2025. There is no ROS 2 port. So the choice was never "install a package" against "write code" — it was "stand up a dead ROS 1 stack" against "write a small tracker." For two walkers in a 3 m room the tracker is one file: cluster the scan points, pair them into legs, follow the pairs by nearest neighbour. The `leg_tracker` source stays a reference for the algorithm and its parameters rather than a dependency. Sensor connects over USB.

The DMX interface is **not** decided. I had ruled out the MADRIX USB ONE from MADRIX's own pages — Windows-only drivers, and DMX-out gated behind a paid MADRIX KEY. Garrett pushed back: why not use an adapter he already owns? He was right. Those terms bind MADRIX's software, not the chip inside the box; a rebadged FTDI part would be driven by OLA regardless. The rule-out was premature rather than plainly wrong — gating DMX output behind a paid licence, and MADRIX shipping its own USB vendor ID, are themselves evidence of custom silicon. But `lsusb` is free, definitive and takes two minutes, so it runs before anything is ruled out or bought. Of the two dongles, the undocumented HB-Laser one has the better chance. Both owned dongles now get bench-tested before anything is bought, as GitHub issue #13, which blocks the control-path decision. Fallback, if both fail, is the Pi's own UART into a CAD $2.50 MAX485 module via OLA's `uartdmx` plugin — no dongle at all. Detail on GitHub issue #9.

## [2026-09-04] Control path: Pi 5 to Enttec DMX USB Pro Mk2, over OLA

Garrett named two more devices he owns, neither of which was on the map: an **Enttec DMX USB Pro Mk2** and an **Enttec Open DMX USB**. The Pro Mk2 is precisely the interface the control-path research was going to have him buy for CAD $227. Nothing needs buying, and the whole system collapses to one box.

**Chosen: Raspberry Pi 5, RPLIDAR A2 in over USB, Enttec DMX USB Pro Mk2 out over USB.** `olad` drives the Enttec through OLA's `usbpro` plugin, which names the device explicitly in its README, so there is no plugin patching or VID:PID guesswork. The tracker and wave logic sit in plain Python and talk to `olad` through OLA's Python client.

The Pro Mk2 beat the also-owned Open DMX USB on one point: it is the only owned device with an **onboard frame buffer**. Every other candidate — Open DMX USB, a MAX485 on the Pi's UART, and both unknown dongles — is host-timed, so DMX break and slot timing ride on Linux scheduling. On a Pi simultaneously reading a LiDAR at 15 Hz and running a tracker, hardware timing is worth taking when it is free. The Open DMX USB stays as the spare.

The MADRIX USB ONE is out: Windows-only drivers and a paid MADRIX KEY required for DMX output. The bench test ticket raised for the two unknown dongles is closed as moot without being run.

One thread survives elsewhere. The HB-Laser USB-DMX-RDM is probably the "optional programming connector" the module datasheet requires for auto-addressing and RDM fountain-height recalibration. That is commissioning rather than runtime, and it is now fog on the map, not a ticket, because it is not yet known whether the modules need addressing by hand at all. Detail on GitHub issue #9.

## [2026-09-04] Enttec manual closes the connector question and may retire the HB-Laser dongle

Read the ENTTEC *DMX USB PRO MK2 User Manual* (doc ID 134658, December 2021) after choosing the interface. Two things it settles.

**Connectors:** *"1\* 5-Pin Male XLR for DMX Input, 2\* 5-Pin Female XLR for DMX Output"*, carried on a 15-pin breakout cable. Female output is the E1.11 convention and mates with a standard fixture's male input, so a stock 5-pin DMX cable should join the Enttec to the modules with nothing to fabricate. What must be confirmed on the shelf is that the breakout cable is in the kit, and the gender on the module cable end.

**RDM:** *"RDM (E1.20) is supported as standard on the DMX USB PRO Mk2."* The modules use RDM for auto-addressing and fountain-height recalibration, which the module datasheet gates behind an optional programming connector and separate software. Since OLA is an RDM controller and the chosen interface speaks RDM, commissioning may need neither the HB-Laser dongle nor a Windows machine. Whether the modules answer standard E1.20 parameters or a vendor-specific set is unknown. This does not change the control-path decision; it narrows the commissioning fog on the map.

Also noted: Mark-After-Break is settable 10-1355 us and Break 96-1355 us in the interface's own hardware, which gives tuning room if the modules prove fussy about timing.

## [2026-09-04] LiDAR variant is the A2M8; 15 Hz confirmed as the right setting

Garrett confirmed the unit is an **RPLIDAR A2M8**. The sensing decision had used the datasheet's conservative "<=1 degree" angular figure. The A2M8 datasheet (rev 2.6) is more specific and better: 8,000 samples per second, scan rate freely adjustable 5-15 Hz, and 0.45 degrees of angular resolution at the typical 10 Hz, adjusted automatically with rotation speed.

Since the sample budget is fixed, resolution trades directly against scan rate. At 15 Hz that is 533 samples per turn, 0.68 degrees, and by arithmetic 12 to 35 mm of lateral error from 1 m to 3 m. The earlier estimate was 17 to 52 mm. Against a 50 mm jet pitch, both scan rates are comfortably inside one jet, so slowing to 10 Hz to buy resolution would cost 33 ms of latency and gain nothing the wave can use. **15 Hz stands.**

One caveat carried to the prototype ticket: the datasheet states the 8,000 samples/s mode uses an extended high-speed protocol and requires the matched SDK or a modified driver. A Python driver speaking the older 4,000/s protocol would halve the resolution to 1.35 degrees at 15 Hz, about 70 mm at 3 m, which is wider than a jet pitch. The driver's reported sample rate must be checked on the bench rather than assumed.

## [2026-09-04] Every part is owned; nothing needs buying

Garrett confirmed the whole parts list is on the shelf: RPLIDAR A2M8, Raspberry Pi 5, Enttec DMX USB Pro Mk2 with its 15-pin breakout cable, an Enttec Open DMX USB as spare, the 24 V supply that shipped with the modules, and every cable. The build has a **CAD $0 bill of materials**, with no conditions attached. The control-path research had been heading for a CAD $227 Enttec purchase.

Two loose values were then closed without a bench, because both were already answerable from evidence gathered earlier in the same session. The **24 V supply came with the jets**, so it is the manufacturer's supply for this exact load and the 6.4 A concern was unfounded. The **module cable is 5-pin male**, and the Enttec Pro Mk2's breakout carries one male DMX input and two female DMX outputs - quoted verbatim from the Enttec manual earlier the same day. Male into female mates directly. Both had been put to Garrett as questions and both should have been reasoned out instead; he said so, and he was right.

With the inventory closed, the bench prototype is the only ticket standing between the map and the build-ready spec. Detail on GitHub issues #3 and #12.

## [2026-09-04] Raspberry Pi OS Lite 64-bit, headless

The Pi 5 gets **Raspberry Pi OS Lite, 64-bit**, the current Debian 13 (Trixie) release dated 18 June 2026, installed headless and reached over SSH.

Lite rather than Desktop because this Pi ends up running unattended in a hallway: a desktop is more surface to update, more to go wrong, and nothing the finished installation uses. Trixie rather than the Legacy Bookworm image because nothing here needs the older base - OLA is packaged in Trixie main as `ola` 0.10.9.nojsmin-7.1, with `ola-python` and `ola-rdm-tests` alongside it. 32-bit was never a real option on a Pi 5.

The cost of choosing Lite is that there is no local window to plot LiDAR scans in. Debugging the tracker therefore needs a small web viewer served from the Pi and opened on a laptop. That is a consequence to build, not a reason to take the desktop image, and it is noted on the prototype ticket.

SSH is set up with password authentication to start with, for speed at the bench. It should move to key-only before the system goes into a wall.

## [2026-09-04] LiDAR measured on hardware; motor PWM 800

The A2M8 ran on the Pi for the first time. The sensing decision was made from datasheets and it survives contact with the hardware.

**Measured against predicted:** 14.57 Hz against 15 Hz, 68.6 ms against 67 ms, ~7,350 samples/s against the claimed 8,000, 0.715 degrees against 0.715, and 13/25/37 mm of lateral error at 1/2/3 m against a predicted 12/24/35. Slightly optimistic, which is the right direction.

**Boost mode is mandatory, not optional.** The device reports three modes: Standard at 2,000 samples/s, Express at 4,000, and Boost at 8,000. Only Boost reaches the datasheet's headline figure. Standard mode would give 2.6 degrees at this scan rate, about 137 mm at 3 m, nearly three jet pitches, and would sink the whole approach. The driver must decode `ULTRA_CAPSULED` frames.

**Motor PWM 800 chosen, giving 14.57 Hz.** A PWM sweep showed the unit will spin to 19.39 Hz at full power, well above Slamtec's rated 5-15 Hz band, for 17 ms less latency. Garrett took the rated setting. The sample rate is constant at about 7,350 dots per second regardless of spin speed, so scan rate and angular resolution trade one-for-one: at 19.39 Hz the error at 3 m is 49.7 mm against a 50 mm jet pitch, which is no margin at all. The 17 ms is also likely invisible against the still-unmeasured time a jet takes to rise. Revisit only if the water proves fast.

**Two hardware facts came out of the bench.** First, the Pi 5's USB ports were current-limited to 600 mA because its 65 W supply offers only 3 A at 5 V, and a Pi 5 needs a fixed 5 V / 5 A profile to unlock 1.6 A. The LiDAR browned out the bus every time its motor started. A powered USB hub fixed it completely and is now part of the build. Second, `pyrplidar` 0.10.9 does not drain its serial buffer on stop, and threw protocol sync errors on reconnect twice; production code needs retry and an explicit flush or the installation will fail to start at random.

## [2026-09-04] Pi device naming and OLA lockdown

Caught at session end rather than when made. Two configuration choices on the Pi that the build depends on.

**Fixed device names via udev.** `/etc/udev/rules.d/99-water-jets.rules` matches on USB serial number and creates `/dev/ttyENTTEC` for the Enttec DMX USB Pro Mk2 (serial `EN329670`) and `/dev/ttyLIDAR` for the RPLIDAR A2M8's CP2102 bridge. This was not tidiness. Plugging the LiDAR in reassigned the Enttec from `ttyUSB0` to `ttyUSB1`, which on an unattended installation would break the show at random. The rule proved itself immediately: a second, unrelated FTDI device with the same `0403:6001` chip appeared on a hub and did not steal the Enttec's name, because the match is on serial.

**OLA restricted to one device and one plugin.** `ola-usbserial.conf` had three `device_prefix` entries covering all of `ttyUSB*`; these were replaced with a single `device_prefix = ttyENTTEC`. Every plugin except `usbserial` was set to `enabled = false`. Before this, OLA's StageProfi plugin was locking the LiDAR's serial port every few seconds, probing it, failing and releasing, which would have fought the LiDAR driver permanently.

**A related fault that will recur.** OLA writes `/var/lock/LCK..ttyUSB0` holding the locking PID, and the file survives a restart. When a recycled PID matches, `olad` reads its own PID back and refuses to open the port, reporting `locked by PID N and process exists`. This cost most of an hour tonight and produces no visible symptom beyond silent jets. The unattended build must clear stale OLA lock files at boot.

## [2026-09-04] Tracker written: plain Python, record-and-replay first

The tracker and the web scan viewer are written and run on the Pi. Code is in
`tracker/`, driven by `python -m tracker.run`. No numpy, no Flask, no ROS - the
whole thing is the standard library plus `pyrplidar`.

**Recording came before tracking.** The Pi runs OS Lite with no window to plot in,
and a walk-past cannot be repeated on demand. So `tracker.run record` writes scans
to JSON Lines and `tracker.run replay` plays them back in real time through the
same code path as the live sensor. Every parameter can now be tuned against a
recorded walk instead of against a person standing in a hallway.

**Background subtraction replaces leg_tracker's trained classifier.** `leg_tracker`
uses a random forest to tell a leg from a chair leg. Here `tracker.run baseline`
takes the nearest return per 1-degree bin over an empty-room recording, and
anything later found 0.15 m nearer than that is a person. Simpler than a
classifier and it needs no training data.

Tested properly, on a clip the baseline had never seen: two 20-second recordings
of the same still bench, baseline built from the first, tracker run on the second.
Result **2 false people without the baseline, 0 with it**. (Scoring a baseline
against the recording it was built from proves nothing - every point is background
by construction. The first attempt did exactly that and was thrown out.)

**Nothing behind the sensor.** The first honest cross-clip run left **one** false
person that sat at x -0.35 to -0.05 for all 273 scans: bench clutter beside the
LiDAR, in baseline bins the first clip happened never to fill. Sweeping `roi_x_min`
showed -0.50 keeps it and 0.00 removes it, so the default is now **0.00**. The cost
is that the sensor is blind behind itself, which is acceptable while it sits at one
end of the strip. Note the general shape of the fault for later: a baseline bin
that was never filled is treated as "anything here is a person", so intermittent
near-field returns become permanent people. Widening the region of interest again
means recording a longer baseline.

**A lone cluster counts as a person.** At a normal standing stance the legs are
about 0.20 m apart centre to centre, so their surfaces are 0.09 m apart - under
`cluster_dist_euclid` (0.13 m). A standing person is therefore **one** cluster, not
two. Requiring a pair would lose the walker exactly during Hold. Two clusters only
appear mid-stride. This is a test in `tracker/tests/test_tracking.py`.

**Hold is handled by a second confirmation rule.** `leg_tracker` opens a track only
after 0.5 m of travel (`dist_travelled_together_to_initiate_leg_pair`), which #12
item 6 flags as fighting Hold. The config keeps that parameter and its 0.5 m value,
and adds `min_times_seen_to_initiate` (default 8 scans, about 0.5 s). A track
confirms on **either**. Both behaviours are covered by tests, including one that
shows the distance rule alone misses a standing person.

**Filter is leg_tracker's constant-velocity Kalman, written out by hand.** Its
4-state filter has no cross terms between x and y, so two 2-state filters are
equivalent and need no matrix library. Noise values are lifted unchanged:
`std_obs` 0.1, `std_process_noise` 0.03333, association variance `(0.1 + 0.4)^2`.

Verified: 10 unit tests pass on the laptop and on the Pi; `live` runs at 16.18 Hz
against the real A2M8 with the viewer reachable at `http://water-jets.local:8080/`;
0 false tracks on a 273-scan clip the baseline had not seen. What is **not**
verified is anything about real walkers - that needs #12 items 5-7 and a recording
of two people.

## [2026-09-04] Correction: PWM 800 is 16.25 Hz, not 14.57 Hz, and is out of spec

Re-measuring the motor PWM sweep with the new code contradicts the numbers logged
earlier today. The earlier figures were low by about 10 percent across the board.

| PWM | Logged 2026-09-04 | Re-measured | Samples/s now |
|---|---|---|---|
| 660 | 11.19 Hz | 12.74 Hz | 7,996 |
| 700 | - | 13.71 Hz | 7,995 |
| 730 | - | 14.39 Hz | 8,003 |
| 760 | - | **15.09 Hz** | 8,000 |
| 800 | 14.57 Hz | **16.25 Hz** | 8,000 |

Two things say the new numbers are the right ones. The offset is consistent at
every PWM value, which is a measurement fault rather than a hardware change. And
the sample rate now lands on **8,000/s exactly**, the datasheet figure, instead of
the 7,350 logged earlier - the device was never 8 percent short of its own spec.

The likely cause is the old sweep script's clock. `bench/lidar_pwm_sweep.py` sets
`t0` immediately after `start_scan_express()` returns, then measures for **5
seconds**. The device does not begin streaming the moment that command is
acknowledged - it has to lock rotation phase first - so the dead time before the
first capsule is counted as scanning time. Working backwards from the offset that
dead time is roughly 0.4 to 0.7 seconds, which against a 5-second window is the
10 percent seen. The new `tracker.run check` starts its clock after the first
complete revolution and measures for 12 to 15 seconds, so both the dead time and
the partial first turn fall outside the window. This is the likely cause, not a
proven one; the old script is kept in `bench/` as the record.

**What this changes.** The PWM 800 decision was taken on the stated grounds that it
was "the rated setting" inside Slamtec's 5-15 Hz band. At a true 16.25 Hz it is
**not** inside that band. PWM 760 gives 15.09 Hz, which is. The cost of moving is
6.4 ms of extra latency; the gain is 2.7 mm less error at 3 m and running the
bearing where the manufacturer rates it.

Angular resolution is unaffected by which one is picked: 0.679 degrees at PWM 760
and 0.731 at PWM 800, giving 35.6 mm and 38.3 mm of lateral error at 3 m, both
comfortably inside the 50 mm jet pitch. Nothing about the sensing decision on #8 is
overturned either way. `config.py` still defaults to **PWM 800**, the logged value,
pending Garrett's call.

## [2026-09-04] Two walkers from one walker: merge two clips by nearest return

Garrett has no second person to test with. Issue #12 item 5 - does one A2M8 hold
both tracks through a crossing - needs two people **in the data**, not two people in
the room.

**A 2D LiDAR reports only the nearest thing on each ray.** So take a left-to-right
recording and a right-to-left recording, and on every ray keep whichever return is
nearer. That is exactly the scan the sensor would have produced with both walkers
present, shadows included, because a nearer body wins the ray under the same rule
the hardware uses. This is not an approximation of occlusion; it is the mechanism.

Built as `tracker/merge.py` and `tracker.run merge A B --shift-b S --out C`.
Verified two ways: a unit test merges two synthetic one-person clips and asserts the
result **matches a real two-person scan point for point**; and the CLI ran on two
real 20-second bench recordings, producing a valid file that replays.

One limit on that "point for point". The test's rays sit on an exact grid, so every
return lands in its own slot. Real A2 angles jitter, so two real returns less than
half a ray apart compete for one slot and the farther one is dropped. That is inside
the sensor's own resolution and does not matter, but it is why the merge is faithful
rather than exact.

**`--shift-b` is the point of the tool.** It slides the second clip in time, which
decides where the two walkers meet. One pair of recordings therefore gives the whole
sweep: crossing right in front of the sensor (worst shadow), crossing at the far end
(mildest), or never meeting (the control). `merge` prints the closest approach and
when it happens, so the shift can be aimed rather than guessed.

**Two things it cannot do**, both stated so nobody forgets. The recorded people never
react to each other - no stepping aside, no slowing down; the ticket asks about the
sensor, not about manners. And rays are matched by rounding the angle to the sensor's
own sample spacing (360/503 = 0.7157 degrees), so two returns only compete when they
are genuinely the same ray. Truncating instead of rounding was a real bug found by
the test: floating point put two neighbouring rays in one slot and silently threw
away a third of the points.

**Items 6 and 7 never needed two people at all.** Track initiation for a standing
person and real latency and accuracy all come from one person. Two-thirds of #12 is
unblocked with no trick.

## [2026-09-04] USB hub swapped; over-current fault ended with it

Garrett changed the powered USB hub. Checked afterwards, and it is good.

The udev rules held: `/dev/ttyLIDAR` and `/dev/ttyENTTEC` both still resolve, even
though the underlying names swapped over - the Enttec moved from `ttyUSB1` to
`ttyUSB0` and the LiDAR from `ttyUSB0` to `ttyUSB1`. That swap is exactly the failure
the rules were written to prevent, and they prevented it. The match is on serial
number, so which hub or port a device lands on does not matter.

**The over-current fault stopped dead at the swap.** The kernel log holds 1,091
over-current events between uptime 1,288 s and 4,400.9 s, and **none after
4,400.9 s** - the moment the new hub enumerated. A 12-second Boost-mode LiDAR run
afterwards added none. The new hub is a Genesys Logic USB2.1/3.1 unit.

The underlying supply problem is unchanged and still logged: `max_current` is 3000
and `usb_max_current_enable` is 0, because the 65 W supply offers only 3 A at 5 V.
The powered hub makes that irrelevant for the LiDAR, which is why it was the
recommended fix.

Measured on the new hub: 16.04 Hz, 7,995 samples/s, 499 samples/scan, 0.722 degrees.

## [2026-09-04] Baseline is a low percentile, so the room never has to be empty

Garrett: *"I don't have an empty room."* The background baseline was built from the
**nearest** return per bearing, which silently assumes nobody is in the scan while it
records. Somebody walking through a bearing would set that bearing's horizon to their
own body, and a person standing there later would then be invisible.

**The horizon is now a percentile of each bearing's returns, not the minimum.** Sort a
bin's distances nearest first. A person on that bearing for a fraction f of the clip
owns the first f of the list, so a percentile p above f steps straight over them,
while a static object that answers for more than p of the clip is still captured. p is
`background_percentile`, and p = 0.0 is exactly the old rule.

**Default is 0.35**, chosen from measurement rather than taste. A synthetic walker
crossing in front of the sensor holds any one bearing for **12%** of a clip, so 0.35
has roughly three times the margin. The failure mode is real and was measured too: a
short 2-second clip where the walker ends up parked on a far bearing reaches **34.5%**
occupancy, because angular speed collapses with distance. That is why the recording
must be 60 s and the walker must keep moving.

The cost was checked, though the check has a limit worth stating. A sweep over the two
real 20-second bench recordings - baseline from the first, tracker on the second -
gave **0 false tracks at every percentile from 0.0 to 0.7**. But both clips are a
still bench, and the cost of a high percentile is a *static object answering
intermittently* being pushed past the horizon and becoming foreground. This bench has
exactly such an object - the near-field clutter - and it is already excluded by
`roi_x_min = 0.00`, so the sweep could not see the failure mode. The honest claim is
therefore: no cost measurable **inside the region of interest on a still bench**. If
the real room holds intermittent clutter inside the region of interest, it will show
as ghost points, and the fix is a lower `--percentile`.

`tracker.run baseline --percentile` exposes it, and the recording plan now ends with a
self-check: replay the baseline's own clip through `tracker.run offline`. Garrett was
walking in it, so he should come out as a track. If he does not, he was absorbed into
the baseline and the clip needs redoing.

## [2026-09-04] First real person tracked; the room mapped from its own baseline

Garrett recorded 60 seconds of the real room with himself walking about in it:
924 scans at 15.40 Hz, `~/data/room.jsonl` on the Pi.

**The percentile baseline works on real data.** All **360 of 360 bins filled**, and
the self-check gave **16.2 moving points per scan** against a "must be over 10"
threshold and a still-bench reference of 0.6. He was not absorbed into the room he
was standing in. With no baseline the same clip reads 80.9 moving points per scan.

**It tracked him.** Over the 924 scans:

| Confirmed tracks alive | Share of scans |
|---|---|
| 1 | **78.0%** |
| 0 | 14.9% |
| 2 | 3.8% |
| 3 or 4 | 3.2% |

One person, one track, most of the time. The longest single track held him for
**17.1 seconds over 4.81 m**, and three others ran 10 s or more. Six short-lived
clusters appeared and correctly **never confirmed** - 1 to 2 seconds each with under
0.1 m of travel - which is the confirmation rule doing its job. This is the first
evidence of the tracker following a real human rather than a synthetic one.

The track broke about eight times across the minute. He was deliberately walking
everywhere, including through the excluded clutter zone, so re-entry accounts for
most of it. Whether it also happens on a clean walk past the strip is what clips 2
and 3 will show.

**The room, read off the baseline.** Two halves, and they match what Garrett said:

- **Bearings 105 to 300 degrees: clutter, 0.23 m to 1.4 m.** Closest at 150-180
  degrees (0.35 m) and 105-135 degrees (0.85 m). This is the "bunch of stuff directly
  behind the sensor".
- **Bearings 300 through 0 to 90 degrees: open.** A wall at about 2.3 m across 30-90
  degrees - his "about 2 m of open space" - opening out to 3 to 8 m towards 0 and 300
  degrees, which is presumably a corridor.

**The frame is the right way round.** Rotating `mount_angle_offset_deg` by 180
degrees drops the moving points kept from 16.2 to 3.9 per scan, so the default 0
already points the tracked half-plane into the open space. Fine adjustments are
worth little until the strip is physically mounted: 0, +15 and -15 degrees give 16.2,
17.1 and 14.8 points per scan. **`mount_angle_offset_deg` stays at 0** and gets set
properly against the strip, not against a bench.

The region of interest does clip him. About 80% of his moving points fall in the open
half-plane, but only 66% survive the full box, because `roi_y` is +/-2.0 m and he
walked wider than that. Left alone on purpose: the wave only cares about walkers
near a 1 m strip, so a person 2.5 m away is not wanted.

## [2026-09-04] Two real faults found on the first real walk: cluster width, and a stale baseline

Garrett recorded 30 seconds of himself walking his line, `~/data/walk-left-right.jsonl`,
433 scans at 14.41 Hz. He walked past twice. Scored against the room baseline recorded
minutes earlier, the tracker reported **four to six people at once, for the whole clip**.
Two separate faults, both real, both now fixed.

### Fault 1: `max_cluster_width` was throwing a real person away

Four of the phantom tracks were static: they sat at fixed points for all 433 scans with
a median speed of 0.00-0.02 m/s. But the walker himself was also being lost. During his
second pass the tracker saw **20 to 50 foreground points per scan and produced no
detection at all**.

Instrumenting the cluster stage found it immediately. **A real person reads 0.45 to
0.62 m wide** at close range - both legs, the gap between them, and clothing - against a
`max_cluster_width` of 0.45 that had been guessed from theory as "two legs merged". Every
scan over the limit dropped him silently: the cluster existed, it just was not a leg
candidate. His second pass was over 0.45 the entire time, so no track ever formed.

A sweep put the knee at **0.65**, and it is now the default. On the walk clip it takes the
tracks from 1 to 2 - both passes caught instead of one - and the longest track from 38 to
70 scans. On the 60-second room clip it does not add phantoms; it **removes** them, from 8
tracks to 7 and from 4 simultaneous to 3. Above 0.65 nothing changes at all.

### Fault 2: a baseline goes stale the moment the room changes

The other phantoms were the room itself. Something moved between the 60-second room
recording and the walk recording, so objects that had been farther away were now nearer
than the stored horizon, and each became a permanent person - confirmed in 8 scans by
`min_times_seen_to_initiate` and then held forever. That rule exists so a standing person
is not missed, and this is its cost.

**The fix is to build each clip's baseline from that clip itself.** The percentile design
already makes this legal: a walker occupies any one bearing for far less than 35% of a
clip, so he does not become part of his own baseline. Measured on the walk clip:

| Baseline | Confirmed tracks | Result |
|---|---|---|
| the earlier room clip | 8, four of them permanent | wrong |
| **the walk clip itself** | **1** | right |

With both fixes, the walk clip reads exactly one person during each of his two passes and
nothing at all between them.

**The exception is the standing-still clip.** Somebody who stands on one bearing for more
than 35% of a clip *would* be absorbed into a baseline built from it. That clip must be
scored against a baseline from a different, walking clip.

**For the installation, neither fix is sufficient.** A baseline captured at boot goes
stale as soon as anything in the hallway moves. That wants a rolling baseline that keeps
updating, which is not built and is now noted on the map.

## [2026-09-04] #12 item 5 answered: one A2M8 holds both walkers through a crossing

Garrett walked his line twice, once each way, 30 seconds each, alone. Merging the two
clips by nearest return per ray gives the scan two people would have made. Answer:
**one RPLIDAR A2M8 is enough. No second unit.**

Each clip alone tracks cleanly first - one confirmed person, 0.91 and 0.92 m/s median
speed, nothing when he is out of shot. Merged with time shifts of 0, 1, 2, 3 and 4
seconds, so the pair meet at five different points, the tracker held **two confirmed
tracks at once in every case**, for 57 to 73 scans - about 4 to 5 seconds each.

Walked through at shift 2 s, scan by scan, the crossing looks like this:

| | Track 1 | Track 2 |
|---|---|---|
| y from | +1.61 | -1.64 |
| y to | **-2.94** | **+2.95** |
| Scans held | 80 | 82 |
| Median speed | 0.96 m/s | 0.92 m/s |

They pass at 4.7-5.1 s at x about 0.8 m from the sensor, closest **0.05 m between
track centres**. Both **keep their own id straight through** and carry on in their
original directions afterwards - no swap, no drop, no merge into one. Track 1 stalls
briefly at 5.1-5.3 s, speed dipping to 0.72 m/s while it coasts on prediction through
the shadow, then recovers. That is the constant-velocity filter doing exactly the job
it was put there for.

This is the hardest case, not the easiest: they crossed within 0.15 m of each other at
under 1 m from the sensor, where each body subtends about 44 degrees and the occlusion
is near total.

**One bug found and fixed on the way.** `merge` used to report a "closest approach"
computed from the nearest raw return of each clip. That is whatever clutter sits by the
sensor, not a person, so it printed the same 0.08 m for every time shift and was
useless. Replaced with `crossing_report`, which subtracts the background, runs the
tracker, and reports scans holding two tracks, the most at once, and the real gap
between the two people.

**Still open on #12:** items 6 and 7 need the standing-still clip, and item 3 needs the
water modules connected.

## [2026-09-04] #12 item 6 answered, item 7 half answered: standing works, 7-13 mm jitter

Garrett stood still at three spots on his line, 596 scans over 40.1 s,
`~/data/standing.jsonl`.

### Item 6: a standing person is tracked, and leg_tracker's rule alone would miss him

| Rule | Scans with the standing person confirmed |
|---|---|
| `min_times_seen_to_initiate = 8` (this build) | **589 of 596, 99%** |
| distance travelled only (leg_tracker's rule) | 442 of 596, 74% |

The 25-point gap is the whole of his **first ten-second stand**. He was already standing
when the clip began, so under leg_tracker's
`dist_travelled_together_to_initiate_leg_pair` he had not walked 0.5 m and was never
opened as a track at all. This is exactly the Hold failure #12 predicted from reading
the source, now measured on hardware. The local rule fixes it.

### Item 7, precision half: 7 to 13 mm of jitter

Position reported while genuinely standing still, one standard deviation:

| Spot | Scans | x | y | Range | Jitter |
|---|---|---|---|---|---|
| A | 127 | 0.875 +/- 0.008 | -1.205 +/- 0.010 | 1.489 m | **12.6 mm** |
| B | 139 | 0.693 +/- 0.003 | -0.001 +/- 0.007 | 0.693 m | **8.2 mm** |
| C | 165 | 0.740 +/- 0.004 | +0.882 +/- 0.005 | 1.151 m | **6.6 mm** |

Against a 50 mm jet pitch this is four to eight times better than needed. It grows with
range, as expected.

The three spots are collinear to within 0.5%: A-B 1.218 m plus B-C 0.884 m is 2.102 m
against a measured A-C of 2.091 m. That is an internal consistency check and it passes.
**Absolute accuracy is still unmeasured** - it needs Garrett's tape measure, and it
carries an unknown offset because the A2's mirror does not sit at the centre of its
case.

### Item 7, latency half: the tracker costs 0.26 ms

Measured on the Pi 5 over 596 real scans: median **0.26 ms** per scan, 95th percentile
0.27 ms, worst 0.45 ms. Against a 67.2 ms scan period that is **0.4% of the budget**.
The sensor is the entire latency; the software is free. The plain-Python-not-ROS
decision is vindicated. End-to-end latency still needs a timed external event.

### A sharper rule about baselines

Scored against a baseline built from **its own clip**, the third stand vanished
completely - and raising `background_percentile` to 0.5 or 0.6 did not bring it back.
The percentile arithmetic is not the whole story. Behind spot C there was nothing in
range, so **his body was the only thing that bearing ever saw**; the percentile of a
list containing only his returns is his own distance, whatever the percentile. A person
standing in front of open space is absorbed at any setting.

So the rule is not "use a high percentile for standing clips". It is: **never build a
baseline from a clip in which anybody stands still.** Score standing clips against a
walking clip's baseline. With `data/base-rl.json` the coverage is 100% for every second
of the clip after the first.

## [2026-09-04] First DMX output: full 512-slot frames, jog starts at zero, LED before pump

Garrett filled a 24 in x 16 in test basin to 9 cm — above the 8 cm minimum the maker's
FAQ gives — and set the rule for the first power-up: *"please start at a very low number
and ensure there is a way to shut them off quickly."* Three things were decided writing
`tracker/dmx.py`.

**Every frame is a full 512 slots**, never a short one. A short DMX frame updates only
the slots it carries, and most fixtures hold the rest of the universe at their last
value. A five-slot "all off" would therefore leave slot 5 — nozzle 1's pump — exactly
where it was. Sending 512 every time makes that question moot by construction instead of
answering it by experiment with water in the basin. `zero()` then reads the universe back
with `FetchDmx`, because "I sent zeros" and "olad holds 512 zeros" are different claims.

**OLA's Python client, not shelling out to `ola_set_dmx`.** The shell tool is proven and
synchronous, which is attractive for a safety path, but it buys nothing on the one hazard
that matters — a short frame — and the wave needs the Python client anyway, so the plumbing
is better proven now. `ClientWrapper` is an event loop, so `send()` passes a callback that
stops the loop and turns it back into a blocking call. Frames are `array.array("B")` and
not `bytearray`: OLA calls `.tobytes()` on what it is given, and `bytearray` has no such
method. That cost one failed run on the Pi.

**The bench order proves the stop on an LED, not a pump.** Channels 1-4 of a nozzle are
red, green, blue and white; only channel 5 is fountain height. So the entire DMX path,
including the emergency stop, can be proven with light. `--channel` is required for that
reason — the only defaults worth having are a harmless LED or a pump, and guessing wrong
in that direction puts water on the ceiling. `--max` defaults to 40 because the datasheet
range is 5 cm to 1.5 m and the DMX-value-to-height mapping is RDM-calibrated and unread.

Stop layers, in the order they are trusted: the tool zeroes through a signal handler, a
`finally` and an `atexit`; `tracker.run zero` is the second terminal's command; and a
switch on the 24 V supply's mains lead is the only one that does not depend on software.
**SIGHUP is handled on purpose** — it is what a dropped ssh sends, and the one signal that
would otherwise skip the `finally` entirely.

Verified on the Pi with nothing non-zero ever sent to a module: `zero` reports
`slots_held=512 ALL ZERO`, and a jog holding **channel 512** at 10 returned the universe
to all-zero after a `SIGHUP`. Channel 512 was chosen because two HD modules occupy 1-100,
so no fixture listens to it.

**Still unknown, and it is the failure that matters:** whether the modules latch on DMX
signal loss, and whether the Enttec Pro Mk2's onboard frame buffer — chosen as a feature —
keeps repeating the last frame if `olad` dies. Every software stop above assumes neither
happens. `tracker/README.md` step 2b tests it by stopping `olad` with an LED lit, before
any pump runs.

Also fixed: `~/wj-venv` had `include-system-site-packages = false`, which made `import ola`
fail inside the venv. It is now `true`, the original is at `~/wj-venv/pyvenv.cfg.bak`, and
the venv imports both `ola` and `pyrplidar`.

## [2026-09-04] The modules fail frozen, not fail safe. The 24 V switch is the only stop.

Tested on real hardware with nozzle 1's **red LED** lit at DMX value 40, so nothing could get
wet while finding this out. Two cuts, in order:

| Cut | Expected | What happened |
|---|---|---|
| `sudo systemctl stop olad` | LED goes out | **LED stayed lit** |
| Enttec USB pulled from the Pi | LED goes out | **LED stayed lit** |

So the modules **hold their last commanded value indefinitely when DMX stops**. They do not
fall back to off. Cutting the signal at any point in the chain — daemon, driver, USB, cable —
changes nothing once a value has landed.

This is the important safety property of the whole build and it was not in the datasheet:
**the system fails frozen, not fail safe.** If the Pi crashes with a jet at full height, the
jet stays at full height until somebody cuts the 24 V.

**What still works.** The software stop is real, but only as an *action*, not as a *fallback*.
`tracker.run zero` and the jog tool's zero-on-exit both turn a lit LED off — proven earlier the
same session — because they actively send a zero frame the modules then latch. They work while
the whole chain is alive. They do nothing once any link in it is dead.

**What this retires.** `DECISIONS.md` chose the Enttec Pro Mk2 partly for its onboard frame
buffer, on the reasoning that hardware DMX timing beats Linux scheduling on a busy Pi. That
reasoning stands for timing and is wrong for safety: the buffer keeps transmitting the last
frame after the host dies. But the second test settles that it does not matter which device is
at fault — with the Enttec unpowered and transmitting nothing at all, the LED still stayed lit.
**The latch is in the modules.** Swapping to the host-timed Open DMX USB would not help.

**What this forces into the build spec (#10).** A hardware kill on the 24 V supply is not a
nicety, it is the only stop that exists. For an unattended hallway installation that means a
switched contactor on the 24 V feed, dropped by a watchdog when the control software stops
heartbeating — otherwise a software crash is a flood. Raise as its own ticket.

Untested at the time of writing: whether cycling the 24 V clears the latch, and whether the
modules come back off or resume the held value. That is the next thing on the bench, and it is
also the only stop procedure this system has, so it needs proving before a pump ever runs.

## [2026-09-04] DMX-to-height is linear: 7.62 mm per DMX unit, full scale about 1.94 m

Measured at the bench on jet 1, channel 5, in the 24 in x 16 in test basin.

| DMX value | Jet height | cm per DMX unit |
|---|---|---|
| 5 | "a very little spray" | - |
| 20 | **6 in = 15.2 cm** | 0.762 |
| 40 | **12 in = 30.5 cm** | 0.762 |

**Two measured points, and they agree exactly.** Double the DMX value, double the height, so
the line passes through the origin with no offset. **0.762 cm per DMX unit**, which makes one
press of the jog tool's default step of 5 about **3.8 cm, or 1.5 inches**. Extrapolated to 255
that is **194 cm**.

The 20 in point was taken as a prediction and then checked, not fitted after the fact: 6 inches
was predicted from the 40 reading and 6 inches is what came back.

That extrapolation lands almost exactly on the maker's website claim of *"A maximum water
height of 2 m can be reached (height can vary between 5 cm and 2 m)"*, and above the module
datasheet's more conservative *"Fountainheight from 5 cm up to 1,5m"*. Two independent sources
agreeing with two bench measurements is good evidence that the mapping is linear over a 2 m
range.

Still unmeasured: the bottom of the range. The "very little spray" at DMX 5 would be 3.8 cm
under this fit, against a datasheet minimum of 5 cm — the right order, but a fountain is most
likely to depart from a straight line right where it starts, and nothing between 0 and 20 has
been measured. That only matters if the wave ever wants very short jets.

**Why this matters more than it looks.** DMX 255 is roughly two metres of water. In a hallway
that is the ceiling. Combined with the latch behaviour logged above — the modules hold their
last value forever when DMX stops — a wrong value written once is not a transient. The wave
code must clamp its output well below full scale, and the clamp belongs in the code, not in
the operator's care. `tracker.run jog` already defaults `--max` to 40, which this measurement
now justifies: 40 is 12 inches, a sane ceiling for a test basin.

Useful working numbers, if linear: DMX 10 is 7.6 cm, 20 is 15.2 cm, 30 is 22.9 cm, 60 is
45.7 cm, 80 is 61 cm.

## [2026-09-04] Wave design: max not sum, two clamps, attract off, and metres not jet index

Logged at session end rather than when decided. Four choices inside `tracker/wave.py` that are
not obvious from reading it, and that a later change could quietly undo.

**Overlapping hills combine with `max`, never `sum`.** Two walkers close together would
otherwise stack into a jet taller than either hill asked for, and past the cap. `max` cannot
exceed its inputs, so the property holds without a second guard.

**Two separate height numbers, and they are not the same kind of thing.** `hill_peak` is what
the wave *wants* — a design knob. `height_max` is what the code will *ever send* — a safety cap,
applied by `dmx.clamp_heights` as the last step before a frame goes out, after all wave logic.
The cap therefore holds even if the wave is wrong. This split exists because these modules latch
their last value forever when DMX stops, so a bad height is not a transient. Tests assert no
frame ever exceeds the cap.

**Attract is written but off by default.** It is the one behaviour that runs with nobody
watching, and combined with the latch, a crash mid-roll leaves jets up in an empty room. It
stays off until there is a contactor on the 24 V that a watchdog can drop.

**The wave reads `track["s"]` in metres, not `track["jet"]`.** The tracker clamps `jet` into
`0..jet_count-1`, so somebody standing three metres past the end of the strip reports jet 19.
Reading it would have looked correct in every test with a walker on the strip, and pinned the
last jet up whenever anyone stood beyond it. Verified both ways: a walker at s=1.2 m and beyond
raises no water, and both ends of the strip still work.

## [2026-09-04] RDM parked, not solved. It was only ever wanted for one number.

The modules answer RDM — ESTA manufacturer 0x2421 is HB-Laserkomponenten, their own maker — but
OLA cannot resolve a UID from their discovery replies, and every run ends `Discovery tree is
corrupted`. Two readings remain unseparated: two responders sharing a factory UID, or a
non-standard DUB encoding. The test that would separate them needs one module powered alone, and
the modules are hardwired together, so it cannot be run.

Two software routes were tried and both are dead ends. `ola_rdm_get` refuses a UID that
discovery never resolved, and `/etc/ola/ola-usbserial.conf` exposes no RDM or timing knobs for
this widget.

**Parked deliberately.** RDM was only ever wanted to read the stored fountain-height
calibration, and that number has since been measured directly on the bench instead — 7.62 mm per
DMX unit. Nothing else in the build needs RDM: plain DMX is one-way and does not use it. What is
left to try, if it is ever wanted, is a 120 ohm terminator on the last module's DMX out, and
OLA's Python `RDMGet` / `SendRawRDMDiscovery`, which may address a UID the CLI refuses.

## [2026-09-05] The AGENTS.md that kept coming back is Codex, and the sync is now off

`AGENTS.md` had been deleted from this repo several times and kept returning as a byte-for-byte
copy of `CLAUDE.md`. It is not a Claude Code hook, skill, or harness behaviour, and it was never
tracked by git, which is why the deletions left no trace to follow.

The **Codex desktop app** copies `CLAUDE.md` to `AGENTS.md` on launch, in every repo it has
marked trusted, because Codex reads only `AGENTS.md`. The proof is Codex's own record: the table
`external_agent_config_imports` in `C:\Users\garrett.reynolds\.codex\state_5.sqlite` logs
`item_type: AGENTS_MD`, source `...\water-jet-follower\CLAUDE.md`, target
`...\water-jet-follower\AGENTS.md`, at 2026-09-04 14:48:28 and again at 2026-09-05 08:52:15 --
the second of those four seconds before the file's own birth timestamp.

**Decided:** Codex is not used on this repo, so the copy is unwanted. The import sync was turned
off -- `external-agent-import-sync-enabled = false` under `[desktop]` in
`C:\Users\garrett.reynolds\.codex\config.toml`, backup at `config.toml.bak-2026-09-05` -- and
`AGENTS.md` was deleted.

**Unverified:** that this key is what gates the copy, and that the edit survives a Codex restart.
Codex rewrites its own `config.toml` from `~/.claude/settings.json` during the same sync, so a
hand edit there may be overwritten. The test is to launch Codex and see whether `AGENTS.md`
returns. If it does, the toggle has to be set inside the Codex app instead.

## [2026-09-05] Global config no longer contradicts this project's General logging mode

An `autoMode.environment` block in `C:\Users\garrett.reynolds\.claude\settings.json` described a
different project entirely and asserted that *"DECISIONS.md is an SR&ED evidence trail, so failed
experiments and dated entries must never be deleted or rewritten."* This project's `CLAUDE.md`
sets the logging mode to **General**, where a superseded entry can be corrected in place. An
agent taking the settings block as binding would have refused to correct a wrong entry in this
file and appended a contradiction underneath it instead.

**Removed**, along with two other stale items found in the same sweep: a `SessionStart` hook
still enforcing a superseded version of global CLAUDE.md section 6, and two `skillOverrides`
trying to disable `create-readme` and `decision-log` -- the two wonderMakr skills that this
repo's own `CLAUDE.md` and `NEXT_STEPS.md` instruct agents to use. Two duplicate personal copies
of those skills were deleted in favour of the plugin versions. General mode now stands unopposed.
