# Control path options: sensor reading to DMX out

Research for GitHub issue #6.

**Salvage note.** Two research agents fetched these sources on 2026-09-04 and were killed before
writing anything. This document was reconstructed on 2026-09-04 from the recovered tool output of
those two runs and from nothing else — no new fetching was done. Coverage is therefore uneven: some
options have datasheet-grade numbers, others have only what a search snippet returned, and several
pages the agents tried came back 403 or 404. Every gap is marked "not in recovered sources" rather
than filled from memory. Prices are whatever the recovered page said, on 2026-09-04, and were not
re-checked.

## Summary

- Two HydroMatrix modules = 100 channels in one universe; a 100-slot packet is far below the 512-slot worst case, so DMX bandwidth is not the constraint — the wave rate is set by whatever generates the frames.
- Cheapest and most self-contained path: an ESP32 running `esp_dmx` into an RS-485 transceiver — CAD $2.50 for a MAX485 module, no SD card to corrupt, hardware UART timing, watchdog auto-reset.
- The Pi + OLA path is strong *if* one of the two dongles Garrett already owns is OLA-supported; otherwise it needs an Enttec DMX USB Pro at CAD $227 or a CAD $19.95 RS-485 HAT.
- **The recovered sources say nothing about the MADRIX USB ONE.** Whether OLA (or QLC+) can drive it is the single unanswered question that decides between those two paths.
- TouchDesigner (Windows/macOS only), QLC+ (no arithmetic in its script language), and the S-Play family (playlists, no continuous position mapping) all fail the "compute a moving hill from a live position" requirement.

## What the control path has to satisfy

From issue #2's resolved research (already in the repo) plus the DMX standard:

