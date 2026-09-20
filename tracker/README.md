# tracker

Finds people in the RPLIDAR A2M8 scan and follows them, in plain Python with no
dependencies beyond `pyrplidar`. This is step 1 and step 2 of `NEXT_STEPS.md`. It
It also drives the water: `show` is the installation, `jog` is the hand-driven
tool for a first power-up, and `zero` is the stop.

## What is in here

| File | Does |
|---|---|
| `config.py` | every tunable number, in one place |
| `lidar.py` | the A2M8: connect with retry, flush the buffer, force Boost mode |
| `scanfile.py` | record scans to a file, play them back, build the empty-room baseline |
| `geometry.py` | polar scan to world x/y, background subtraction, position to jet number |
| `tracking.py` | cluster, pair legs, follow people with a constant-velocity Kalman filter |
| `merge.py` | two one-person clips into one two-person clip, by nearest return per ray |
| `dmx.py` | DMX out through olad; always full 512-slot frames, and the zero path |
| `wave.py` | tracks in, one DMX frame out: hills, colour by speed, attract |
| `viewer.py` | web page served from the Pi, because Pi OS Lite has no window |
| `settings.py` | versioned profiles, validation, undo, and safe operator actions |
| `run.py` | the command line |
| `tests/` | synthetic walkers, so the maths can be checked with nobody in the room |

Parameter names copied from `angusleigh/leg_tracker` keep that project's spelling.
It is a reference for the algorithm, not a dependency — it targets ROS 1 Noetic,
which is end of life.

## Put it on the Pi

On the laptop, in Git Bash:

```
scp -r "C:/Users/garrett.reynolds/Projects/Personal/Electronics/water-jet-follower/tracker" pi@water-jets:~/
```

## Use it on the Pi

Everything runs from the home directory, in the venv:

```
ssh pi@water-jets
cd ~
```

**1. Is the LiDAR alive and in Boost mode?**

```
~/wj-venv/bin/python -m tracker.run check
```

Expect about 16 Hz and about 500 samples per scan at the default PWM 800. Under 400
samples per scan means it is not in Boost, and the whole approach fails at that
resolution.

**2. Record the room, then build the baseline.**

The baseline is what stops the walls and the basin from looking like people. It does
**not** need an empty room. Clutter is exactly what it is for, and you can be in the
room while it records — just **keep moving and do not stand still**.

```
~/wj-venv/bin/python -m tracker.run record --seconds 60 --out data/room.jsonl --notes "the room, me walking about"
~/wj-venv/bin/python -m tracker.run baseline --scan data/room.jsonl --out data/baseline.json
```

Why moving works: for each bearing the baseline takes the 35th-nearest-percent of
what it saw, not the nearest. Somebody walking normally sits on any one bearing for
about 12% of a clip, so they fall below that line and never become part of the room.
Standing still on one spot for a third of the clip **would** bake you in, which is
why the clip is 60 s and why you keep walking.

**Check it worked** — replay the same clip through the tracker and read the
**`moving points per scan`** line. You were walking in that clip, so you should still
show up as moving:

```
~/wj-venv/bin/python -m tracker.run offline data/room.jsonl --baseline data/baseline.json
```

| `moving points per scan` | Means |
|---|---|
| **over 10** | good — you are still visible, the room is not |
| **under 3** | you were absorbed into the baseline |
| **over 80** | the baseline is not doing its job at all |

Measured on a still bench for scale: 0.6 to 0.9 with a baseline, 118.8 with none.

If you were absorbed, record again and keep moving, or raise the line with
`--percentile 0.5`.

Read this line, not the track count. A still room can still throw the odd ghost
track; the points figure is the direct measure and does not go through the tracker's
confirmation rules.

**3. Record yourself walking. One person is enough — see "Two people, on your own".**

Walk your line, past the whole strip and out the far end.

```
~/wj-venv/bin/python -m tracker.run record --seconds 30 --out data/walk-left-right.jsonl --notes "one person, left to right"
~/wj-venv/bin/python -m tracker.run record --seconds 30 --out data/walk-right-left.jsonl --notes "one person, right to left"
```

**4. Record yourself standing still.** This one answers #12 items 6 and 7 on its own.

Stand 10 seconds at each of three spots, measured along the strip from the LiDAR:
**0.2 m, then 0.6 m, then 1.0 m**. Stand beside the strip, on the same line you
walked, not on top of it. Count the seconds out loud so the clip can be read later.

