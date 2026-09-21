# water-jet-follower

A strip of water jets that follows people along a hallway. One LiDAR finds walkers by their
legs, and a hill of water rises under each one. It runs on a Raspberry Pi 5 in plain Python.

**Prototype. The final build uses all 20 jets. Jets 0 through 9 use a measured person-to-jet
path and are verified with light and water. Jets 10 through 19 are not calibrated yet.**

[Decisions](DECISIONS.md) · [Next steps](NEXT_STEPS.md) · [Glossary](CONTEXT.md) · [Tracker notes](tracker/README.md)

![The signal chain, from a walker in the hallway to water in the air](docs/water-jet-follower.png)

## ⚙️ How It Works

1. **The LiDAR sweeps a level slice.** It sits at one end of the strip at shin height. Boost
   mode gives 8,000 samples a second at about 16 Hz.
2. **The tracker removes the room.** A baseline holds the nearest thing on each bearing. Points
   nearer than the baseline are people.
3. **The tracker follows each walker.** It clusters the moving points, pairs them into legs, and
   runs a constant-velocity Kalman filter. One track per person.
4. **The wave builds a hill.** Each confirmed walker gets a hill five jets wide, centred a
   little ahead of them. Two hills that overlap combine with max, never sum.
5. **The frame goes out as DMX.** Every frame carries all 512 slots. A hard cap limits every
   fountain channel as the last step before sending.
6. **The modules raise the jets.** `olad` drives the Enttec, which drives the modules over DMX.
   Each nozzle takes five channels: red, green, blue, white, height.

The pixel beside each jet takes its colour from the walker's speed, slow blue to fast white. A
walker who stops keeps their hill, because their track is still there.

## ✨ Features

- **Follow.** A hill of water tracks each walker along the strip.
- **Hold.** The hill stays put when a walker stops.
- **Two walkers.** One hill each, and they pass through each other cleanly.
- **Colour by speed.** Slow is blue, fast is white, over a dim base colour.
- **Attract.** A slow half-height hill rolls end to end when nobody is there. Off by default.

## 🔩 Hardware

| Part | Choice |
|---|---|
| Sensor | Slamtec RPLIDAR A2M8, one unit, Boost mode |
| Controller | Raspberry Pi 5, Raspberry Pi OS Lite 64-bit, headless |
| DMX interface | Enttec DMX USB Pro Mk2 |
| Water | 2 x HB-Laser 3D HydroMatrix HD modules, 10 jets each; first module verified |
| USB hub | Powered hub, Genesys Logic USB2.1/3.1 |
| Module supply | 24 V DC, 3.2 A per module |

- **The powered hub is not optional.** The Pi 5 limits its USB ports to 600 mA on a 65 W supply.
  The LiDAR browned out the bus every time its motor started.
- **The modules latch.** They hold their last commanded value forever when DMX stops. A switch
  on the 24 V mains lead is the only real stop.
- **Boost mode is mandatory.** Standard mode gives 2.6 degrees at this scan rate. That is nearly
  three jet pitches of error at 3 m.

## 🔌 Wiring

| From | To | Cable | Notes |
|---|---|---|---|
| RPLIDAR A2M8 | Powered USB hub | USB | Appears as `/dev/ttyLIDAR`. Never plug it straight into the Pi. |
| Enttec Pro Mk2 | Powered USB hub | USB | Appears as `/dev/ttyENTTEC`. Serial `EN329670`. |
| Powered USB hub | Raspberry Pi 5 | USB | The hub carries its own supply. |
| Enttec breakout | Module 1 input | 5-pin XLR | Enttec output is female. The module input is male. |
| Module 1 | Module 2 | HB-Laser link | Final build uses both modules. Current bench config drives module 1 only. |
| 24 V supply | Module 1 | HB-Laser feed | Put a switch on the mains lead. Keep it in reach. |

## 🧰 Setup

### Requirements

| Item | Version |
|---|---|
| Raspberry Pi OS Lite | 64-bit, Debian 13 Trixie |
| OLA | `ola` and `ola-python`, from apt |
| Python | System Python 3, plus a venv at `~/wj-venv` |
| pyrplidar | 0.10.9 |

### Steps

Run steps 1 to 4 and 6 on the Pi, over SSH.

1. **Install OLA and the LiDAR driver.**

   ```
   sudo apt update
   sudo apt install -y ola ola-python
   python3 -m venv ~/wj-venv
   ~/wj-venv/bin/pip install pyrplidar
   ```

2. **Let the venv see the system OLA package.** `ola-python` installs outside the venv. Edit
   `~/wj-venv/pyvenv.cfg` and set:

   ```
   include-system-site-packages = true
   ```

3. **Give the two USB devices fixed names.** Plugging the LiDAR in can move the Enttec from
   `ttyUSB0` to `ttyUSB1`. That breaks the show at random. Create
   `/etc/udev/rules.d/99-water-jets.rules` with one rule per device, matched on **serial
   number**, making `/dev/ttyLIDAR` and `/dev/ttyENTTEC`. Match on serial, not on chip ID.
   Another device with the same FTDI chip will otherwise steal the name.

4. **Restrict OLA to the Enttec.** Edit `/etc/ola/ola-usbserial.conf` and set a single
   `device_prefix = ttyENTTEC`. Then set `enabled = false` in every other `/etc/ola/*.conf`.
   OLA's StageProfi plugin otherwise grabs the LiDAR's port every few seconds.