| Fact | Value | Source |
|---|---|---|
| Channels per module | 50, in order R, G, B, W, fountain height per jet | issue #2 research doc |
| Two modules on one line | 100 channels, one universe | issue #2 research doc |
| Power | 24 VDC, 3.2 A max per module | issue #2 research doc |
| DMX bit time | 3.92 / 4 / 4.08 µs (min/typ/max) | [ANSI E1.11-2008 (R2018) Table 6](https://tsp.esta.org/tsp/documents/docs/ANSI-ESTA_E1-11_2008R2018.pdf) |
| Minimum update time, 513 slots | 22.7 ms | E1.11 Table 6 |
| Maximum refresh rate, 513 slots | 44 updates/s | E1.11 Table 6 |
| BREAK (transmitter) | min 92 µs, max 176 µs | E1.11 Table 6 |
| MAB (transmitter) | min 12 µs | E1.11 Table 6 |
| BREAK-to-BREAK | min 1204 µs, max 1.00 s | E1.11 Table 6 |

The 44 Hz ceiling is for a *full* universe. ENTTEC's DMX primer states the arithmetic and the
consequence of sending fewer slots: a packet is "Break (88 µs) + MAB (8 µs) + 513 slots × 44 µs",
totalling ≈22.7 ms, and "A controller driving a 96-channel rig … needs about 4.4 ms per packet,
roughly 230 packets per second"
([support.enttec.com/dmx/dmx-basics/what-is-dmx512](https://support.enttec.com/dmx/dmx-basics/what-is-dmx512)).
**Derived, not quoted:** 100 slots sits essentially on that same figure, ≈4.6 ms of data per packet,
so a short-frame controller could in principle push well past 44 Hz on this rig. Whether the
HydroMatrix modules accept short or fast frames is **not in recovered sources** — assume 44 Hz until
bench-measured.

---

## 1. MADRIX USB ONE (owned)

**Garrett already owns it? Yes.**

This is the option that most needs an answer and has the least evidence behind it.

- **Everything the recovered sources say about MADRIX**, in full, is one line in the issue #2
  research doc, sourced from HB-Laser's own HydroMatrix site: *"HB-Laser uses MADRIX; any DMX-512
  controller works."* That is a statement about HB-Laser's house software, not about the USB ONE
  interface.
- **No MADRIX product page, datasheet, driver page, refresh-rate figure, or price is in the recovered
  sources.** Neither dead agent fetched one.
- **Does OLA list it as supported? Not in recovered sources — and the two OLA device lists that
  *were* recovered do not name it.** The USB plugin (`ola-usbdmx.conf`) lists: "Anyma uDMX, AVLdiy
  D512, Digital Enlightenment USB-DMX, DMXControl Projects e.V. Nodle U1, DMXCreator 512 Basic,
  Eurolite USB-DMX512 PRO, Eurolite USB-DMX512 PRO MK2, Fadecandy, FX5 DMX, ShowJockey SJ-DMX-U1,
  Sunlite USBDMX2, Velleman K8062"
  ([docs.openlighting.org/ola/conf/ola-usbdmx.conf.html](https://docs.openlighting.org/ola/conf/ola-usbdmx.conf.html)).
  The serial USB plugin (`ola-usbserial.conf`) lists: "Arduino RGB Mixer, DMX-TRI & RDM-TRI, DMXking
  USB DMX512-A, Ultra DMX, Ultra DMX Pro, DMXter4, DMXter4A & mini DMXter, Enttec DMX USB Pro & USB
  Pro Mk II, Robe Universe Interface, LumenRadio CRMX Nova TX USB"
  ([ola/plugins/usbserial/README.md](https://github.com/OpenLightingProject/ola/blob/master/plugins/usbserial/README.md)).
  Neither names MADRIX. These are two plugin READMEs out of OLA's full plugin set, so **absence here
  is not proof of non-support** — OLA's own site claims "over a dozen USB devices"
  ([openlighting.org/ola](https://www.openlighting.org/ola/)) and the full device list was never
  fetched.
- Likewise QLC+: its DMX USB plugin "supports a variety of FTDI-based USB-to-DMX devices" and can
  force a device to Open TX, Open RX, Pro RX/TX, Pro Mk2, Ultra Pro, DMX4ALL or Vince Tx
  ([docs.qlcplus.org/v4/plugins/dmx-usb](https://docs.qlcplus.org/v4/plugins/dmx-usb)). Whether the
  USB ONE is FTDI-based, and so whether one of those forced modes would work, is **not in recovered
  sources.**

**Consequence.** If the USB ONE (or the HB-Laser USB-DMX-RDM, below) turns out to be Enttec-Pro-API
compatible or otherwise OLA-drivable, the Pi + Python path costs nothing in new hardware and becomes
the obvious choice. If neither is, the Pi path needs a CAD $227 interface and the ESP32 path wins on
cost. **This is the top open question.**

## 2. HB-Laser USB-DMX-RDM (owned)

**Garrett already owns it? Yes.**

**Zero mentions in the recovered sources** — no page for it was fetched by either agent. Same
consequence as above: unknown whether OLA, QLC+ or TouchDesigner can drive it.

---

## 3. ESP32 sending DMX512 directly (esp_dmx + RS-485 transceiver)

**Garrett already owns it? The ESP32, yes. The transceiver, unknown.**

### Library

`esp_dmx` by Mitch Weisbrod, v4.1.0 released 2024-03-21, default branch `release/v4.1`, MIT licence,
491 stars, last push 2024-06-14 ([github.com/someweisguy/esp_dmx](https://github.com/someweisguy/esp_dmx);
`library.json`, `library.properties`). "This library allows for transmitting and receiving ANSI-ESTA
E1.11 DMX-512A and ANSI-ESTA E1.20 RDM using an Espressif ESP32."

- Frameworks: Arduino-ESP32 ≥ 2.0.3, ESP-IDF ≥ 4.4.1, PlatformIO. `platforms: espressif32`,
  `architectures=esp32`.
- Writing: `dmx_write()` fills the buffer, `dmx_send()` transmits, `dmx_wait_sent()` blocks until
  idle. `dmx_write_slot(port, slot_num, value)` writes one slot; `dmx_write_offset()` writes a run.
- **Short frames:** "To send a specific number of DMX slots, the function `dmx_send_num()` may be
  used." So the 100 live slots can be sent as a 100-slot packet rather than a full 512.
- Timing: "It takes a typical DMX packet approximately 22 milliseconds to send." Break and MAB are
  adjustable per-port with `dmx_set_break_len()` / `dmx_set_mab_len()`; "In most situations it is not
  necessary to adjust the default timing." The README also notes "Frame rates may range from 1fps to
  up to approximately 830fps. A typical DMX controller transmits packets between approximately 25fps
  to 44fps."
- RDM controller functions exist, including `rdm_send_set_dmx_start_address()` and
  `rdm_discover_devices_simple()` — relevant because issue #2 found RDM is how HydroMatrix fountain
  height is recalibrated and (possibly) how modules are auto-addressed.
- Chip variants: the README does not enumerate them. The source does contain an ESP32-C3 guard —
  `src/dmx/hal/timer.c`: `#ifdef CONFIG_IDF_TARGET_ESP32C3 / timer->idx = 0;  // ESP32C3 uses idx 1
  for Watchdog` — so C3 is at least accounted for. Which ESP32 variants are formally supported is
  **not in recovered sources.**

### Wiring

From the README's "Wiring an RS-485 Circuit" section: the ESP32 has no built-in transceiver, so
`RO`→UART RX, `DI`→UART TX, and `DE`+`/RE` shorted together to one GPIO ("the enable pin … also
referred to as the RTS pin"). The example schematic uses a MAX485 with "R1 and R3 are 680 ohms each"
and "R2, the 120 ohm resistor, is a terminating resistor". Critically:

> "Many RS-485 chips, such as the Maxim MAX485 are 3.3v tolerant. This means that it can be
> controlled with the ESP32 without any additional electrical components. Other RS-485 chips may
> require 5v data to transmit DMX."

The MAX485 datasheet itself was never successfully read in these runs, so the electrical margin is
**unverified beyond the library author's claim.**

### Parts and cost

| Part | Price | Stock | Source |
|---|---|---|---|
| MAX 485 Module / TTL to RS-485 converter, PiShop.ca | CAD $2.50 | "IN STOCK" | [pishop.ca](https://www.pishop.ca/product/max-485-module-rs-485-module-ttl-to-rs-485-converter-module/) — "On-board MAX485 chip … Working voltage: 5V", 44 × 14 mm |
| ESP32-DEVKITC-32E (ESP32-WROOM-32E 4MB), DigiKey.ca | CAD $15.62 | 0 in stock, 252 est. 2027-03-29 | [digikey.ca](https://www.digikey.ca/en/products/detail/espressif-systems/ESP32-DEVKITC-32E/12091810) |
| SparkFun Transceiver Breakout RS-485 (SP3485) | price not shown | Elmwood has stopped taking orders | [elmwoodelectronics.ca/products/10124](https://elmwoodelectronics.ca/products/10124) |

Note the PiShop MAX485 module is listed at 5 V working voltage; the esp_dmx claim is about the chip
being 3.3 V *tolerant on its logic inputs*, not about running its supply at 3.3 V. Reconcile on the
bench.

### Headless operation and power-loss recovery

Strong. No filesystem to corrupt. ESP-IDF's watchdogs give unattended recovery: the Interrupt
Watchdog "is responsible for ensuring that ISRs … are not blocked from running for a prolonged period
of time", and on timeout invokes the panic handler, with "a second stage timeout that will hard-reset
the chip". The Task Watchdog by default only prints a warning and backtrace, but
`CONFIG_ESP_TASK_WDT_PANIC` makes it "cause a panic and a system reset"
([docs.espressif.com … wdts.html](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/wdts.html)).
Set that for a months-long install.

### Wave maths

Easiest of all the options in one sense — it is just C. A 100-byte array, a hill function over jet
index, a speed→colour map, `dmx_write()`, `dmx_send_num()`. Hardest in another: you write and debug
it on a microcontroller with no display.

## 3a. SparkFun ESP32 Thing Plus DMX to LED Shield (DEV-15110)

**Garrett already owns it? Not stated — assume no.**

- USD $18.50 on SparkFun; **CAD $30.22, 64 in stock, "Active"** on DigiKey.ca
  ([digikey.ca DEV-15110](https://www.digikey.ca/en/products/detail/sparkfun-electronics/DEV-15110/10054912)).
- "capable of DMX output, input, as well as Artnet input. The shield is electrically isolated to keep
  with DMX spec"
  ([github.com/sparkfun/SparkFun_ESP32_Thing_Plus_DMX_to_LED_Shield](https://github.com/sparkfun/SparkFun_ESP32_Thing_Plus_DMX_to_LED_Shield)).
- Parts, read out of the Eagle schematic in that repo: **MAX3485CSA** transceiver, **6N137S**
  optocouplers, **TXB0104** level shifter, nets named `485/TX`, `485/RX`, `485/EN`, and isolated
  `VCC-ISO`/`GND-ISO` rails. The hookup guide confirms "Power and data isolation through DC-DC
  converter and optocouplers", "1 kVDC isolation voltage", "200 mA at 5V"
  ([learn.sparkfun.com](https://learn.sparkfun.com/tutorials/sparkfun-esp32-dmx-to-led-shield/all)).
- **Two catches.** (1) Its DMX connectors are **XLR-3**, not the XLR-5 the modules terminate in — an
  adapter is needed and no adapter price is in the recovered sources. (2) "You should always power
  the DMX shield with 5V to provide proper power for RS485." Termination: "If you know the board will
  be at the end of a chain of DMX devices, solder in a 120 Ohm resistor in the term spot."
- Its own library, **SparkFunDMX** v2.0.1 (2023-11-27), offers only `.initWrite()`, `.write()`,
  `.update()`; the guide "does not document frame rate, timing specifications, or transmission
  methodology". Which ESP32 UART pins it uses is **not in recovered sources**. Prefer `esp_dmx` on
  this hardware.
- Board is Feather footprint; SparkFun recommends the ESP32 Thing Plus.

---

## 4. Raspberry Pi with OLA and Python

**Garrett already owns it? The Pi, yes. The USB interface, unknown (see §1, §2).**

### OLA

"The Open Lighting Architecture is a framework for lighting control information. It supports a range
of protocols and over a dozen USB devices" ([openlighting.org/ola](https://www.openlighting.org/ola/)).
Protocols include Art-Net (TX/RX/RDM), E1.31/sACN (TX/RX on Linux, macOS, FreeBSD), Enttec DMX USB
Pro (TX/RX/RDM), Enttec Open DMX (TX), and the DMXking ultraDMX series. It "runs as a service daemon".

- Latest release **0.10.9, 2023-02-26** (`gh api repos/OpenLightingProject/ola/releases/latest`).
  Debian bookworm packages it as `ola` version `0.10.9.nojsmin-2` — "olad, the OLA daemon used to
  control lighting, and a number of command-line tools" — with `ola-python` alongside
  ([packages.debian.org/bookworm/ola](https://packages.debian.org/bookworm/ola)).
- Python client, verbatim from the docs
  ([openlighting.org/ola/developer-documentation/python-api](https://www.openlighting.org/ola/developer-documentation/python-api/)):

  ```python
  import array
  from ola.ClientWrapper import ClientWrapper

  def DmxSent(state):
    wrapper.Stop()

  universe = 1
  data = array.array('B', [10, 50, 255])
  wrapper = ClientWrapper()
  client = wrapper.Client()
  client.SendDmx(universe, data, DmxSent)
  wrapper.Run()
  ```

  The continuous-send example uses `TICK_INTERVAL = 100  # in ms` via `wrapper.AddEvent()` — i.e. the
  doc's own example runs at ~10 fps. That is the example's choice, not a limit; the tick is yours to
  set.
- Pi tutorial ([openlighting.org/ola/tutorials/ola-on-raspberry-pi](https://www.openlighting.org/ola/tutorials/ola-on-raspberry-pi/)):
  either a pre-built `raspbian-ola-X.Y.Z.zip` image or a source build. Web UI on port 9090, config in
  `/var/lib/ola/conf`, logs to `/var/log/syslog`. **Whether `olad` auto-starts at boot is not stated
  on that page** — it shows a manual `olad -l 3`. Also: "A powered USB Hub, if you plan on using a USB
  DMX/RDM device. Many devices draw more current than the Raspberry Pi can support."

### The four ways OLA gets DMX out of a Pi

| Plugin | How it works | Rate config | Source |
|---|---|---|---|
| `usbserial` | Enttec DMX USB Pro & Mk II, DMXking USB DMX512-A / Ultra DMX / Ultra DMX Pro, DMX-TRI, Robe, LumenRadio. Interface does the timing. | `pro_fps_limit = 190` (Usb Pro / DMXKing), `ultra_fps_limit = 40` (Ultra DMX Pro) | [ola-usbserial.conf](https://docs.openlighting.org/ola/conf/ola-usbserial.conf.html) |
| `ftdidmx` | "compatible with Enttec Open DMX USB and other FTDI chipset based USB to DMX converters **where the host needs to create the DMX stream itself** and not the interface (the interface has no microprocessor to do so)." | `frequency = 30` — "The DMX stream frequency (30 to 44 Hz max are the usual)." | [ola/plugins/ftdidmx/README.md](https://github.com/OpenLightingProject/ola/blob/master/plugins/ftdidmx/README.md) |
| `uartdmx` | "drives a supported POSIX UART … The host needs to create the DMX stream itself as there is no external microcontroller. This is tested with the on-board UART of the Raspberry Pi." `device = /dev/ttyAMA0`. "Using USB-serial adapters is not supported." | `<device>-break = 100`, `<device>-malf = 100` (µs) | [ola/plugins/uartdmx/README.md](https://github.com/OpenLightingProject/ola/blob/master/plugins/uartdmx/README.md) |
| `opendmx` | Enttec Open DMX USB via the Open DMX kernel module; "if you don't have this installed, use the FTDI DMX USB plugin instead." `device = /dev/dmx0`. | — | [ola-opendmx.conf](https://docs.openlighting.org/ola/conf/ola-opendmx.conf.html) |

The `uartdmx` route pairs with an RS-485 HAT and skips USB entirely:
**RS485 CAN HAT for Raspberry Pi, CAD $19.95, "IN STOCK", SP3485 transceiver, "RS485 function,
controlled via UART", P14/TXD and P15/RXD**
([pishop.ca](https://www.pishop.ca/product/rs485-can-hat-for-raspberry-pi/)). Cheap, but host-timed —
the Pi's Linux scheduler is generating your break and MAB.

### USB DMX interfaces

**ENTTEC DMX USB Pro (70304)** — the reference option. From the datasheet
([cdn.enttec.com/…/70304_DMX_USB_PRO_DATASHEET.pdf](https://cdn.enttec.com/pdf/assets/70304/70304_DMX_USB_PRO_DATASHEET.pdf))
and product page
([enttec.com](https://www.enttec.com/product/dmx-usb-interfaces/dmx-usb-pro-professional-1u-usb-to-dmx512-converter/)):

- "Full 512 DMX channel (1 universe) of input or output." "Fully compliant with USITT DMX512-A."
- "**Output refresh rate configurable from 1 to 40 FPS**"; spec table "Max. output refresh rate 40FPS".
- "Break time is configurable from 96uS to 1.3mS"; "Configurable MAB and Break time using ENTTEC's EMU
  Software to accommodate non-standard equipment."
- "features an internal frame buffer for consistent DMX generation when outputting, meaning timing it
  isn't dependent on your PC's processor."
- "1500V full isolation (data & power lines)"; "RDM enabled (ANSI E1.20 compliant)"; FTDI drivers for
  Windows, macOS, Linux; "Even Raspberry Pi is supported."
- Connectors: "1 x DMX output (female XLR5), 1 x DMX input (male XLR5), 1 x USB 2.0 Type-B" — matches
  the modules' 5-pin XLR directly.
- Power: 5 V via USB, 300 mA, 1.5 W.
- **Price: CAD $227.00, "In Stock - Ship or Pick-up"** at AVShop.ca
  ([avshop.ca](https://www.avshop.ca/lighting-amp-effects-controllers-dimmers-dmx-software-amp-dongles/enttec-dmx-usb-pro)).
- **Conflict to note:** the AVShop copy and an ENTTEC marketing line both claim "up to 850 frames per
  second", while the datasheet and product spec table both say 40 FPS max. Trust the datasheet. Other
  recovered prices from search snippets — StageStore.ca CAD $351.07, Amazon.ca "starting at CAD
  $96.83" — came from search summaries, not fetched product pages; treat them as unverified.

**ENTTEC Open DMX USB (70303)** — USD $70.00 on ENTTEC
([enttec.com](https://www.enttec.com/product/dmx-usb-interfaces/open-dmx-usb/)); **CAD $94.00, "In
Stock - Ship or Pick-up"** at AVShop.ca. "1* DMX Output (Female XLR5), 1* USB 2.0 Type-B", 512
channels, FTDI driver, Windows/macOS/Linux, folded metal. No standalone playback, no MIDI, no config
software, no firmware update, no LED indicators, no RDM. **No refresh-rate spec is published.** The
timing story is the disqualifier: ENTTEC's own latency note says Open DMX USB "does not have an
internal frame buffer or guaranteed consistent frame rate" and "simply converts the DMX values into
DMX frames 1:1 when the computer processor provides them", whereas the Pro models have "an internal
frame buffer allowing them to output DMX at a constant refresh rate independently of the computer's
processor load"
([support.enttec.com/…/latency-on-usb-to-dmx-product](https://support.enttec.com/support/solutions/articles/101000395678-latency-on-usb-to-dmx-product)).
QLC+ adds: "On Windows, Enttec open DMX clones might flicker at 44Hz."

**DMXking ultraDMX Micro / MAX.** The Micro is discontinued and "has been succeeded by the ultraDMX
MAX". DMXking's own discontinued page quotes: "Microprocessor controls DMX512 timing - no flicker
problems like the 'Open' and clones"; "DMX512 Transmitter or Receiver"; "Fully compatible with
software suitable for ENTTEC USB Pro"; "Internal double buffered DMX512 streams resulting in zero
lost frames" ([dmxking.tv/discontinued/ultradmx-micro](https://dmxking.tv/discontinued/ultradmx-micro)).
The MAX is described as having "an internal microcontroller and tough XLR housing, plus Enttec Pro
protocol compatibility … now with USB-C". **No refresh-rate figure, no RDM statement and no price for
either was recovered** — the shop pages returned 403 and the user manual PDF would not parse. OLA's
`usbserial` plugin does list "DMXking USB DMX512-A, Ultra DMX, Ultra DMX Pro".

### Latency

ENTTEC: "Typically there's a couple of milliseconds (1-2 DMX frames) delay between your PC generating
a frame of DMX on its processor and it being output." Quoted verbatim because it is internally
inconsistent — one DMX frame is ≈22.7 ms at full universe, not "a couple of milliseconds". Read it as
1–2 frames. Input direction "can increase to up to 2-3 DMX frames".

### Headless operation and power-loss recovery

The known weak point of a Pi in a hallway is the SD card. Raspberry Pi's own docs give the fix:
`sudo raspi-config` → "4 Performance Options > P2 Overlay File System", which offers "*Set the root
file system to read-only.* This uses a temporary overlay stored in RAM. Any changes made to files
outside of `/boot` while the system is running aren't permanently saved and disappear when you power
off or reboot" and "*Write-protect the boot partition.*" A reboot is required
([raspberrypi/documentation … performance.adoc](https://github.com/raspberrypi/documentation/blob/develop/documentation/asciidoc/computers/configuration/performance.adoc)).
The Raspberry Pi whitepaper *Making a More Resilient File System* (RP-003610-WP) explains corruption
happens when "write operations are interrupted by power loss", describes the overlay as a read-only
lower layer plus a tmpfs upper layer, and for unattended deployments recommends F2FS, read-only root
with a separate read-write data partition, pSLC on Compute Modules, network boot, and
application-level integrity checks
([pip-assets.raspberrypi.com … RP-003610-WP](https://pip-assets.raspberrypi.com/categories/685-whitepapers-app-notes/documents/RP-003610-WP/Making-a-more-resilient-file-system.pdf)).

### Hardware cost

Raspberry Pi 5 / 4GB, PiShop.ca: **CAD $153.95, out of stock**
([pishop.ca](https://www.pishop.ca/product/raspberry-pi-5-4gb/)). The Pi 4 Model B 2GB (SC0193) page
was searched but the price was never fetched — **not in recovered sources.** Garrett already owns
Raspberry Pis, so this is reference pricing only.

### Wave maths

The easiest of any option. Python, a 100-element list, a timer at whatever tick you choose,
`client.SendDmx()`. Full freedom on hill shape, easing, multi-walker handling and speed→colour
mapping.

---

## 5. Art-Net / sACN node

**Garrett already owns it? No.**

**ENTTEC ODE Mk3 (70407)** ([enttec.com](https://www.enttec.com/product/dmx-ethernet/ode-mk3-dmx-ethernet-converter/)):
"2 Universes of Ethernet to DMX conversion" (2U, 1024 ch); protocols "Art-Net / Art-RDM / sACN / ESP"
and "USITT DMX512-A / ANSI E1.20 RDM"; ports "1 x EtherCon Port (RJ45), 2 x Bi-directional DMX (Female
XLR5), 1 x Power Input (DC Jack)"; **DMX output refresh rate "44FPS"**; "Power over Ethernet (PoE) or
a flexible 12-24v DC input", "IEEE 802.3af". **Price: CAD $447.00** at AVShop.ca
([avshop.ca/enttec](https://www.avshop.ca/enttec)).

DMXking's eDMX MAX family (eDMX1/2/4/8 MAX, DIN and ISODIN22 variants) supports "sACN (ANSI E1.31)",
"ArtNet 4", "RDM (ANSI E1.20)", "High quality Neutrik connectors" and a "Built In Show Recorder" with
"Standalone Playback" ([dmxking.com](https://dmxking.com/usbdmx/ultradmx-max)). **No prices and no
refresh rates were recovered.**

An Art-Net node is a way to *reach* DMX over Ethernet — it does not compute anything. It only makes
sense paired with §4, §6 or §7 and mainly buys you distance and a network drop, at roughly 2× the
price of a USB Pro. Given the modules sit about 1 m from wherever the controller lives, it earns its
cost only if the controller has to be elsewhere in the building.

---

## 6. TouchDesigner on a PC

**Garrett already owns it? Not stated — assume no licence.**

- **DMX Out CHOP** "sends channels to DMX, Art-Net, sACN, KiNET, or FTDI devices", with interface
  options "Enttec Generic Serial", "Enttec USB Pro", "Enttec USB Pro Mk2", "Art-Net", "sACN", "KiNET".
  Art-Net addressing is net 0-127 / subnet 0-15 / universe 0-15. The `Rate` parameter is "How often
  data is sent to the device (per second)", with the explicit warning: "**DMX512 devices have a
  maximum refresh rate of 44Hz. It is recommended that Rate <= 44 for reliable performance.**"
  ([docs.derivative.ca/DMX_Out_CHOP](https://docs.derivative.ca/DMX_Out_CHOP))
- Scripting: "The current version of Python shipped with TouchDesigner is 3.11"
  ([docs.derivative.ca/Python](https://docs.derivative.ca/Python)).
- Licences ([derivative.ca/UserGuide/TouchDesigner_Products](https://derivative.ca/UserGuide/TouchDesigner_Products),
  [docs.derivative.ca/TouchDesigner_Non-Commercial](https://docs.derivative.ca/TouchDesigner_Non-Commercial)):
  Non-Commercial free, Educational USD $300, Commercial USD $600, Pro USD $2,200. Non-Commercial is
  "free for non-commercial use **ONLY**. (Precisely, 'You are not receiving money or compensation for
  your work with TouchDesigner')", "image resolution is limited to 1280x1280", excludes "a subset of
  Pro/Commercial Operators", forum support only, and "keys are 1 time use and not transferrable
  between computers. Each account is given 10 keys." **The docs list no DMX/Art-Net/sACN restriction
  on Non-Commercial.**
- **The killer.** System requirements: "Microsoft Windows 10 / Windows 11" or "Apple macOS 13
  (Ventura) and up"; "TouchDesigner requires a GPU and drivers that support Vulkan 1.1"; "A minimum of
  4GB GPU memory, 8GB+ is recommended". **Linux and Raspberry Pi are not listed**
  ([docs.derivative.ca/System_Requirements](https://docs.derivative.ca/System_Requirements)). A
  months-long hallway install would therefore need a Windows or Mac machine with a discrete-class GPU
  living in the hallway, plus Windows Update, plus a GUI session that must survive reboots.
- Wave maths: excellent — CHOPs and Python 3.11 make the hill easy to build and tune visually.
- Power-loss recovery: **not in recovered sources.** Whatever you would build with auto-login and a
  startup shortcut is unverified here.

---

## 7. QLC+ on a PC or Raspberry Pi

**Garrett already owns it? Free software; no licence needed.**

- **Art-Net plugin** ([docs.qlcplus.org/v4/plugins/art-net](https://docs.qlcplus.org/v4/plugins/art-net)):
  native, works on Linux/Windows/macOS, UDP port 6454, broadcast by default, unicast by setting the IP
  in 1-254. Three transmission modes, verbatim: "*Standard* means that DMX universes are transmitted
  only when at least one DMX channel changes or every 2 seconds to refresh receiver's values. *Full*
  means that all the 512 DMX channels of a universe are transmitted at the speed rate of the QLC+
  internal clock (50Hz), producing a fixed bitrate of about 250kbps. *Partial* … will transmit only
  the DMX channel actually used in a universe, starting from channel 1." QLC+ universe N maps to
  Art-Net universe N-1.
- **DMX USB plugin** ([docs.qlcplus.org/v4/plugins/dmx-usb](https://docs.qlcplus.org/v4/plugins/dmx-usb)):
  "supports a variety of FTDI-based USB-to-DMX devices", auto-detected, with forced modes Open TX,
  Open RX, "Pro RX/TX: Enttec USB DMX Pro or most of the DMXKing devices", Pro Mk2, "Ultra Pro: DMXKing
  ultraDMX Pro", DMX4ALL, Vince Tx. Linux needs libftdi and membership of `dialout`; Windows needs FTDI
  D2XX drivers and **not** VCP.
- **OLA plugin** ([docs.qlcplus.org/v4/plugins/ola](https://docs.qlcplus.org/v4/plugins/ola)): "Since
  OLA doesn't run on Windows, only Linux and macOS users can benefit from this plugin." Can start
  `olad` itself via "Run standalone OLA daemon".
- **Headless.** The built-in web server "comes very handy when you need to run QLC+ on a device
  without a display (headless system)", enabled with `-w`/`--web`, reachable at `http://[IP]:9999`,
  with a websocket web API
  ([docs.qlcplus.org/v4/advanced/web-interface](https://docs.qlcplus.org/v4/advanced/web-interface)).
  Kiosk mode: `qlcplus -k -f -o workspace.qxw -p -c 500,10,32,32` — `-k` kiosk, `-f` fullscreen, `-o`
  workspace, `-p` operate mode
  ([docs.qlcplus.org/v4/advanced/kiosk-mode](https://docs.qlcplus.org/v4/advanced/kiosk-mode)).
- **Pi image.** Per QLC+ site and forum material recovered via search: supports every 64-bit Pi (3, 4,
  400, 5, Zero 2W), fits a 4 GB card, no Xorg, includes the web interface and all plugins including
  OLA, UART, GPIO and SPI; place `autostart.qxw` in `/root/.qlcplus` and QLC+ loads it at boot; web UI
  reachable roughly 30 s after boot. Obtained "through a donation link in the reserved area". **The
  authoritative pages (qlcplus.org/raspberry, the Pi guide PDF) both returned 403, so this paragraph
  rests on search summaries, not fetched primary pages.**
- **The killer.** QLC+'s Script function language has no arithmetic. The full recovered keyword list
  is `startfunction`, `stopfunction`, `blackout`, `systemcommand`, `setfixture` (`setfixture:fixtureID
  ch:channelIndex val:DMXValue`), `wait`, plus a random-number helper
  ([docs.qlcplus.org/v4/function-manager/script-editor](https://docs.qlcplus.org/v4/function-manager/script-editor)).
  There is no way to express "hill centred on a position that moves continuously with a sensor".
  `systemcommand` can shell out to an external program — but at that point the external program is
  doing the work and QLC+ is only a DMX driver, which OLA does more directly. **Reasoning, not a
  quote:** on that basis QLC+ is redundant for this job.

---

## 8. Standalone controllers with trigger inputs

**Garrett already owns it? No.**

| Product | Price | Inputs | Logic | Source |
|---|---|---|---|---|
| ENTTEC S-Play Mini | USD $400.00 / **CAD $532.00** (AVShop) | "4 digital inputs + 1 GND (5-pin Phoenix screw terminal)", 1 relay, OSC API, UDP, DMX/Art-Net/sACN triggers | Playlists only. "Playlists can loop on power-up or be triggered externally" | [enttec.com](https://www.enttec.com/product/light-show-control/s-play-mini-2-universe-smart-light-show-controller/), [avshop.ca/enttec](https://www.avshop.ca/enttec) |
| ENTTEC S-Play SP1-1 | price not on page; **CAD $3,059.00** (AVShop, "S-Play DMX Recorder/Editor/Playback") | "4 Digital Inputs (GPI)"; triggers via "RS232, UDP, OSC, Digital Input (GPI), Art-Net, sACN and DMX"; schedules; "**No Analog Inputs** … the I/O Extender accessory can provide analog trigger capability"; "On Power Up" playlist start | Playlists only | [support.enttec.com/user-manuals/s-play-sp1-1](https://support.enttec.com/user-manuals/s-play-sp1-1) |
| ENTTEC S-Play Nano | **CAD $266.00** (AVShop) | not in recovered sources | not in recovered sources | [avshop.ca/enttec](https://www.avshop.ca/enttec) |
| Pharos Designer LPC 1/2/4 | not shown | "Eight inputs, individually selectable operating mode for contact closure, digital or analog input", RIO modules, DMX in, "send/receive any Ethernet message" | **"Lua scripting for total flexibility"**; "commences programmed playback automatically on receiving power"; RDM | [pharoscontrols.com](https://www.pharoscontrols.com/products/controllers/lpc/) |
| Nicolaudie DINA-DR1 | "Public price (excluding VAT): US$ 2399" | "8" dry contact ports, RS232, Ethernet, TCP/UDP, time/date, DALI, audio. No analog stated | Scenes and zones; "full recovery after power lose" | [nicolaudie.com/dina-dr1.htm](https://www.nicolaudie.com/dina-dr1.htm) |

The S-Play family plays back *recorded* playlists on contact closure. It cannot take a continuously
varying walker position and compute a hill from it — its 4 digital inputs are on/off events. The
Pharos LPC is the only one with real programmability (Lua) and analog inputs, which makes it
technically capable, but its price was never recovered and it is architecturally overkill for 100
channels.

---

## Comparison

| Option | DMX rate | Latency | Wave maths | New hardware / cost | Headless + power-loss | Garrett already owns it? |
|---|---|---|---|---|---|---|
| **MADRIX USB ONE** (owned) | not in recovered sources | not in recovered sources | depends on host software | CAD $0 | depends on host | **Yes** |
| **HB-Laser USB-DMX-RDM** (owned) | not in recovered sources | not in recovered sources | depends on host software | CAD $0 | depends on host | **Yes** |
| ESP32 + `esp_dmx` + MAX485 | Configurable break/MAB; `dmx_send_num()` for a 100-slot frame; ~22 ms for a full packet | Sensor→frame is in-process; no USB or OS in the path | C on the MCU; total freedom, no visual tooling | MAX485 module CAD $2.50 (+ XLR-5 wiring, not priced) | Best: no filesystem; IWDT hard-resets, TWDT resets if `CONFIG_ESP_TASK_WDT_PANIC` | ESP32 **yes**; transceiver unknown |
| ESP32 + SparkFun DEV-15110 | as above | as above | as above | CAD $30.22 (DigiKey.ca, 64 in stock) + XLR-3→XLR-5 adapter (not priced) | as above | No |
| Pi + OLA + Enttec DMX USB Pro | 1-40 FPS configurable, 40 FPS max; internal frame buffer, timing independent of the host | "a couple of milliseconds (1-2 DMX frames)" per ENTTEC | Python; easiest of all | CAD $227.00 (AVShop, in stock) | Overlay FS read-only root; `olad` boot behaviour not documented on the Pi page | Pi **yes**; interface no |
| Pi + OLA + Open DMX USB | no published refresh rate; host-timed, "no internal frame buffer or guaranteed consistent frame rate" | worse and jittery | Python | USD $70 / CAD $94.00 (AVShop) | same, but timing degrades under load | No |
| Pi + OLA `uartdmx` + RS485 HAT | host-timed; per-device break/MALF in µs | in-process, but Linux-scheduled | Python | CAD $19.95 (PiShop, in stock) | same | Pi **yes**; HAT no |
| Pi/PC + Art-Net node (ODE Mk3) | 44 FPS | plus one network hop | depends on host | CAD $447.00 (AVShop) | node itself is appliance-grade | No |
| TouchDesigner on a PC | `Rate` param; "Rate <= 44" recommended | not in recovered sources | Best: CHOPs + Python 3.11 | Non-Commercial free (not for paid work) / Commercial USD $600, **plus a Windows/macOS machine with a Vulkan 1.1 GPU, 4 GB+ VRAM** | No Linux/Pi support; recovery behaviour not in recovered sources | No |
| QLC+ (PC or Pi image) | Art-Net Full mode = 50 Hz internal clock | not in recovered sources | **Cannot do it** — Script language has no arithmetic | Free | Good: `-w` web UI on :9999, kiosk mode, Pi image with `autostart.qxw` | Free |
| ENTTEC S-Play Mini / SP1-1 | not in recovered sources | event-driven | **Cannot do it** — playlists on 4 digital inputs, no analog | CAD $532 / CAD $3,059 | "loop on power-up" / "On Power Up" | No |
| Pharos LPC | not in recovered sources | not in recovered sources | Lua scripting, analog inputs | price not in recovered sources | "commences programmed playback automatically on receiving power" | No |
| Nicolaudie DINA-DR1 | not in recovered sources | not in recovered sources | Scenes/zones, no continuous mapping | USD $2,399 | "full recovery after power lose" | No |

---

## Recommendation

**Default: ESP32 running `esp_dmx` into an RS-485 transceiver, unless one of the owned dongles turns
out to be OLA-drivable.**

Why, with the reason for each:

1. **Cost.** CAD $2.50 for the MAX485 module against CAD $227 for the cheapest USB interface with
   hardware timing, on a microcontroller Garrett already owns.
2. **Timing.** The ESP32's hardware UART generates the break, MAB and slots directly, with
   `dmx_set_break_len()` / `dmx_set_mab_len()` if the modules turn out fussy. No USB stack, no Linux
   scheduler, no FTDI driver between the maths and the wire.
3. **Months unattended.** No SD card to corrupt. The Interrupt Watchdog hard-resets the chip on a
   second-stage timeout, and the Task Watchdog can be made to reset with `CONFIG_ESP_TASK_WDT_PANIC`.
   A Pi needs the overlay filesystem configured and `olad` boot-start verified; a PC running
   TouchDesigner needs far more.
4. **Frame size.** `dmx_send_num()` lets the 100 live slots go out as a 100-slot packet. By the
   ENTTEC arithmetic that is ≈4.6 ms of data per frame (derived), so headroom is generous even if you
   stay at 44 Hz.

**Conditions on that recommendation:**

- **Answer the MADRIX question first.** If the MADRIX USB ONE or the HB-Laser USB-DMX-RDM turns out
  to be Enttec-Pro-API compatible, or otherwise appears in OLA's full device list, the Pi + OLA +
  Python path becomes free in hardware terms and is materially easier to write and debug (Python, a
  keyboard, `ssh`). At that point it beats the ESP32 on developer time and loses only on power-loss
  robustness — which the overlay filesystem largely closes. **Test:** plug each dongle into a Pi,
  run `olad -l 3`, then check `http://<pi-ip>:9090` for a device.
- **Confirm which ESP32 board Garrett actually has.** The `esp_dmx` README does not enumerate
  supported variants; the source only proves an ESP32-C3 code path exists in `timer.c`.
- **Confirm the transceiver's logic levels.** `esp_dmx` claims "Many RS-485 chips, such as the Maxim
  MAX485 are 3.3v tolerant", but the PiShop module is listed at 5 V working voltage and the MAX485
  datasheet was never read. Either verify on the bench or pick a documented 3.3 V transceiver.
- **XLR-5 wiring is unsolved either way.** The modules terminate in 5-pin XLR; a bare transceiver
  module has screw terminals and the SparkFun shield has XLR-3. Neither an XLR-5 chassis connector nor
  a 3→5 adapter appears with a price in the recovered sources.

**Ruled out, with the reason:**

- **QLC+** — its Script language has only `startfunction`/`stopfunction`/`blackout`/`systemcommand`/
  `setfixture`/`wait`. No arithmetic, so the hill cannot be expressed in it.
- **TouchDesigner** — Windows 10/11 or macOS 13+ with a Vulkan 1.1 GPU only; no Linux or Pi. A GPU PC
  in a hallway for months is the wrong shape of problem, and the Non-Commercial licence forbids paid
  work.
- **ENTTEC S-Play family** — playlist playback triggered by 4 digital on/off inputs, explicitly no
  analog inputs on the SP1-1. It cannot map a continuous position to a moving hill.
- **Art-Net node** — correct technology, but it only moves DMX across a network; it computes nothing,
  and at CAD $447 it earns its keep only if the controller cannot sit next to the basin.

---

## Gaps

1. **MADRIX USB ONE — everything.** No product page, no driver info, no refresh rate, no price, and
   no confirmation either way on OLA support. The two OLA plugin device lists that were recovered do
   not name it, but they are only two plugins out of the full set. **This decides the whole choice
   and is the first thing to resolve.**
2. **HB-Laser USB-DMX-RDM — everything.** Not fetched at all by either agent.
3. **The full OLA device list** (the "device list" link on `openlighting.org/ola/`) was never fetched.
   That page is where gaps 1 and 2 would most likely be answered.
4. **Whether `olad` starts at boot on a Pi.** The OLA Pi tutorial shows a manual `olad -l 3` and says
   nothing about a systemd unit.
5. **MAX485 electrical margin at 3.3 V drive.** The datasheet fetch never landed; only the `esp_dmx`
   author's claim is on record, against a PiShop listing that says 5 V working voltage.
6. **Which ESP32 variants `esp_dmx` supports.** Not enumerated in the README; only a C3 guard in
   `timer.c` was found.
7. **XLR-5 connectors and adapters** — no part, no supplier, no price recovered.
8. **Whether the HydroMatrix modules accept short (100-slot) or faster-than-44 Hz frames.** Bench
   measurement; issue #2 already flagged the fountain-height channel mapping as unmeasured.
9. **TouchDesigner power-loss / auto-restart behaviour** — not in recovered sources.
10. **QLC+ Raspberry Pi image primary sources** — `qlcplus.org/raspberry` and the Pi guide PDF both
    returned 403. The Pi-image paragraph in §7 rests on search summaries.
11. **DMXking ultraDMX MAX** — no price, no refresh rate, no RDM statement; shop page 403, manual PDF
    unparseable.
12. **Pharos LPC price** — not shown on the product page.
13. **Raspberry Pi 4 Model B 2GB price at PiShop.ca** — searched, never fetched.
14. **Enttec DMX USB Pro price conflict** — CAD $227 (AVShop, fetched) vs CAD $351.07 (StageStore,
    search snippet) vs CAD $96.83 (Amazon.ca, search snippet). Only the AVShop figure came from a
    fetched page.
15. **"850 frames per second" vs "40 FPS max"** for the DMX USB Pro — marketing copy contradicts the
    datasheet. The datasheet is preferred here; unresolved.

---

## Sources

Pages that were actually read, and are cited above.

**Standard**
- ANSI E1.11-2008 (R2018) DMX512-A, Tables 6 and 7 — https://tsp.esta.org/tsp/documents/docs/ANSI-ESTA_E1-11_2008R2018.pdf
- ENTTEC, "What is DMX512? Channels, Universes and Timing Explained" — https://support.enttec.com/dmx/dmx-basics/what-is-dmx512

**ESP32**
- esp_dmx repository and README — https://github.com/someweisguy/esp_dmx
- esp_dmx `library.json`, `library.properties`, `src/dmx/hal/timer.c` — https://github.com/someweisguy/esp_dmx
- SparkFun ESP32 Thing Plus DMX to LED Shield repo and Eagle schematic — https://github.com/sparkfun/SparkFun_ESP32_Thing_Plus_DMX_to_LED_Shield
- SparkFunDMX library — https://github.com/sparkfun/SparkFunDMX
- SparkFun hookup guide — https://learn.sparkfun.com/tutorials/sparkfun-esp32-dmx-to-led-shield/all
- SparkFun product page — https://www.sparkfun.com/sparkfun-esp32-thing-plus-dmx-to-led-shield.html
- ESP-IDF watchdog timers — https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/wdts.html

**OLA / Raspberry Pi**
- Open Lighting Architecture — https://www.openlighting.org/ola/
- OLA Python API — https://www.openlighting.org/ola/developer-documentation/python-api/
- OLA on Raspberry Pi — https://www.openlighting.org/ola/tutorials/ola-on-raspberry-pi/
- OLA USB plugin config — https://docs.openlighting.org/ola/conf/ola-usbdmx.conf.html
- OLA serial USB plugin config — https://docs.openlighting.org/ola/conf/ola-usbserial.conf.html
- OLA Open DMX plugin config — https://docs.openlighting.org/ola/conf/ola-opendmx.conf.html
- OLA plugin READMEs (uartdmx, usbserial, ftdidmx) — https://github.com/OpenLightingProject/ola
- Debian bookworm `ola` package — https://packages.debian.org/bookworm/ola
- Raspberry Pi performance/config docs (Overlay File System) — https://github.com/raspberrypi/documentation/blob/develop/documentation/asciidoc/computers/configuration/performance.adoc
- Raspberry Pi, *Making a More Resilient File System* (RP-003610-WP) — https://pip-assets.raspberrypi.com/categories/685-whitepapers-app-notes/documents/RP-003610-WP/Making-a-more-resilient-file-system.pdf

**Interfaces and nodes**
- ENTTEC DMX USB Pro product page — https://www.enttec.com/product/dmx-usb-interfaces/dmx-usb-pro-professional-1u-usb-to-dmx512-converter/
- ENTTEC DMX USB Pro datasheet (70304) — https://cdn.enttec.com/pdf/assets/70304/70304_DMX_USB_PRO_DATASHEET.pdf
- ENTTEC DMX USB Pro (protocols page) — https://www.enttec.com/product/lighting-communication-protocols/dmx512/dmx-usb-pro/
- ENTTEC Open DMX USB — https://www.enttec.com/product/dmx-usb-interfaces/open-dmx-usb/
- ENTTEC, "Latency on USB to DMX Product" — https://support.enttec.com/support/solutions/articles/101000395678-latency-on-usb-to-dmx-product
- ENTTEC, "DMX USB Pro Mk2 API" — https://support.enttec.com/support/solutions/articles/101000396178-dmx-usb-pro-mk2-api
- ENTTEC ODE Mk3 — https://www.enttec.com/product/dmx-ethernet/ode-mk3-dmx-ethernet-converter/
- DMXking ultraDMX Micro (discontinued) — https://dmxking.tv/discontinued/ultradmx-micro
- DMXking ultraDMX MAX — https://dmxking.com/usbdmx/ultradmx-max

**Software**
- TouchDesigner DMX Out CHOP — https://docs.derivative.ca/DMX_Out_CHOP
- TouchDesigner Python — https://docs.derivative.ca/Python
- TouchDesigner System Requirements — https://docs.derivative.ca/System_Requirements
- TouchDesigner Products (pricing) — https://derivative.ca/UserGuide/TouchDesigner_Products
- TouchDesigner Non-Commercial — https://docs.derivative.ca/TouchDesigner_Non-Commercial
- QLC+ Art-Net plugin — https://docs.qlcplus.org/v4/plugins/art-net
- QLC+ DMX USB plugin — https://docs.qlcplus.org/v4/plugins/dmx-usb
- QLC+ OLA plugin — https://docs.qlcplus.org/v4/plugins/ola
- QLC+ Script Editor — https://docs.qlcplus.org/v4/function-manager/script-editor
- QLC+ Web Interface — https://docs.qlcplus.org/v4/advanced/web-interface
- QLC+ Kiosk Mode — https://docs.qlcplus.org/v4/advanced/kiosk-mode

**Standalone controllers**
- ENTTEC S-Play Mini — https://www.enttec.com/product/light-show-control/s-play-mini-2-universe-smart-light-show-controller/
- ENTTEC S-Play SP1-1 user manual — https://support.enttec.com/user-manuals/s-play-sp1-1
- ENTTEC S-Play SP1-1 product page — https://www.enttec.com/product/light-show-control/s-play-sp1-32-universe-smart-light-show-controller/
- Pharos Designer LPC — https://www.pharoscontrols.com/products/controllers/lpc/
- Nicolaudie DINA-DR1 — https://www.nicolaudie.com/dina-dr1.htm

**Canadian pricing**
- AVShop.ca ENTTEC catalogue — https://www.avshop.ca/enttec
- AVShop.ca ENTTEC DMX USB Pro — https://www.avshop.ca/lighting-amp-effects-controllers-dimmers-dmx-software-amp-dongles/enttec-dmx-usb-pro
- AVShop.ca ENTTEC Open DMX USB — https://www.avshop.ca/lighting-amp-effects-controllers-dimmers-dmx-software-amp-dongles/enttec-open-dmx-usb-interface
- PiShop.ca MAX485 module — https://www.pishop.ca/product/max-485-module-rs-485-module-ttl-to-rs-485-converter-module/
- PiShop.ca RS485 CAN HAT — https://www.pishop.ca/product/rs485-can-hat-for-raspberry-pi/
- PiShop.ca Raspberry Pi 5 4GB — https://www.pishop.ca/product/raspberry-pi-5-4gb/
- DigiKey.ca SparkFun DEV-15110 — https://www.digikey.ca/en/products/detail/sparkfun-electronics/DEV-15110/10054912
- DigiKey.ca ESP32-DEVKITC-32E — https://www.digikey.ca/en/products/detail/espressif-systems/ESP32-DEVKITC-32E/12091810
- Elmwood Electronics SparkFun RS-485 breakout (SP3485) — https://elmwoodelectronics.ca/products/10124

**Repo**
- Issue #2 research result: `docs/research/hb-laser-single-module-manual.md` on branch `research/hb-laser-module-manual`
