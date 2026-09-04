# Walker sensing methods along a 1 m strip

Resolves GitHub issue #5.

> **Salvage note.** This document was written on 2026-09-04 from a recovered dump of a killed
> research agent's fetched pages (`sensing.txt`). No new fetching was done. Coverage is therefore
> uneven: some datasheets parsed cleanly, several returned 404 or unreadable binary PDF, and most
> Canadian supplier pages were blocked or returned the wrong product. Every number below is
> attributed to the URL the dead agent fetched it from. Where the dump has nothing, the row says
> **not in recovered sources** rather than a guess.

## Summary

- Only three recovered options report *per-target lateral position*, which is what "two people at
  once, crossing" actually requires: HLK-LD2450 radar (3 targets, x/y/speed, 10 Hz), Seeed MR60BHA2
  radar (3 targets, x/y), and multi-zone ToF arrays / depth cameras (a map, targets separated in
  software).
- The DFRobot C4001 that Garrett already knows outputs **distance and speed only, no angle or x/y**
  ([DFRobot wiki](https://wiki.dfrobot.com/sen0610/docs/20949)) — it cannot satisfy constraint 1.
- Update rate is the second gate. Derived from the dump's usual walking pace of 1.31 m/s: a walker
  crosses one 50 mm jet pitch every ~38 ms, so ~26 Hz is the rate at which the wave lands within one
  jet. The LD2450's 10 Hz is ~2.6 jet pitches per frame; a VL53L5CX 8×8 at 15 Hz is ~1.7.
- Break-beam is out on range alone (~50 cm emitter-to-receiver vs a ~3 m hallway).
- **Water spray is the largest gap: the dump contains nothing on spray or humidity for any sensor.**

---

## 1. Single-point ToF — ST VL53L1X

A row of these along the strip, each looking across the hallway; walker position = which sensor sees
a short return.

| Spec | Value | Source |
|---|---|---|
| Max range | 4 m, long distance mode | [ST datasheet DocID031281 Rev 3, Nov 2018](https://www.pololu.com/file/0J1506/vl53l1x.pdf) |
| Max range vs ambient (Table 4) | short 136 cm dark / 135 cm ambient; medium 290 / 76; long 360 / 73 | same |
| Table 4 test conditions | "timing budget = 100 ms, white target 88 %, dark = no IR ambient, ambient light = 200 kcps/SPAD" | same |
| Ranging frequency | "Up to 50 Hz ranging frequency" | same |
| Carrier's rate breakdown | up to 30 Hz medium/long modes; 50 Hz max in short mode | [Pololu #3415](https://www.pololu.com/product/3415) |
| Timing budget | 20 ms min (short mode only); 33 ms min for all modes; 140 ms to reach 4 m in long mode | ST datasheet, above |
| Field of view | "Typical full field-of-view (FoV): 27 °"; receiver diagonal FoV "Programmable from 15 to 27 degrees" | ST datasheet, above |
| ROI | programmable from 4×4 SPADs (minimum) up to 16×16 SPADs (full FoV) | ST datasheet, above |
| Interface | I²C up to 400 kHz; 7-bit address, default `0101001b` | ST datasheet / [Pololu #3415](https://www.pololu.com/product/3415) |
| Many on one bus | via XSHUT — bring each out of reset individually and assign a unique address | [Pololu #3415](https://www.pololu.com/product/3415) |
| Multi-target | not in recovered sources for VL53L1X (the sibling VL53L4CX is described as "multiobject detection… tell you the two distances", [Adafruit 5425 page content](https://www.adafruit.com/product/5425)) |
| Ambient light | long distance mode "maximum range is significantly affected by ambient light"; short distance mode "mostly immune to ambient light interference" | [Pololu #3415](https://www.pololu.com/product/3415) |
| Water spray | not in recovered sources | — |
| Price | USD $22.95 (Pololu #3415 carrier) — [Pololu](https://www.pololu.com/product/3415); CAD $35.00, DigiKey 497-18088-ND, 95 in stock, for the ST **VL53L1X-SATEL** eval board — [digikey.ca](https://www.digikey.ca/en/products/result?keywords=VL53L1X-SATEL) |

**What breaks it.** The 3 m hallway: under the datasheet's ambient-light test condition, medium and
long modes collapse to 76 cm and 73 cm — a sensor at one wall would not reach the other. Short mode
reaches 135 cm ambient, which covers roughly a person on the near side only. Two people crossing:
a row of point sensors gives position from *which* sensor fires, but the near walker occludes the
far one on the same beam line (inference, unsourced). Cost and wiring scale with sensor count — one
per 50 mm jet over 1 m is 20 sensors, each needing an XSHUT line.

## 2. Single-point ToF — Benewake TF-Luna

| Spec | Value | Source |
|---|---|---|
| Operating range | "0.2m~8m(90%reflectivity indoor 0klux)" | [TF-Luna datasheet PDF](https://en.benewake.com/uploadfiles/2024/04/20240426135921367.pdf) |
| Range (product page) | "0.2 ~ 8 m" | [Benewake TF-Luna page](https://en.benewake.com/TFLuna/index.html) |
| Accuracy | "± 6 cm @ (0.2 ~ 3 m)"; ±2% @ 3–8 m | product page / datasheet PDF |
| Distance resolution | 1 cm | [product page](https://en.benewake.com/TFLuna/index.html) |
| Frame rate | "1 ~ 250 Hz" (page); datasheet note 4: "The Highest frame rate is 250Hz, the default frame rate is 100Hz" | product page / datasheet PDF |
| Field of view | 2° (extract read "FOV 2°5" — the 5 is a footnote marker, garbled by the text extractor) | datasheet PDF |
| Ambient light | 70 Klux | datasheet PDF |
| Wavelength | 850 nm | datasheet PDF |
| Supply | 3.7 V – 5.2 V; ≤ 0.35 W | datasheet PDF / product page |
| Interface | UART, I²C, I/O; I²C address range 0x08~0x77 | datasheet PDF |
| Size / weight | 35 × 21.25 × 13.5 mm, < 5 g | product page |
| Multi-target | not in recovered sources | — |
| Water spray | not in recovered sources (a separate "TF-Luna (underwater)" datasheet exists in Benewake's download list but was not fetched) | [Benewake download centre](https://en.benewake.com/DataDownload/index.aspx?pid=20&lcid=21) |
| Canadian price | **not in recovered sources** — digikey.ca returned "'TF-Luna' did not return any results"; the mouser.ca fetch came back with DigiKey content | — |

**What breaks it.** The 2° beam is a pencil, not a curtain: it sees a walker only when the walker is
in that one line, so you need many of them or a scan. 250 Hz is far more than needed but the default
is 100 Hz. No Canadian source was recovered, which is a real procurement problem.

## 3. Single-point ToF — Benewake TFmini

**Not in recovered sources.** Only a datasheet URL appeared, in a search result list
(`https://cdn.sparkfun.com/assets/5/e/4/7/b/benewake-tfmini-datasheet.pdf`); it was never fetched.
No range, rate, FoV or price recovered.

## 4. Multi-zone ToF array — ST VL53L5CX

A ceiling- or soffit-mounted 8×8 grid looking down at the strip; each zone is a distance, so a
person shows as a short-range blob whose column index is their position along the strip.

| Spec | Value | Source |
|---|---|---|
| Zones | 4×4 or 8×8, configurable | [Pololu #3417](https://www.pololu.com/product/3417) / [SparkFun 18642](https://www.sparkfun.com/products/18642) |
| Max ranging frequency | "60 Hz" max for the part | [Pololu #3417](https://www.pololu.com/product/3417) |
| Rate by zone count | "60Hz at 4x4 and 15Hz at 8x8" for VL53L5CXV0GC/1 — **from a WebSearch summary of ST datasheet DS13754, not from the datasheet itself** ([st.com/resource/en/datasheet/vl53l5cx.pdf](https://www.st.com/resource/en/datasheet/vl53l5cx.pdf) — every direct fetch of this PDF failed to parse) | WebSearch result in dump |
| Rate (SparkFun wording) | "60 Hz frame rate capability", though it "can also operate at speeds up to 15Hz when measuring across all zones" | [SparkFun 18642](https://www.sparkfun.com/products/18642) |
| Field of view | "65° diagonal (45° horizontal/vertical)" (Pololu); "63 ° diagonal square FoV using diffractive optical elements (DOE)" (SparkFun) | both, above |
| Max range | 4 m (13 ft) under favourable conditions / "up to 4000mm" across all zones | both, above |
| Multi-target | yes — "separate readings for each zone (which can include multiple targets per zone)" | [Pololu #3417](https://www.pololu.com/product/3417) |
| Interface | I²C, fast mode plus (1 MHz); SparkFun board is I²C-only at address 0x52 | both, above |
| Ambient light | FlightSense measures time-of-flight, so readings are "independent of ambient lighting conditions"; SparkFun notes "immunity to crosstalk from cover glass (beyond 60cm)" | both, above |
| Water spray | not in recovered sources | — |
| Price | USD $19.95 (Pololu #3417, $18.35 @ qty 5); USD $32.50 (SparkFun 18642, $30.88 @ 10+); **CAD $35.47**, DigiKey 497-VL53L5CX-SATEL-ND, 459 in stock, for the ST eval board — [digikey.ca](https://www.digikey.ca/en/products/result?keywords=VL53L5CX-SATEL) |

**Derived geometry** (arithmetic from the quoted 45° per-axis FoV, not a sourced number): footprint
along one axis ≈ 2·h·tan(22.5°) = 0.83·h. To cover the full 1 m strip the sensor sits ~1.2 m above
it; 8 zones across 1 m is 125 mm per zone ≈ 2.5 jet pitches. Two sensors, or a lower mount covering
half the strip each, buys back resolution.

**What breaks it.** Zone size, not update rate, is the limit: 8 zones over 1 m cannot resolve a
50 mm jet without interpolating the blob centroid across zones. At 8×8 the rate drops to ~15 Hz
(≈87 mm of walker travel per frame at 1.31 m/s). Two people at once is workable — the zone map
shows two blobs, and they separate again after a crossing — but the dump contains no measured
two-person test.

## 5. Multi-zone ToF array — ST VL53L8CX

| Spec | Value | Source |
|---|---|---|
| Zones | 4×4 or 8×8 | [Pololu #3419](https://www.pololu.com/product/3419) |
| Max update rate | "a maximum update rate of 60 Hz is mentioned in the comparison table"; the page does **not** split 4×4 vs 8×8 | [Pololu #3419](https://www.pololu.com/product/3419) |
| Field of view | "65° diagonal (45° horizontal/vertical)" | [Pololu #3419](https://www.pololu.com/product/3419) |
| Max range | 4 m (13 ft) ideal; ~2.8 m in 5000 lux — "a large reflective target up to 2.8 m (9.2 ft) away" | [Pololu #3419](https://www.pololu.com/product/3419) |
| Interface | I²C up to 1 MHz; SPI up to 3 MHz (min ~1.1 MHz for reliable initialization) | [Pololu #3419](https://www.pololu.com/product/3419) |
| Positioning vs L5CX | "enhances performance under ambient light with reduced power consumption… accurate ranging up to 400 cm with a 65° diagonal FoV"; "supports SPI and I²C interfaces for high frequency frame rates and short-boot times" | WebSearch summary of ST material in dump |
| Water spray | not in recovered sources | — |
| Price | USD $24.95 (Pololu #3419). **No CAD price** — digikey.ca: "'VL53L8CX-SATEL' did not return any results" | [Pololu #3419](https://www.pololu.com/product/3419) / [digikey.ca](https://www.digikey.ca/en/products/result?keywords=VL53L8CX-SATEL) |

**What breaks it.** Same zone-size limit as the L5CX. The 5000 lux figure is the useful one for a
lit hallway: max range drops from 4 m to 2.8 m, which still spans a 3 m hallway diagonal only
marginally. The 4×4-vs-8×8 rate split was never recovered — treat "60 Hz" as the 4×4 figure until
confirmed. SPI is the reason to prefer this part over the L5CX if frame rate turns out to be the
binding constraint.

## 6. mmWave radar — DFRobot C4001 (SEN0610 12 m / SEN0609 25 m)

| Spec | Value | Source |
|---|---|---|
| Frequency / modulation | 24 GHz, FMCW | [DFRobot wiki SEN0610](https://wiki.dfrobot.com/SKU_SEN0610_Gravity_C4001_mmWave_Presence_Sensor_12m_I2C_UART) |
| Presence range | 8 m | [dfrobot.com product-2795](https://www.dfrobot.com/product-2795.html) |
| Motion / ranging range | 12 m; distance measurement 1.2 m to 12 m | [dfrobot.com product-2795](https://www.dfrobot.com/product-2795.html) |
| Speed detection | "0.1m/s to 10m/s" | [dfrobot.com product-2795](https://www.dfrobot.com/product-2795.html) |
| Beam angle | "100*80°" (horizontal × vertical) | [DFRobot wiki SEN0610](https://wiki.dfrobot.com/SKU_SEN0610_Gravity_C4001_mmWave_Presence_Sensor_12m_I2C_UART) |
| **Output data** | detects "presence, slight movement, and motion of human body" and supports "Distance and velocity detection". **"No angle or x/y coordinate data is mentioned in the reference."** | [DFRobot wiki reference SEN0610/20949](https://wiki.dfrobot.com/sen0610/docs/20949) |
| Update / refresh rate | **not in recovered sources** — "No information about output refresh rate, detection delay, report period, or configurable response settings is included in this reference section" | [DFRobot wiki reference](https://wiki.dfrobot.com/sen0610/docs/20949) |
| Number of targets | **not in recovered sources** ("Maximum number of targets not specified") | [DFRobot wiki reference](https://wiki.dfrobot.com/sen0610/docs/20949) |
| Interface | I²C (0x2A/0x2B) and UART (9600 baud); Gravity PH2.0 | [dfrobot.com product-2795](https://www.dfrobot.com/product-2795.html) |
| Supply / size | 3.3 V/5 V; 22 × 30 mm; -40~85 ℃ | [dfrobot.com product-2795](https://www.dfrobot.com/product-2795.html) |
| Installation | "sensitive to the installation method" — top, bottom, horizontal and downward-tilted mounting documented | [DFRobot wiki reference](https://wiki.dfrobot.com/sen0610/docs/20949) |
| SEN0609 (25 m variant) | 100° horizontal, presence 16 m, motion/ranging 25 m | WebSearch summary of [wiki.dfrobot.com/SKU_SEN0609…](https://wiki.dfrobot.com/SKU_SEN0609_C4001_mmWave_Presence_Sensor_25m) |
| Metal | cannot detect through metal — metal reflects RF; nearby metal can also generate false reflections, a specific C4001 caution. Works through glass, drywall, wood, most plastics | Second Brain vault, `wiki/hardware/dfrobot-c4001-mmwave-radar.md` |
| Water spray | not in recovered sources | — |
| Price | USD $12.90 — [dfrobot.com](https://www.dfrobot.com/product-2795.html); **CAD $18.91**, DigiKey 23028644, "GRAVITY: MMWAVE C4001 24GHZ" — [digikey.ca](https://www.digikey.ca/en/products/result?keywords=SEN0610) |

**What breaks it for this job.** It gives you a distance and a speed for *the* target, with no
bearing and no per-target separation. Two people on opposite sides of the strip both sit inside the
100° beam and there is no recovered way to tell them apart or to know which side of the strip either
is on. Being FMCW it does hold a stationary person (unlike Doppler), which matters for the Hold
behaviour — but constraint 1 is not met. Prior project use (Coors ball dispenser) was
presence-gating, a single-zone question, not tracking.

## 7. mmWave radar — HLK-LD2450

The only recovered part that directly outputs what the strip needs: per-target x, y and speed.

| Spec | Value | Source |
|---|---|---|
| Targets | "the serial port output data contains up to three target"; single-target mode cmd 0x0080, multi-target 0x0090, **default is multi-target** | [LD2450 Serial Communication Protocol v1.03](https://make.net.za/wp-content/datasheets/HLK%20LD2450%20Serial%20Communication%20Protocol%20v1.03.pdf) |
| Report rate | "The data format reported by the radar is shown in the table below, **10 frames per second**" | same |
| Per-target fields | Target X coordinate (mm), Target Y coordinate (mm), Target speed (cm/s), Distance resolution (mm) — sign carried in the high bit | same, Table 9 / Table 10 |
| Worked example in the manual | X = −782 mm, Y = 1713 mm, speed = −16 cm/s, distance resolution = 320 mm | same |
| Detection range | "Longest detection range 6m" | [hlktech.net id=1157](https://www.hlktech.net/index.php?id=1157) |
| Angles | "Azimuth angle ±60°, pitch angle ±35°" | [hlktech.net id=1157](https://www.hlktech.net/index.php?id=1157) |
| Frequency / antenna | 24 GHz ISM, "one-transmitter-two-receiver microstrip antenna", FMCW | [hlktech.net id=1157](https://www.hlktech.net/index.php?id=1157) |
| Interface | serial TTL, "default baud rate of the serial port is 256000, 1 stop bit, no parity bit" | protocol PDF, above |
| Supply | module supply 5 V; IO output level 3.3 V | protocol PDF, above |
| Size | 15 mm × 44 mm | [hlktech.net id=1157](https://www.hlktech.net/index.php?id=1157) |
| Visualisation tool | shows "the real-time positions of up to three targets on a sector map, with distance, angle and speed information for each target" | protocol PDF, above |
| Water spray | not in recovered sources | — |
| Canadian price | **not in recovered sources.** A search for Canadian stock returned only retailer home pages (pishop.ca, robotshop.com/ca, creatroninc.com) with no confirmed listing; the digikey.ca "LD2450" fetch returned the catalogue homepage, not results | — |

**What breaks it.** 10 Hz is the weak point: at the dump's usual 1.31 m/s pace that is 131 mm of
travel per frame, ≈2.6 jet pitches, so the wave will need prediction between frames (the reported
per-target speed makes that straightforward — extrapolate x by v·Δt). Three targets is a hard
ceiling. It is a wall-mounted room-tracking sensor, not a strip sensor, so mounting geometry has to
map its x/y into position-along-strip. The ESPHome `ld2450` component page was 404 in the dump, so
its reported update behaviour is unconfirmed.

## 8. mmWave radar — Seeed MR60BHA2 / MR60FDA2

| Spec | MR60BHA2 | MR60FDA2 |
|---|---|---|
| Outputs | breathing and heart rate, presence, distance, phase, **target position (x and y coordinates in meters)**, target velocity via Doppler index calculated as cm/s | fall detection status, human presence, and coordinates via `getHuman()` / `getFall()` |
| Range | breathing/heartbeat up to 1.5 m; static presence up to 6 m | "Human Static Presence Detection: up to 6 Meters"; fall detection covers "3x3x3 meter range" |
| Targets | "Up to 3 individuals simultaneously" | not stated in the recovered page |
| Field of view | not in recovered sources | "Horizontal Field of View (FoV) of 120°" and "Vertical FoV of 100°" |
| Mounting | not in recovered sources | ceiling: "Top-mounted hanging height 2.2-3.0m, maximum sensing radius 2m" |
| Refresh rate | "Not explicitly specified"; firmware v1.6.12 notes "reporting refresh rate has decreased" after optimization | not in recovered sources |
| Interface | serial to a Seeed XIAO ESP32C6 | serial to a Seeed XIAO ESP32C6, 1 GPIO, WS2812 LED |
| Price | not in recovered sources | "Not displayed in the documentation provided" |

Sources: [MR60BHA2 wiki](https://wiki.seeedstudio.com/getting_started_with_mr60bha2_mmwave_kit/),
[MR60FDA2 wiki](https://wiki.seeedstudio.com/getting_started_with_mr60fda2_mmwave_kit/).

**What breaks it.** No refresh rate was recovered for either part, which is disqualifying until
checked — the BHA2's own release notes say the reporting rate *decreased*. The FDA2's 2 m sensing
radius at ceiling height is tight for a 3 m hallway. Both are sold as kits tied to a XIAO ESP32C6
rather than as bare modules.

## 9. Depth camera — Luxonis OAK-D Lite

| Spec | Value | Source |
|---|---|---|
| Stereo sensors | OV7251 mono pair, 640 × 480 px | [Luxonis docs](https://docs.luxonis.com/hardware/products/OAK-D%20Lite) / WebSearch summary of Luxonis material |
| Stereo FoV | "DFOV / HFOV / VFOV: 86° / 73° / 58°" | [Luxonis docs](https://docs.luxonis.com/hardware/products/OAK-D%20Lite) |
| Ideal depth range | "~80cm - 12m"; MinZ ~20 cm with 400P extended disparity, ~35 cm at 480P | [Luxonis docs](https://docs.luxonis.com/hardware/products/OAK-D%20Lite) |
| Depth accuracy | below 2% error (<4 m); 4–6% error (4–10 m) | [Luxonis docs](https://docs.luxonis.com/hardware/products/OAK-D%20Lite) |
| **Depth frame rate** | **not in recovered sources** — two separate fetches of the Luxonis page both reported depth FPS "not explicitly specified" | [Luxonis docs](https://docs.luxonis.com/hardware/products/OAK-D%20Lite) |
| Baseline | the docs state **"75cm"** / "750mm (75cm)" in both fetches. Flagged: this is not plausible for a handheld camera, but nothing in the dump resolves it — do not design around it | [Luxonis docs](https://docs.luxonis.com/hardware/products/OAK-D%20Lite) |
| On-device AI | "4 TOPS of processing power (1.4 TOPS for AI)"; "Run any AI model, even custom-architected/built ones" | [Luxonis docs](https://docs.luxonis.com/hardware/products/OAK-D%20Lite) |
| RGB | IMX214, 4208 × 3120; RVC2 encoding 4K/30FPS, 1080P/60FPS | [Luxonis docs](https://docs.luxonis.com/hardware/products/OAK-D%20Lite) |
| Interface / power | "USB 2/3 (up to 10 Gbps)"; USB-C, up to 5 W | [Luxonis docs](https://docs.luxonis.com/hardware/products/OAK-D%20Lite) / WebSearch summary |
| Water spray | not in recovered sources | — |
| Price | **not in recovered sources** — the robotshop.ca product fetch returned other content and digikey.ca returned "no results" for OAK-D-Lite | — |

**What breaks it.** Two people crossing is the case a depth camera handles best (blob tracking with
identity through a crossing, or a person-detection model on the 1.4 TOPS VPU), but the missing depth
FPS number is exactly the spec constraint 2 turns on. It also needs a host and real vision code,
which is a much larger control-path than a serial radar.

## 10. Depth camera — Intel RealSense D435

| Spec | Value | Source |
|---|---|---|
| Depth technology | "Stereoscopic" (Intel spec page: "Active Stereoscopic") | [realsenseai.com D435](https://www.realsenseai.com/products/stereo-depth-camera-d435/) / [intel.com SKU 128255](https://www.intel.com/content/www/us/en/products/sku/128255/intel-realsense-depth-camera-d435/specifications.html) |
| Depth FoV | "87° × 58°" (Intel spec page states "85.2 x 58") | both, above |
| Depth resolution | "Up to 1280 × 720" | both, above |
| Max frame rate | "Up to 90 fps" | [realsenseai.com D435](https://www.realsenseai.com/products/stereo-depth-camera-d435/) |
| Ideal range | ".3 m to 3 m" | both, above |
| Min depth at max resolution | ~28 cm; depth accuracy under 2% at 2 m | [realsenseai.com D435](https://www.realsenseai.com/products/stereo-depth-camera-d435/) |
| RGB | "1920 × 1080 at 30 fps" | [realsenseai.com D435](https://www.realsenseai.com/products/stereo-depth-camera-d435/) |
| Shutter | global shutter sensor, "ideal for low-light environments and fast-moving applications" | [realsenseai.com D435](https://www.realsenseai.com/products/stereo-depth-camera-d435/) |
| Interface | "USB-C 3.1 Gen 1" (Intel spec page: USB 3.0 Type C) | both, above |
| IR projector | not in recovered sources | — |
| Water spray | not in recovered sources | — |
| Price | **CAD $554.63**, 327 in stock, 14-week manufacturer lead time — but the listing is the **D435i** (IMU variant), from one of the digikey.ca fetches in the dump. Result ordering in the dump is ambiguous; treat as approximate | [digikey.ca](https://www.digikey.ca/en/products/result?keywords=D435) |

**What breaks it.** Nothing technical: 90 fps depth and a 0.3–3 m ideal range fit a 3 m hallway
almost exactly. Price and lead time are the problem — roughly 30× a radar module, with a 14-week
quoted lead time.

## 11. Overhead camera — Raspberry Pi Camera Module 3

Plain 2D camera looking down at the strip; walker position from blob or person detection on a host.

| Spec | Value | Source |
|---|---|---|
| Sensor | Sony IMX708, back-illuminated stacked CMOS, 12 MP; 4608 × 2592 (11.9 MP) | [raspberrypi.com camera docs](https://www.raspberrypi.com/documentation/accessories/camera.html) / [product brief RP-008151-DS](https://pip-assets.raspberrypi.com/categories/786-raspberry-pi-camera-module-3/documents/RP-008151-DS-1-camera-module-3-product-brief.pdf) |
| Video modes | "2304 × 1296p56, 2304 × 1296p30 HDR, 1536 × 864p120" | [raspberrypi.com camera docs](https://www.raspberrypi.com/documentation/accessories/camera.html) |
| Video modes (retailer) | "1080p50, 720p100, 480p120" — **differs from the Raspberry Pi docs above; not reconciled here** | [pishop.ca](https://www.pishop.ca/product/raspberry-pi-camera-module-3/) |
| FoV, standard | diagonal 75°, horizontal 66°, vertical 41°; focal length 4.74 mm, F1.8, focus 10 cm–∞ | product brief RP-008151-DS |
| FoV, wide | diagonal 120°, horizontal 102°, vertical 67°; 2.75 mm, F2.2, focus 5 cm–∞ | product brief RP-008151-DS |
| Autofocus | phase detection autofocus (PDAF) | [raspberrypi.com camera docs](https://www.raspberrypi.com/documentation/accessories/camera.html) |
| Interface | CSI — 15-pin standard connector on Pi 4 and earlier, 22-pin mini connector on Pi 5 and Zero | [raspberrypi.com camera docs](https://www.raspberrypi.com/documentation/accessories/camera.html) |
| Alternative | Global Shutter Camera: Sony IMX296, 1456 × 1088, 1456 × 1088p60, CSI with C/CS-mount for external lenses | [raspberrypi.com camera docs](https://www.raspberrypi.com/documentation/accessories/camera.html) |
| Ambient light | not in recovered sources | — |
| Water spray | not in recovered sources | — |
| Price | **CAD $36.45**, in stock | [pishop.ca](https://www.pishop.ca/product/raspberry-pi-camera-module-3/) |
| Host | no bare Pi 5 price recovered (the pishop.ca product page 404'd); pishop.ca listed Raspberry Pi 5 Desktop Kit 8GB at CAD $280.00 and Raspberry Pi 5 Starter Kit 1GB at CAD $132.95 | [pishop.ca](https://www.pishop.ca/?s=Raspberry+Pi+5&post_type=product) |

**What breaks it.** No depth, so the far walker and the near walker are separated only by apparent
size and image position; both-sides walking is the hard case. Rolling shutter on the IMX708 (the
Global Shutter Camera exists precisely because of this). Ambient light and hallway lighting change
the whole pipeline, and nothing in the dump quantifies that. Cheapest sensor here by a wide margin,
but the most software.

## 12. IR break-beam — Adafruit 2168 (5 mm LEDs)

| Spec | Value | Source |
|---|---|---|
| Type | IR break-beam, separate emitter and receiver modules | [Adafruit 2168](https://www.adafruit.com/product/2168) |
| Max range | approximately 50 cm (20 inches) | [Adafruit 2168](https://www.adafruit.com/product/2168) |
| Supply | 3.3 V – 5.5 V DC (5 V recommended for optimal range); emitter draws 10 mA @ 3.3 V, 20 mA @ 5 V | [Adafruit 2168](https://www.adafruit.com/product/2168) |
| Output | "Open collector transistor output" needing a pull-up; sinks up to 100 mA | [Adafruit 2168](https://www.adafruit.com/product/2168) |
| Response time | less than 2 ms | [Adafruit 2168](https://www.adafruit.com/product/2168) |
| Size | 20 × 10 × 8 mm; a 3 mm version exists for shorter distances | [Adafruit 2168](https://www.adafruit.com/product/2168) |
| Ambient light | "The product description does not address sunlight or ambient light interference" | [Adafruit 2168](https://www.adafruit.com/product/2168) |
| Water spray | not in recovered sources | — |
| Canadian price | **not in recovered sources** — elmwoodelectronics.ca returned HTTP 403 (and the site now redirects orders to PiShop.ca); the pishop.ca break-beam search returned no break-beam products | — |

**What breaks it.** Range. 50 cm cannot span a ~3 m hallway, so an emitter/receiver pair per beam
across the walking path is impossible at this part. Even if range allowed, a break-beam is binary:
you get crossings, not position, and two people crossing simultaneously make the beam pattern
ambiguous. Resolution equals beam spacing — 20 beams at 50 mm pitch means 20 emitter/receiver pairs
and 40 mounting points, one row per side of the strip.

## 13. Safety light curtain — Banner EZ-SCREEN LS

The industrial version of the same idea, with the range break-beam lacks.

| Spec | Value | Source |
|---|---|---|
| Resolutions | 14 mm, 23 mm or 40 mm (this is the beam spacing) | WebSearch summary + [EZ-SCREEN LS manual 179480](https://info.bannerengineering.com/cs/groups/public/documents/literature/179480.pdf) ("Choose resolution (14, 23, or 40 mm) and defined area") |
| Operating range | up to 12 m (39 ft) | WebSearch summary of Banner material |
| Response time | per-model table, `Response Time, Tr (ms)`, varies by resolution and defined area. One worked example in the manual: "Tr = 0.0116 second (the specified SLLP23-560P88 response time)" ≈ 11.6 ms | [EZ-SCREEN LS manual 179480](https://info.bannerengineering.com/cs/groups/public/documents/literature/179480.pdf) |
| Cascading | "Up to four sensor pairs (any length or resolution) can be combined into one system" | same manual |
| Output | OSSD safety outputs (turn Off when the defined area is broken, On when clear); OSSD test pulse width 200 µs typ, period 200 ms typ; switching current 0–0.5 A per OSSD | same manual |
| **Does it report which beam is blocked?** | **Not resolved from the dump.** The manual references a diagnostic indicator showing "condition (clear or blocked beam) of a defined group of beams" and a 7-segment diagnostic digit, but no per-beam data output was recovered. The primary output is OSSD on/off | same manual |
| Price | not in recovered sources | — |

**What breaks it.** A safety light curtain is designed to answer "is the area clear?", not "where in
the area". Unless the per-beam status is readable — which the dump does not establish — it gives no
position at all, and two people are indistinguishable from one. It is also a machine-guarding
product priced accordingly (no price recovered), and mounting a 1 m curtain along a hallway is a
physical intrusion the water strip probably cannot accept.

## 14. Pressure / capacitive floor mats

Only search-result summaries were recovered; no datasheet parsed.

| Spec | Value | Source |
|---|---|---|
| Basic behaviour | "A pressure sensitive mat provides a contact signal when force is applied anywhere within the area of the mat. Some mats provide a single signal, while others can resolve the position of the applied force within the mat" | WebSearch summary in dump |
| Typical product | 24" × 36" pressure sensitive mat with a 12 ft, 2-wire connection cable; "floor mat switches close electrical contact when weight is applied" | WebSearch summary (Amazon listing) |
| Position resolution | one *pressure-mapping* sensor quoted "resolution of 20 mm from center to center", but for a different 320 × 320 mm product — not a floor mat | WebSearch summary in dump |
| Response time | **not in recovered sources** — the Tapeswitch safety-mat catalog fetch returned no usable content | [tapeswitch.com Mat_v3.01.pdf](https://www.tapeswitch.com/support/catalogs/Mat_v3.01.pdf) |
| Zoned / position output | not in recovered sources | — |
| Water resistance | **not in recovered sources** — notable, since the mat would sit next to a water basin | — |
| Capacitive mats | **not in recovered sources**, nothing fetched | — |
| Price | not in recovered sources | — |

**What breaks it.** A plain safety mat is one switch: it says someone is standing on it, nowhere
near a 50 mm position. Zoned mats exist per the summary above but nothing recovered names a part,
a pitch, a response time or a price. Two people is fine for presence, useless for identity. And a
pressure mat is the one method that only sees people who step *on* it — a walker passing beside the
strip may never touch it.

---

## Comparison

Derived column: **mm/frame** is how far a walker moves between updates at the dump's usual pace of
1.31 m/s ([Murtagh et al., Sports Medicine, 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7806575/)).
50 mm = one jet pitch. This is arithmetic from cited values, not a sourced figure.

| Method | Position resolution along strip | Update rate | Range | **Tracks 2 people?** | **Gives speed?** | mm/frame @ 1.31 m/s | Covers ~3 m hallway? | Interface | Price |
|---|---|---|---|---|---|---|---|---|---|
| VL53L1X row | = sensor spacing (one per jet = 50 mm) | up to 50 Hz short / 30 Hz med-long | 4 m dark; **73–76 cm med/long under ambient test**, 135 cm short | Partly — occlusion of far by near walker (inference) | Derived from position rate | 26 mm @50 Hz | Marginal (short mode ~1.35 m) | I²C 400 kHz, XSHUT per device | USD $22.95 ea / CAD $35.00 SATEL |
| TF-Luna row | = sensor spacing; 2° beam | 1–250 Hz, default 100 Hz | 0.2–8 m | Partly — same occlusion caveat | Derived from position rate | 13 mm @100 Hz | Yes | UART / I²C | No CAD source recovered |
| TFmini | not in recovered sources | — | — | — | — | — | — | — | — |
| VL53L5CX 8×8 | ~125 mm/zone over 1 m (derived) | 60 Hz @4×4, 15 Hz @8×8 (search summary) | 4 m | **Yes** — zone map, multi-target per zone | Derived from position rate | 87 mm @15 Hz | Yes | I²C 1 MHz | USD $19.95 / CAD $35.47 SATEL |
| VL53L8CX 8×8 | ~125 mm/zone over 1 m (derived) | "up to 60 Hz"; 4×4-vs-8×8 split not recovered | 4 m ideal, 2.8 m @5000 lux | **Yes** — same as L5CX | Derived from position rate | 22 mm @60 Hz (4×4 assumed) | Yes | I²C 1 MHz / SPI 3 MHz | USD $24.95, no CAD |
| DFRobot C4001 | none along strip — distance only, **no angle or x/y** | not in recovered sources | 8 m presence / 12 m motion | **No** | **Yes, directly** (0.1–10 m/s) | — | Yes | I²C / UART 9600 | USD $12.90 / **CAD $18.91** |
| HLK-LD2450 | mm-resolution x/y per target | **10 fps** | 6 m, ±60° az | **Yes — up to 3 targets** | **Yes, directly** (cm/s per target) | 131 mm ≈ 2.6 pitches | Yes | UART 256000 | No CAD source recovered |
| Seeed MR60BHA2 | x/y in metres per target | **not in recovered sources** | 6 m presence | **Yes — up to 3** | Yes (Doppler index, cm/s) | unknown | Yes | serial via XIAO ESP32C6 | not recovered |
| Seeed MR60FDA2 | coordinates via `getHuman()` | not in recovered sources | 6 m presence; 2 m radius ceiling-mounted | not stated | not stated | unknown | Marginal (2 m radius) | serial via XIAO ESP32C6 | not recovered |
| OAK-D Lite | pixel-level, software | **depth FPS not in recovered sources** | ~80 cm – 12 m ideal | **Yes** (software; on-device AI) | Derived from position rate | unknown | Yes | USB 2/3 | not recovered |
| RealSense D435 | pixel-level, software | up to 90 fps depth | 0.3–3 m ideal | **Yes** (software) | Derived from position rate | 15 mm @90 Hz | Yes, near-exactly | USB-C 3.1 Gen 1 | CAD $554.63 (D435i, approximate) |
| Pi Camera Module 3 | pixel-level, software, no depth | 1536×864p120 (docs) | lens-dependent | Partly — no depth to separate near/far | Derived from position rate | 11 mm @120 Hz | Yes | CSI | **CAD $36.45** + host |
| IR break-beam (Adafruit 2168) | = beam spacing | <2 ms response | **~50 cm — fails** | **No** — binary, ambiguous with 2 people | Derived from crossing times | — | **No** | open-collector GPIO | not recovered |
| Banner EZ-SCREEN LS | = 14 / 23 / 40 mm resolution, **if per-beam status is readable — unconfirmed** | ~11.6 ms (one model) | up to 12 m | **No** as an OSSD device | No | 15 mm @11.6 ms | Yes | OSSD outputs | not recovered |
| Pressure mat | single contact typical; zoned exists but no part recovered | not in recovered sources | mat area | Presence only | No | — | mat area only | dry contact | not recovered |

---

## Ranked shortlist for this hallway

Hallway assumed ~3 m × 3 m, strip ~1 m of 20 jets at 50 mm pitch, two walkers who may cross.

**1. HLK-LD2450 mmWave radar — start here.**
It is the only recovered part that hands you exactly the two hard constraints in one serial frame:
up to three targets, each with X and Y in mm and speed in cm/s, default multi-target mode
([protocol v1.03](https://make.net.za/wp-content/datasheets/HLK%20LD2450%20Serial%20Communication%20Protocol%20v1.03.pdf)).
6 m range and ±60° azimuth cover a 3 m hallway. **Condition:** 10 fps is 2.6 jet pitches of travel
per frame, so the control path must extrapolate between frames using the reported speed — that is
the design commitment this choice implies. **Condition:** no Canadian supplier or price was
recovered; sourcing is an open item. **Condition:** RF and metal do not mix — a metal basin or trim
near the strip reflects and can create false targets (vault, `dfrobot-c4001-mmwave-radar.md`).

**2. VL53L5CX or VL53L8CX 8×8 ToF array, overhead — the strip-native option.**
A downward-looking zone map is the most direct mapping from sensor to jets, is independent of
ambient lighting by construction, and reads two blobs when two people are present. **Condition:**
~125 mm per zone over a 1 m strip (derived from the quoted 45° per-axis FoV) is 2.5 jet pitches, so
you interpolate the blob centroid or use two sensors. **Condition:** at 8×8 the rate is ~15 Hz per
a search summary of the ST datasheet — confirm from the datasheet before committing. Prefer the
**L8CX** if rate binds, for its SPI interface; prefer the **L5CX** if CAD availability binds
(CAD $35.47 at DigiKey vs no CAD listing for the L8CX).

**3. RealSense D435 — the option that meets every constraint and costs the most.**
0.3–3 m ideal range against a 3 m hallway, 90 fps depth, global shutter, and depth makes near/far
walker separation a solved problem rather than a heuristic. **Condition:** ~CAD $554.63 (D435i,
approximate) and a 14-week lead time, plus a host and real vision code. Justified only if the
crossing case defeats the radar in testing.

**4. OAK-D Lite — same idea, cheaper, with a missing number.**
On-device 1.4 TOPS inference means person tracking without a beefy host. **Condition: do not
select it until depth FPS is confirmed** — two fetches of the Luxonis page failed to state it, and
that is the constraint-2 number. Also do not design around the "75 cm" baseline in the docs.

**5. Pi Camera Module 3 overhead — the cheap fallback.**
CAD $36.45 and 1536×864p120. **Condition:** no depth, so two people on opposite sides are separated
only by image position and apparent size, and hallway lighting drives everything. Reasonable as a
bench rig to develop the wave logic before the real sensor arrives.

**Not recommended for this job:** the DFRobot C4001 (no bearing, no x/y, no per-target
separation — it answers "is someone there and how fast", which is a different question), IR
break-beam (50 cm range against a 3 m hallway), safety light curtains (OSSD on/off, no confirmed
per-beam readout, physically intrusive), and pressure mats (single contact, and a walker passing
beside the strip may never step on one).

**Open across all five.** Nothing in the dump addresses water spray or humidity for any sensor.
That is a first-order question for a device mounted next to twenty water jets and it decides which
of these survive contact with the actual installation.

---

## Gaps — what the dump did not cover

1. **Water spray and humidity, for every single method.** Not one fetched page addressed it. This
   is the biggest hole and the one most likely to overturn the ranking.
2. **Both-sides walking and the crossing case.** No source measured or described two-target
   behaviour during a crossing for any part. All multi-target claims are capability claims from
   product pages, not test results.
3. **ST datasheets never parsed.** Every direct fetch of `vl53l1x.pdf` (via st.com/mouser),
   `vl53l5cx.pdf` and `vl53l8cx.pdf` returned unreadable binary or 404. The VL53L1X numbers here
   come from a Pololu-hosted copy that *did* parse; the VL53L5CX 8×8 = 15 Hz figure comes from a
   search summary, and the VL53L8CX 4×4/8×8 split was never recovered.
4. **Canadian prices, mostly missing.** Only three CAD prices are trustworthy in the dump —
   SEN0610 CAD $18.91, VL53L5CX-SATEL CAD $35.47, VL53L1X-SATEL CAD $35.00 (all digikey.ca) — plus
   pishop.ca CAD $36.45 for the Pi Camera. digikey.ca product-detail fetches returned unrelated
   parts (a wire seal, a crystal oscillator), so any other DigiKey number in the dump is unsafe.
   elmwoodelectronics.ca returned 403 and now redirects to PiShop.ca. **No CAD price recovered for:
   TF-Luna, HLK-LD2450, VL53L8CX, OAK-D Lite, IR break-beam, light curtains, pressure mats.**
5. **TFmini and capacitive floor mats: nothing at all.** Neither was fetched.
6. **OAK-D Lite depth frame rate**, and the implausible "75 cm" stereo baseline in the Luxonis docs.
7. **Banner EZ-SCREEN LS per-beam readout.** Whether you can read *which* beam is blocked — the
   only thing that would make a light curtain a position sensor — was not established.
8. **Pressure mat response time, zoning, IP rating and part numbers.** The Tapeswitch catalog fetch
   returned nothing usable.
9. **C4001 update rate and max target count.** Both explicitly absent from the DFRobot reference.
10. **Seeed MR60 refresh rate.** Absent for both variants, and the BHA2 firmware notes say it
    *decreased*.
11. **ESPHome `ld2450` component page** 404'd — its polling/update behaviour is unconfirmed.
12. **Cheap follow-up available locally.** The dead agent left `pdftotext` extracts of several
    datasheets in the scratchpad. They were *not* read for this document (scope was `sensing.txt`
    only) but a future session can read them without re-fetching:
    - `C:\Users\GARRET~1.REY\AppData\Local\Temp\claude\C--Users-garrett-reynolds-Projects-Personal-Electronics-water-jet-follower\150b3fb2-e203-49fc-bb29-f6406d73b48c\scratchpad\vl53l1x.txt`
    - `C:\Users\GARRET~1.REY\AppData\Local\Temp\claude\C--Users-garrett-reynolds-Projects-Personal-Electronics-water-jet-follower\150b3fb2-e203-49fc-bb29-f6406d73b48c\scratchpad\vl53l8cx.txt`
    - `C:\Users\GARRET~1.REY\AppData\Local\Temp\claude\C--Users-garrett-reynolds-Projects-Personal-Electronics-water-jet-follower\150b3fb2-e203-49fc-bb29-f6406d73b48c\scratchpad\ld2450.txt`
    - `C:\Users\GARRET~1.REY\AppData\Local\Temp\claude\C--Users-garrett-reynolds-Projects-Personal-Electronics-water-jet-follower\150b3fb2-e203-49fc-bb29-f6406d73b48c\scratchpad\tfluna.txt`
    - `C:\Users\GARRET~1.REY\AppData\Local\Temp\claude\C--Users-garrett-reynolds-Projects-Personal-Electronics-water-jet-follower\150b3fb2-e203-49fc-bb29-f6406d73b48c\scratchpad\banner.txt`
    - `C:\Users\GARRET~1.REY\AppData\Local\Temp\claude\C--Users-garrett-reynolds-Projects-Personal-Electronics-water-jet-follower\150b3fb2-e203-49fc-bb29-f6406d73b48c\scratchpad\picam3.txt`

    (`vl53l8cx.txt` has a later timestamp than the rest and its provenance is unverified.)

---

## Sources

Used for at least one number in this document:

- https://www.pololu.com/file/0J1506/vl53l1x.pdf — ST VL53L1X datasheet, DocID031281 Rev 3, Nov 2018
- https://www.pololu.com/product/3415 — Pololu VL53L1X carrier
- https://www.pololu.com/product/3417 — Pololu VL53L5CX carrier
- https://www.pololu.com/product/3419 — Pololu VL53L8CX carrier
- https://www.sparkfun.com/products/18642 — SparkFun Qwiic ToF Imager VL53L5CX
- https://www.adafruit.com/product/5425 — Adafruit board page (returned VL53L4CX content)
- https://www.st.com/resource/en/datasheet/vl53l5cx.pdf — cited only via a WebSearch summary (DS13754); the PDF itself never parsed
- https://en.benewake.com/TFLuna/index.html — Benewake TF-Luna product page
- https://en.benewake.com/uploadfiles/2024/04/20240426135921367.pdf — TF-Luna datasheet
- https://en.benewake.com/DataDownload/index.aspx?pid=20&lcid=21 — Benewake download centre
- https://www.dfrobot.com/product-2795.html — DFRobot C4001 / SEN0610 product page
- https://wiki.dfrobot.com/SKU_SEN0610_Gravity_C4001_mmWave_Presence_Sensor_12m_I2C_UART — C4001 12 m wiki
- https://wiki.dfrobot.com/sen0610/docs/20949 — C4001 API/protocol reference
- https://wiki.dfrobot.com/SKU_SEN0609_C4001_mmWave_Presence_Sensor_25m — C4001 25 m variant (via search summary)
- https://www.hlktech.net/index.php?id=1157 — Hi-Link HLK-LD2450 product page
- https://make.net.za/wp-content/datasheets/HLK%20LD2450%20Serial%20Communication%20Protocol%20v1.03.pdf — LD2450 serial protocol v1.03
- https://wiki.seeedstudio.com/getting_started_with_mr60bha2_mmwave_kit/ — Seeed MR60BHA2
- https://wiki.seeedstudio.com/getting_started_with_mr60fda2_mmwave_kit/ — Seeed MR60FDA2
- https://docs.luxonis.com/hardware/products/OAK-D%20Lite — Luxonis OAK-D Lite
- https://www.realsenseai.com/products/stereo-depth-camera-d435/ — RealSense D435
- https://www.intel.com/content/www/us/en/products/sku/128255/intel-realsense-depth-camera-d435/specifications.html — Intel D435 spec page
- https://www.raspberrypi.com/documentation/accessories/camera.html — Raspberry Pi camera docs
- https://pip-assets.raspberrypi.com/categories/786-raspberry-pi-camera-module-3/documents/RP-008151-DS-1-camera-module-3-product-brief.pdf — Camera Module 3 product brief
- https://www.pishop.ca/product/raspberry-pi-camera-module-3/ — PiShop.ca, CAD price
- https://www.pishop.ca/?s=Raspberry+Pi+5&post_type=product — PiShop.ca Pi 5 kit prices
- https://www.adafruit.com/product/2168 — Adafruit IR break-beam sensor, 5 mm LEDs
- https://info.bannerengineering.com/cs/groups/public/documents/literature/179480.pdf — Banner EZ-SCREEN LS manual
- https://www.digikey.ca/en/products/result?keywords=SEN0610 — CAD $18.91
- https://www.digikey.ca/en/products/result?keywords=VL53L5CX-SATEL — CAD $35.47
- https://www.digikey.ca/en/products/result?keywords=VL53L1X-SATEL — CAD $35.00
- https://www.digikey.ca/en/products/result?keywords=D435 — CAD $554.63 (D435i; attribution approximate)
- https://pmc.ncbi.nlm.nih.gov/articles/PMC7806575/ — Murtagh et al., Sports Medicine, 2020, walking speed meta-analysis
- Second Brain vault: `C:\Users\garrett.reynolds\Vaults\Second Brain\wiki\hardware\dfrobot-c4001-mmwave-radar.md`

Fetched but unusable — do not retry these exact URLs without a different approach:

- https://www.st.com/en/imaging-and-photonics-solutions/vl53l5cx.html — 404
- https://www.st.com/resource/en/datasheet/vl53l1x.pdf, `vl53l5cx.pdf`, `vl53l8cx.pdf` — unreadable binary PDF
- https://www.mouser.com/datasheet/2/389/vl53l1x-1587865.pdf — 404
- https://cdn.sparkfun.com/assets/8/f/9/1/2/VL53L5CX_Datasheet.pdf — 404
- https://www.sparkfun.com/sparkfun-qwiic-tof-imager-vl53l8cx.html — 404 (the VL53L8CX SparkFun board may not exist under that URL)
- https://www.pololu.com/file/0J1878/vl53l5cx.pdf — unreadable binary PDF
- https://datasheets.raspberrypi.com/camera/camera-module-3-product-brief.pdf — 301, then 403 / 302 chain
- https://www.tapeswitch.com/support/catalogs/Mat_v3.01.pdf — no usable content returned
- https://elmwoodelectronics.ca/... — 403; the site now directs orders to PiShop.ca
- https://esphome.io/components/sensor/ld2450/ — 404
- https://pubmed.ncbi.nlm.nih.gov/9143432/ — cookie wall
- https://www.digikey.ca/en/products/detail/... product-detail URLs — returned unrelated parts (wire seal, crystal oscillator); use the `?keywords=` search form instead
- https://www.digikey.ca/en/products/result?keywords=VL53L8CX-SATEL, `TF-Luna`, `OAK-D-Lite` — no results at DigiKey Canada