5. **Copy the code from the laptop.** Run this in Git Bash on the laptop.

   ```
   scp -r "C:/Users/garrett.reynolds/Projects/Personal/Electronics/water-jet-follower/tracker" pi@water-jets:~/
   ```

6. **Let the settings page reboot and shut down the Pi.** The **Reboot Pi** and **Shut down
   Pi** buttons on `/settings` run `sudo -n /usr/sbin/reboot` and `sudo -n /usr/sbin/poweroff`.
   Without this rule they are refused with "a password is required". Run
   `sudo visudo -f /etc/sudoers.d/water-jets` and make the file exactly this:

   ```
   pi ALL=(root) NOPASSWD: /usr/sbin/reboot, /usr/sbin/poweroff
   ```

   `visudo` sets the mode (0440) and checks the syntax. Nothing else gets passwordless sudo.
   Check it with `sudo -n /usr/sbin/reboot --help`, which must print help and not ask for a
   password.

### Verifying it worked

```
ssh pi@water-jets
cd ~ && ~/wj-venv/bin/python -m tracker.run check
```

Expect about 16 Hz and about 500 samples per scan. Under 400 samples per scan means the LiDAR is
not in Boost mode. Then run `~/wj-venv/bin/python -m tracker.run zero` and expect
`slots_held=512 ALL ZERO`.

### Gotchas

- **The software stop only works while the whole chain is alive.** Killing the tracker zeroes the
  jets. Killing `olad`, unplugging the interface or crashing the Pi does not. The modules hold
  their last value. Cut the 24 V.
- **OLA leaves stale lock files.** `/var/lock/LCK..ttyUSB*` holds a PID and survives a restart.
  When a recycled PID matches, `olad` refuses to open the port. Clear these at boot.
- **`pyrplidar` does not drain its serial buffer on stop.** It throws
  `PyRPlidarProtocolError: sync bytes are mismatched` on reconnect. The driver retries and
  flushes for this reason.
- **The control path uses ten measured points.** `strip_points` maps real person positions to
  jets 0 through 9. The tracker interpolates between adjacent points.
- **One DMX unit is 7.62 mm of jet height.** DMX 255 is about 1.94 m. Raise the cap in small
  steps and never as a guess.

## ⚡ Quickstart

```
ssh pi@water-jets
cd ~ && ~/wj-venv/bin/python -m tracker.run show --replay ~/data/crossing.jsonl --baseline ~/data/baseline.json --dry-run
cd ~ && ~/wj-venv/bin/python -m tracker.run show --baseline ~/data/baseline.json --lights-only
cd ~ && ~/wj-venv/bin/python -m tracker.run show --baseline ~/data/baseline.json
cd ~ && ~/wj-venv/bin/python -m tracker.run zero
```

The first line needs no hardware but the Pi. The second drives real DMX with every fountain
forced to zero, so nothing gets wet. The third moves water. The last is the stop.

## 🚨 Troubleshooting

| Symptom | Fix |
|---|---|
| Jets stay up after the software stops | Cut the 24 V. The modules latch and no software can clear them. |
| `zero` says `olad returned NO DATA` | The interface is unplugged. Check `ola_dev_info`, then cut the 24 V if anything is up. |
| `olad` will not open the port | Delete the stale `/var/lock/LCK..ttyUSB*` file and restart `olad`. |
| `PyRPlidarProtocolError: sync bytes are mismatched` | Unplug and replug the LiDAR. The driver flushes and retries on connect. |
| LiDAR resets when the motor starts | Move it onto the powered hub. The Pi's own ports cannot supply it. |
| Under 400 samples per scan | The LiDAR is not in Boost mode. Check `require_boost` in `config.py`. |
| `ModuleNotFoundError: No module named 'ola'` | Set `include-system-site-packages = true` in `~/wj-venv/pyvenv.cfg`. |
| Hills appear at the wrong jet | `strip_start` and `strip_end` are not calibrated. See step 1 of `NEXT_STEPS.md`. |

## 📁 Project structure

| Path | Holds |
|---|---|
| `tracker/` | Everything that runs. Import as a package. |
| `tracker/run.py` | The command line. `check`, `record`, `baseline`, `show`, `jog`, `zero`. |
| `tracker/config.py` | Every tunable number, with the measurement behind it. |
| `tracker/lidar.py` | The A2M8 driver. Connect with retry, flush, force Boost. |
| `tracker/tracking.py` | Clustering, leg pairing, Kalman tracking. |
| `tracker/wave.py` | Tracks in, one DMX frame out. |
| `tracker/dmx.py` | DMX out through `olad`, and the stop path. |
| `tracker/viewer.py` | The web page, served from the Pi. |
| `tracker/tests/` | 133 tests. Synthetic walkers, so no hardware is needed. |
| `bench/` | Throwaway LiDAR probe scripts from the sensor bring-up. |
| `data/` | Recorded scans and baselines. |
| `docs/` | The signal chain diagram and the agent docs. |

## 📚 Documentation

- [DECISIONS.md](DECISIONS.md) — every choice made, and why.
- [NEXT_STEPS.md](NEXT_STEPS.md) — the true state of play, and what to do next.
- [CONTEXT.md](CONTEXT.md) — the glossary. Read this before the code.
- [docs/BUILD_SPEC.md](docs/BUILD_SPEC.md) — the final 20-jet build specification.
- [tracker/README.md](tracker/README.md) — running the tracker, the show, and the first power-up.
- [docs/water-jet-follower.html](docs/water-jet-follower.html) — the signal chain, interactive.

<!-- create-readme v0.2.4 -->