```
~/wj-venv/bin/python -m tracker.run record --seconds 40 --out data/standing.jsonl --notes "10s each at 0.2m, 0.6m, 1.0m along the strip"
```

**5. Watch it live, any time.**

```
~/wj-venv/bin/python -m tracker.run live --baseline data/baseline.json
```

Open `http://water-jets:8080/` on a laptop. Green dot = a confirmed
person. Grey = a new track that is not confirmed yet. Red = a track coasting
through an occlusion. Orange rings = leg clusters. Blue dots = moving points, dark
grey = the room.

**6. Replay a recording, as many times as you like.**

```
~/wj-venv/bin/python -m tracker.run replay data/walk-left-right.jsonl --baseline data/baseline.json --loop
```

Or with no viewer, just a count:

```
~/wj-venv/bin/python -m tracker.run offline data/walk-left-right.jsonl --baseline data/baseline.json
```

## Two people, on your own

Issue #12 asks whether one LiDAR survives two walkers crossing. That needs two
people **in the data**, not two people in the room.

A 2D LiDAR reports only the nearest thing on each ray. So take your left-to-right
clip and your right-to-left clip, and on every ray keep whichever return is nearer.
The result is exactly the scan the sensor would have made with both walkers there,
shadows and all — because a nearer body wins the ray, which is the same rule the
hardware uses. A unit test proves it: merging two one-person clips gives a scan that
matches a real two-person one point for point. (Real angles jitter, so two returns
less than half a ray apart compete for one slot. That is inside the sensor's own
resolution.)

```
~/wj-venv/bin/python -m tracker.run merge data/walk-left-right.jsonl data/walk-right-left.jsonl --shift-b 4.0 --out data/crossing-4s.jsonl
~/wj-venv/bin/python -m tracker.run replay data/crossing-4s.jsonl --baseline data/baseline.json --loop
```

`--shift-b` slides the second clip in time, which is what decides **where** the two
walkers meet. That one pair of recordings gives the whole sweep:

| `--shift-b` | What it tests |
|---|---|
| tuned so they cross close to the sensor | worst case — the biggest shadow |
| tuned so they cross at the far end | mildest case |
| large, so they never meet | the control — two tracks, no interaction |

`merge` prints the closest approach and when it happens, so you can aim the shift
instead of guessing. Try a few values and watch the viewer.

**What this cannot do:** the two recorded people never react to each other — no
stepping aside, no slowing down. The ticket asks about the sensor, not about
manners, so that is a fair trade. It is worth one real two-person recording later
if a second person ever turns up.

## Build each clip's baseline from that clip

A baseline goes stale the moment anything in the room moves. Measured 2026-09-04: a
room baseline recorded minutes before a walk gave **8 confirmed people, four of them
permanent**, because things had shifted. The same walk scored against **its own**
baseline gave **1**.

So for any clip with somebody walking in it, do this:

```
~/wj-venv/bin/python -m tracker.run baseline --scan data/walk-left-right.jsonl --out data/base-lr.json
~/wj-venv/bin/python -m tracker.run offline data/walk-left-right.jsonl --baseline data/base-lr.json
```

This is only legal because the baseline is a percentile, not a minimum — a walker
holds any one bearing for well under 35% of a clip, so he does not end up in his own
baseline.

**Never build a baseline from a clip in which anybody stands still.** Score standing
clips against a walking clip's baseline instead:

```
~/wj-venv/bin/python -m tracker.run offline data/standing.jsonl --baseline data/base-rl.json
```

Raising `--percentile` does **not** rescue this, and it is worth knowing why. If there
is open space behind the person, their body is the only thing that bearing ever sees.
The percentile of a list containing nothing but their own returns is their own
distance, at any percentile. Measured 2026-09-04: a third standing spot vanished
entirely from its own baseline at 0.35, 0.5 and 0.6 alike, and came back at 100%
coverage against a walking clip's baseline.

## Lining the sensor up

The world frame puts the LiDAR at `(0, 0)`, `+x` along the strip and `+y` across the
hallway. If the scan comes out rotated or mirrored in the viewer, change
`mount_angle_offset_deg` and `mirror` in `config.py`. There is no way to get these
right on paper; look at the picture.

