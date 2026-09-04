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

The DMX interface is **not** decided. I had ruled out the MADRIX USB ONE from MADRIX's own pages — Windows-only drivers, and DMX-out gated behind a paid MADRIX KEY. Garrett pushed back: why not use an adapter he already owns? He was right. Those terms bind MADRIX's software, not the chip inside the box; a rebadged FTDI part would be driven by OLA regardless. Ruling hardware out on a vendor's software licence, when `lsusb` answers it in two minutes, was the wrong call. Both owned dongles now get bench-tested before anything is bought, as GitHub issue #13, which blocks the control-path decision. Fallback, if both fail, is the Pi's own UART into a CAD $2.50 MAX485 module via OLA's `uartdmx` plugin — no dongle at all. Detail on GitHub issue #9.
