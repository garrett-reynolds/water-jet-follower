# Water-Jet Follower Build Specification

Status: approved by Garrett on 2026-09-19. Bench-proven on jets 0 through 9.

The final build uses jets 0 through 19.

This document defines the final 1 x 20 water-jet strip.

The two HB-Laser modules sit end to end.

The first module is verified with real light and water.

The second module still needs calibration and a bench check.

The build is not ready for unattended use until the hardware stop in this document exists.

## 1. System result

The system finds people with one RPLIDAR A2M8.

It makes one five-jet water hill for each person.

The light colour changes from blue to white as the person moves faster.

The final strip has 20 jets and 20 RGBW pixels.

## 2. System path

The signal path is:

`person → RPLIDAR A2M8 → tracker → wave → OLA → Enttec DMX USB Pro Mk2 → two HB-Laser modules`

See the full wiring diagram in [water-jet-follower.html](water-jet-follower.html).

The Raspberry Pi 5 runs the tracker, wave, OLA, and web viewer.

The viewer uses `http://water-jets:8080/`.

OLA uses DMX universe 1.

## 3. Parts

Prices are in CAD.

| Qty | Part | State | Cost to finish |
|---:|---|---|---:|
| 1 | Slamtec RPLIDAR A2M8 | Owned and tested | $0 |
| 1 | Raspberry Pi 5 with its own supply | Owned and tested | $0 |
| 1 | Powered Genesys Logic USB hub | Owned and tested | $0 |
| 1 | Enttec DMX USB Pro Mk2 | Owned and tested | $0 |
| 1 | Enttec 15-pin breakout cable | Owned and tested | $0 |
| 2 | HB-Laser 3D HydroMatrix HD Single Module | Owned; first module tested | $0 |
| 1 | HB-Laser 24 V supply | Owned and tested | $0 |
| 1 | 5-pin DMX cable and module link | Owned and tested | $0 |
| 1 | 24 V contactor and watchdog stop | Not selected | Unverified |

The listed owned parts add CAD $0.

The final cost is not known until the contactor and watchdog are selected.

## 4. Physical layout

Put the two modules end to end.

Module 1 holds jets 0 through 9.

Module 2 holds jets 10 through 19.

Each module has ten jets at 50 mm pitch.

Mount the LiDAR at one end of the strip.

Keep the scan plane level at shin height.

Put the scan origin at the LiDAR mirror.

Do not use the centre of the LiDAR case as the range origin.

## 5. Wiring

```text
RPLIDAR ──USB──► powered hub ──USB──► Raspberry Pi 5
Enttec  ◄─USB── powered hub ◄──USB── Raspberry Pi 5
Raspberry Pi 5 ──OLA──► Enttec ──5-pin DMX──► module 1 ──link──► module 2
watchdog ──control──► contactor ──switched 24 V──► module 1 ──link──► module 2
```

| From | To | Link | Required result |
|---|---|---|---|
| RPLIDAR A2M8 | Powered USB hub | USB | Linux device is `/dev/ttyLIDAR`. |
| Enttec Pro Mk2 | Powered USB hub | USB | Linux device is `/dev/ttyENTTEC`. |
| Powered USB hub | Raspberry Pi 5 | USB | The hub uses its own power supply. |
| Enttec output | Module 1 DMX input | 5-pin XLR | Use DMX universe 1. |
| Module 1 | Module 2 | HB-Laser link | Carry DMX and 24 V to module 2. |
| HB-Laser 24 V supply | Module 1 power input | HB-Laser feed | Feed both linked modules. |
| Hardware watchdog | 24 V contactor | Heartbeat control | Drop power when the heartbeat stops. |
| 24 V contactor | Module 24 V feed | Switched power | Open on a fault. |

The LiDAR must use the powered hub.

The Pi USB ports did not supply enough current for LiDAR motor start.

The 24 V contactor must default to off.

The contactor must open when the Pi, tracker, OLA, Enttec, or DMX path fails.

## 6. DMX map

Each jet uses five channels.

The order is red, green, blue, white, and height.

Module 1 uses channels 1 through 50.

Module 2 must use channels 51 through 100.

The module 2 address is not verified on the real hardware.