`roi_x_min` is `0.00`, so **the sensor is blind behind itself**. That is on purpose:
clutter beside the LiDAR on the bench held a false person for a whole recording.
Raise the region of interest again only with a longer empty-room baseline.

## Tests

On the laptop, in Git Bash:

```
cd "C:/Users/garrett.reynolds/Projects/Personal/Electronics/water-jet-follower" && python -m unittest discover -s tracker/tests -t .
```

They use fake scans with real ray occlusion. They prove the maths, not the hardware.
Only recordings of the real room answer issue #12.

## Known, and not fixed here

- `~/wj-venv` has `include-system-site-packages = false`, so `import ola` fails
  inside it. That blocks DMX output, which is the next piece, not this one.

## Driving the water modules, the first time

The jets have never been commanded. Do this in order and do not skip ahead.

**Before anything: have a hand on the mains switch of the 24 V supply.** It is the
only stop that does not depend on software. Everything below is layers on top of it.

**1. Find the modules and their DMX addresses.**

```
ssh pi@water-jets
ola_rdm_discover -u 1
```

The modules auto-address, so they may not start at 1. RDM discovery answers that and
also settles whether they speak standard E1.20 at all — an open question in
`NEXT_STEPS.md`. It reads; it does not set levels.

**2. Prove the stop works, on an LED, before touching a pump.**

Channel 1 is nozzle 1's **red LED**. Channels 1 to 4 are colour and only channel 5 is
the pump, so the whole DMX path can be proven with light instead of water.

```
~/wj-venv/bin/python -m tracker.run jog --channel 1 --max 40
```

ENTER steps up by 5, `-` steps down, a number jumps to it, `q` quits. The red LED on
nozzle 1 should come up. There are then two different failures to check, and they are
not the same test.

**2a. The client dies.** Bring the LED to 40. From a second terminal:

```
ssh pi@water-jets "pkill -HUP -f 'tracker.run jog'"
```

The LED should go out. This is the path already proven at the olad level on channel
512; 2a only confirms a real fixture follows it.

**2b. `olad` itself dies.** This is the one nothing has tested, and it is the failure
that decides whether the software stops are worth anything. Bring the LED to 40, then:

```
sudo systemctl stop olad
```

Watch the LED. If it goes out, DMX signal loss turns the modules off. **If it stays
lit**, either the modules latch on signal loss or the Enttec Pro Mk2's onboard frame
buffer keeps repeating the last frame — it was chosen for that buffer — and in that
case the mains switch is the only thing that covers an `olad` crash. Either answer is
worth knowing before a pump runs. Then:

```
sudo systemctl start olad
~/wj-venv/bin/python -m tracker.run zero
```

**3. Only then, the pump.** Channel 5 is nozzle 1's fountain height.

```
~/wj-venv/bin/python -m tracker.run jog --channel 5 --max 40
```

`--max 40` is a deliberate ceiling. The datasheet range is 5 cm to 1.5 m and the
mapping from DMX value to height is RDM-calibrated and unread, so a middle value may
already be a tall jet. Raise `--max` on purpose, a little at a time, never as a guess.

Watch the water level as well as the jet. A 24 in x 16 in basin at 9 cm has only about
2 L above the module's 8 cm minimum, so splash-out is the limit long before the jet is.

**Layer (b), the stop you keep in a second terminal:**

```
ssh pi@water-jets "cd ~ && ~/wj-venv/bin/python -m tracker.run zero"
```

It drives all 512 slots to zero and then reads the universe back to prove it, rather
than printing "sent" and hoping. Short to type on purpose — a 512-value
`ola_set_dmx` string is exactly the paste Git Bash mangles.

## Running the show

`tracker.run show` is the installation: LiDAR in, people tracked, hills of water
following them, colour by speed. Three ways to run it, and they are meant to be used
in this order.

**1. Dry run.** No DMX at all. Watch it in the browser against a recorded walk.

```
ssh pi@water-jets
cd ~ && ~/wj-venv/bin/python -m tracker.run show --replay ~/data/crossing.jsonl --baseline ~/data/baseline.json --dry-run
```

**2. Lights only.** Real DMX, but every fountain channel is forced to zero. The pixels
chase a walker and **nothing gets wet.** This is how the whole behaviour gets watched
on real hardware before any water moves.

