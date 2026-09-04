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