| Jet | Module nozzle | Red | Green | Blue | White | Height |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1-1 | 1 | 2 | 3 | 4 | 5 |
| 1 | 1-2 | 6 | 7 | 8 | 9 | 10 |
| 2 | 1-3 | 11 | 12 | 13 | 14 | 15 |
| 3 | 1-4 | 16 | 17 | 18 | 19 | 20 |
| 4 | 1-5 | 21 | 22 | 23 | 24 | 25 |
| 5 | 1-6 | 26 | 27 | 28 | 29 | 30 |
| 6 | 1-7 | 31 | 32 | 33 | 34 | 35 |
| 7 | 1-8 | 36 | 37 | 38 | 39 | 40 |
| 8 | 1-9 | 41 | 42 | 43 | 44 | 45 |
| 9 | 1-10 | 46 | 47 | 48 | 49 | 50 |
| 10 | 2-1 | 51 | 52 | 53 | 54 | 55 |
| 11 | 2-2 | 56 | 57 | 58 | 59 | 60 |
| 12 | 2-3 | 61 | 62 | 63 | 64 | 65 |
| 13 | 2-4 | 66 | 67 | 68 | 69 | 70 |
| 14 | 2-5 | 71 | 72 | 73 | 74 | 75 |
| 15 | 2-6 | 76 | 77 | 78 | 79 | 80 |
| 16 | 2-7 | 81 | 82 | 83 | 84 | 85 |
| 17 | 2-8 | 86 | 87 | 88 | 89 | 90 |
| 18 | 2-9 | 91 | 92 | 93 | 94 | 95 |
| 19 | 2-10 | 96 | 97 | 98 | 99 | 100 |

Every output frame has all 512 DMX slots.

Unused slots stay at zero.

## 7. Show rules

| Rule | Value |
|---|---|
| Active jets | 20 in the final build |
| Hill width | 5 jets |
| Normal hill peak | DMX 30, about 22.9 cm |
| Hard height cap | DMX 40, about 30.5 cm |
| Hill position | 0.15 seconds ahead of the walker |
| Two walkers | One hill for each confirmed track |
| Overlap | Use the larger value. Never add the two values. |
| Stopped walker | Keep the hill under the track. |
| Base colour | RGBW `(0, 0, 40, 0)` |
| Slow colour | RGBW `(0, 0, 255, 0)` |
| Fast colour | RGBW `(255, 255, 255, 255)` at 1.6 m/s |
| Colour smoothing | 0.5 seconds |
| Empty room | All heights zero |
| Attract mode | Off until the watchdog contactor exists |
| DMX resend | Every 0.5 seconds |

The last output step must cap every height channel at DMX 40.

## 8. Sensor and tracker settings

| Setting | Value |
|---|---|
| Sensor | RPLIDAR A2M8 |
| Scan mode | Boost |
| Motor PWM | 800 in current code |
| Measured speed at PWM 800 | About 16.25 Hz |
| Rated-band alternative | PWM 760 at about 15.09 Hz |
| Range | 0.15 m to 6.0 m |
| Region x | 0.0 m to 3.5 m |
| Region y | -2.0 m to 2.0 m |
| Background margin | 0.15 m |
| Track start | 8 scans or 0.5 m of travel |
| Track coast time | 1.0 second |

PWM 800 is above the A2M8 rated 15 Hz limit.

The final PWM choice is still open.

## 9. Control-path map

The ten measured points define the full walking path.

They are control points.

They are not one required measurement for each final jet.

| Point | LiDAR x | LiDAR y | State |
|---:|---:|---:|---|
| 0 | 1.80 | -1.64 | Verified |
| 1 | 1.80 | -1.32 | Verified |
| 2 | 1.75 | -1.00 | Verified |
| 3 | 1.72 | -0.73 | Verified |
| 4 | 1.65 | -0.48 | Verified |
| 5 | 1.62 | -0.19 | Verified |
| 6 | 1.60 | 0.07 | Verified |
| 7 | 1.51 | 0.47 | Verified |
| 8 | 1.55 | 0.65 | Verified |
| 9 | 1.54 | 1.20 | Verified |

Spread the configured jet count across this path.

The final profile uses 20 jets.

The current bench profile uses 10 jets.

## 10. Configuration screen

The existing browser viewer will also hold the settings screen.

The settings module has one small interface.

It loads, validates, previews, applies, and saves one full profile.

It must not write a partial profile into a running show.

### Path and hardware settings