```
cd ~ && ~/wj-venv/bin/python -m tracker.run show --baseline ~/data/baseline.json --lights-only
```

**3. The real thing.** Water moves.

```
cd ~ && ~/wj-venv/bin/python -m tracker.run show --baseline ~/data/baseline.json
```

Add `--attract` to roll a hill when nobody is there. **It is off by default and should
stay off** until there is a contactor on the 24 V that a watchdog can drop — attract
runs with nobody watching, and the modules latch.

### Browser settings

While `show` is running, open `http://water-jets:8080/settings`. Edits go live on their own,
about a quarter of a second after the last change, as one complete versioned profile. Three
things wait for **Apply profile** because they are big jumps: the hard maximum (unlock it first),
**Load JSON**, and **Reset defaults**. Live-apply never touches the hard maximum. **Undo applied**
steps back one edit burst, up to 50. Lights-only always forces the water channel to zero. **Save JSON** downloads the profile to
the browser computer; **Load JSON** previews a saved profile before apply. The layout map draws
the live LiDAR scan behind the editable path. Use the mouse wheel or the `−`, **Fit**, and `+`
buttons to zoom around the selected path point.

**ALL OFF**, **Apply profile**, **Lights only**, and the status line sit in a bar that stays
on screen however far the page is scrolled. **ALL OFF** zeroes every slot *and halts the live
show*. Without the halt, the next scan put the hill straight back and the button looked dead.
The bar shows a banner while the show is halted; press **Resume live show** to continue. Every
height slider shows its DMX value and the matching centimetres (0.762 cm per unit).

### Test page

`http://water-jets:8080/test` is the testing area. Opening it enters **test mode**: the output is
zeroed and the live show stops sending. Tracking keeps running, so the page shows which jet the
tracker thinks you are standing on (numbered from 1, like the settings map). Nothing a walker
does can put water up while test mode is on.

**Start test** holds one selected jet at one selected height. Keep a hand on the 24 V switch.
**Stop test** sends zero and verifies that all 512 DMX slots are zero. A jet test is rejected
outside test mode and while lights-only mode is on. **Resume live show** zeroes first, then hands
the output back to the show. Closing the page does *not* resume the show; only that button does,
so a dropped tablet cannot restart the water. The console line reads `TEST` while test mode is on.

### The height cap

`--height-max` is a hard ceiling applied to every fountain channel as the last step
before a frame goes out, in `dmx.clamp_heights`. It holds even if the wave logic is
wrong. Default 40.

**1 DMX unit is 7.62 mm**, measured on the bench. So:

| DMX | Height |
|---|---|
| 15 | 11 cm — the attract height |
| 30 | 23 cm — what a hill aims for |
| 40 | **30 cm — the cap, and the tallest ever run** |
| 255 | 194 cm — do not |

Raise it deliberately and in small steps. The modules **latch their last value forever**
when DMX stops, so a height written once by mistake stays up until the 24 V is cut.

### Stopping it

`show` and `jog` both run inside `dmx.safe_output`, which zeroes the line on the way in
and on the way out — on Ctrl-C, on `kill`, and on SIGHUP when the ssh session drops.
That path was tested on hardware with a real LED.

**It does not save you if `olad` dies, the interface is unplugged, or the process is
SIGKILLed.** All three were tested and the modules held their value. The only stop that
covers those is the switch on the 24 V supply. Keep a hand on it.

**If the LiDAR USB comes out, `show` keeps running.** It zeroes the water once, stops the
watchdog beat, and every page says "LiDAR not available" until the plug is back. Then it
reconnects and tracks again. Proven on the Pi 2026-09-20. `record`, `live`, and `check` do not
do this; they fail loudly, which is what you want from a recording.

### Aiming it at the real strip

`config.py` holds ten measured LiDAR x/y control-path points for the bench profile. The settings
screen makes one movable control point per jet. Raising the jet count fills the new points across
the current path, so the operator can then move every jet point.
The tracker draws a joined path through those points and interpolates between adjacent jets.
The large viewer panel shows x, y, and the mapped jet number. Garrett verified the live viewer
map, light aim, and water aim for jets 0 through 9 on 2026-09-19. The live water test peaked at
DMX 30 and stopped with all 512 DMX slots at zero. The final build uses all 20 jets. Jets 10
through 19 still need measured points and the same bench check.