- Drag, add, remove, undo, and reset control-path points on the scan view.
- Set the jet count from 1 to 20.
- Enable or disable one jet.
- Test one jet at a safe value.
- Reverse the jet order.

### Water settings

- Set the minimum active water height.
- Set the normal hill height.
- Set the hard maximum water height.
- Set the hill width.
- Set the lead time.
- Set the follow response.

The hard maximum needs a clear warning and a lock.

Zero always means off and stays outside the minimum active height.

### Colour settings

- Set the base RGBW colour.
- Set the slow RGBW colour.
- Set the fast RGBW colour.
- Set the slow speed threshold.
- Set the fast speed threshold.
- Set the maximum idle brightness.

### Screen actions

- Save one versioned JSON profile.
- Load a saved profile.
- Preview all changes before apply.
- Apply the full validated profile as one change.
- Enter lights-only mode.
- Send ALL OFF and read back all 512 DMX slots at zero.

## 11. Idle animations

The operator can select an idle water animation and an idle colour animation in the profile.

Idle water starts off by default.

It stays disabled until the watchdog contactor passes.

Idle water includes an end-to-end hill, a soft ripple, and a slow low-height pulse.

Idle colour includes an end-to-end chase, a slow colour fade, and a breathing effect.

All idle water stays inside the idle minimum and the hard maximum.

All idle colour stays inside the idle brightness limit.

A confirmed person stops the idle animation and takes control.

ALL OFF clears both water and colour channels.

## 12. Software and start commands

The Pi uses Raspberry Pi OS Lite 64-bit.

The code runs in `~/wj-venv`.

Run this safe check first:

```sh
ssh pi@water-jets "cd ~ && ~/wj-venv/bin/python -m tracker.run zero"
```

Expect `slots_held=512 ALL ZERO`.

Run lights only next:

```sh
ssh pi@water-jets "cd ~ && ~/wj-venv/bin/python -m tracker.run show --baseline ~/data/baseline.json --lights-only"
```

Run water only with a person at the 24 V switch:

```sh
ssh pi@water-jets "cd ~ && ~/wj-venv/bin/python -m tracker.run show --baseline ~/data/baseline.json"
```

Run zero after the test:

```sh
ssh pi@water-jets "cd ~ && ~/wj-venv/bin/python -m tracker.run zero"
```

## 13. Stop rules

The software stop sends 512 zero slots.

It works only while the full control path works.

The modules hold the last DMX value when the signal stops.

The modules also hold the value when OLA stops or the Enttec is unplugged.

Use the 24 V switch for every attended bench test.

Do not enable attract mode for the current bench build.

Do not use the system unattended until the watchdog contactor passes a real fault test.

## 14. Acceptance checks

The final build passes only when all checks pass.

| Check | Required result | Current state |
|---|---|---|
| LiDAR Boost mode | About 8,000 samples/s | Passed |
| First module address | Module 1 starts at channel 1 | Passed |
| Second module address | Module 2 starts at channel 51 | Not verified |
| Control-path map | Ten draggable points can drive 20 jets | Not built |
| Light aim | Correct pixel hill on all 20 jets | First 10 passed |
| Water aim | Correct water hill on all 20 jets | First 10 passed |
| Settings profile | Save, load, validate, preview, and apply one full profile | Not built |
| Per-jet controls | Disable, test, and reverse safely | Not built |
| Idle water | Three capped animations and person takeover | Not built; blocked by watchdog |
| Idle colour | Three limited animations and person takeover | Not built |
| Height cap | No height channel above DMX 40 | Passed in code and first module test |
| Normal stop | Read back 512 zero slots | Passed |
| Hardware fault stop | 24 V drops when the heartbeat stops | Not built |
| Attract mode | Stays off until the hardware fault stop passes | Passed in current config |
| Motor speed | Final PWM is inside the chosen operating limit | Open |

## 15. Release blocks

1. Build the configuration screen and settings profiles in issue #14.

2. Map all 20 jets across the existing control path in issue #15.

3. Commission and verify the second module in issue #16.

4. Build and test the watchdog contactor in issue #17.

5. Measure jet response and choose the motor PWM in issue #18.

6. Keep the background baseline fresh in issue #19.

7. Check whether water changes LiDAR tracking in issue #20.

8. Build idle water animations in issue #21.

9. Build idle colour animations in issue #22.

Garrett accepted this specification on 2026-09-19.

The release blocks stay open until the related hardware work passes.
