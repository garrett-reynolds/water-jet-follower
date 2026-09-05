"""DMX output to the HB-Laser modules, through olad.

Every frame this module sends is a full 512 slots. That is deliberate and it is the
whole reason the zero path can be trusted. A short DMX frame updates only the slots
it carries, and most fixtures hold the rest of the universe at their last value, so
a five-slot "all off" would leave slot 5 exactly where it was - which is to say, a
jet still up. Sending 512 every time makes the question moot by construction.

Channel map, from the module datasheet: 5 channels per nozzle, in the order
red, green, blue, white, fountain height. Ten nozzles to an HD module, 50 channels
to a module. So nozzle n (counting from 1) owns channels 5n-4 .. 5n, and the pump
is always the last of the five.

Frames are `array.array("B")`, not `bytearray`. OLA's SendDmx calls `.tobytes()`
on what it is given, which `array` has and `bytearray` does not.

`ola` is imported inside the functions, not at the top. It is a system package on
the Pi and is not installed on the laptop, and the arithmetic here is worth testing
without it.
"""

import array
import contextlib
import sys

UNIVERSE_SIZE = 512
CHANNELS_PER_NOZZLE = 5
NOZZLES_PER_HD_MODULE = 10

RED, GREEN, BLUE, WHITE, HEIGHT = 0, 1, 2, 3, 4
COLOUR_NAMES = {"red": RED, "green": GREEN, "blue": BLUE, "white": WHITE,
                "height": HEIGHT}


def channel_for(nozzle, role, nozzles_per_module=NOZZLES_PER_HD_MODULE, module=1):
    """1-based DMX channel for one role of one nozzle.

    `nozzle` and `module` both count from 1, because that is how the datasheet and
    every DMX tool count. `role` is a name from COLOUR_NAMES or a 0-based offset.
    """
    if nozzle < 1 or nozzle > nozzles_per_module:
        raise ValueError(f"nozzle {nozzle} outside 1..{nozzles_per_module}")
    if module < 1:
        raise ValueError(f"module {module} must be 1 or more")
    offset = COLOUR_NAMES[role] if isinstance(role, str) else role
    if not 0 <= offset < CHANNELS_PER_NOZZLE:
        raise ValueError(f"role offset {offset} outside 0..4")
    module_base = (module - 1) * nozzles_per_module * CHANNELS_PER_NOZZLE
    return module_base + (nozzle - 1) * CHANNELS_PER_NOZZLE + offset + 1


def blank_frame():
    """512 slots, all zero. The safe state."""
    return array.array("B", [0] * UNIVERSE_SIZE)


def frame_with(channel, value):
    """A full 512-slot frame, zero everywhere but one channel.

    This is the only shape the jog tool ever sends. One channel moves, and every
    other channel in the universe is actively driven to zero rather than left alone.
    """
    if channel < 1 or channel > UNIVERSE_SIZE:
        raise ValueError(f"channel {channel} outside 1..{UNIVERSE_SIZE}")
    frame = blank_frame()
    frame[channel - 1] = clamp(value)
    return frame


def clamp(value, low=0, high=255):
    return max(low, min(high, int(value)))


# --- talking to olad ----------------------------------------------------

def send(frame, universe=1):
    """Send one frame and block until olad has taken it.

    ClientWrapper is an event loop and SendDmx does not reach the socket until the
    loop runs, so the callback stops the loop and turns this back into a plain
    synchronous call.
    """
    # Length check first, before the import. A short frame is a bug worth catching
    # on the laptop, where there is no ola package to import.
    if len(frame) != UNIVERSE_SIZE:
        raise ValueError(f"refusing to send {len(frame)} slots, must be "
                         f"{UNIVERSE_SIZE} - see this module's docstring")

    from ola.ClientWrapper import ClientWrapper

    wrapper = ClientWrapper()
    result = {}

    def sent(status):
        result["ok"] = status.Succeeded()
        wrapper.Stop()

    wrapper.Client().SendDmx(universe, frame, sent)
    wrapper.Run()
    return result.get("ok", False)


def fetch(universe=1):
    """Read back what olad holds. Returns a list of ints, empty if olad has none.

    olad hands the callback `data=None` when the request fails - which happens when
    the universe has no device bound to it, for instance because the interface was
    unplugged. Guard it, because this runs inside the stop path.
    """
    from ola.ClientWrapper import ClientWrapper

    wrapper = ClientWrapper()
    result = {}

    def got(status, _universe, data):
        result["ok"] = status.Succeeded()
        result["data"] = list(data) if data else []
        wrapper.Stop()

    wrapper.Client().FetchDmx(universe, got)
    wrapper.Run()
    return result.get("data", [])


def zero(universe=1, verbose=True):
    """Drive every slot to zero and prove it landed.

    Called from the jog tool's exit path and available on its own as
    `tracker.run zero`. Read back rather than trusted: "I sent zeros" and "olad
    holds 512 zeros" are different claims, and only the second one is worth
    anything with water in the basin.
    """
    ok = send(blank_frame(), universe)
    held = fetch(universe)
    clean = len(held) == UNIVERSE_SIZE and not any(held)
    if verbose:
        if not held:
            # Not "everything is off". olad could not tell us anything at all,
            # usually because nothing is bound to the universe. The modules latch
            # their last value, so silence here means the jets may still be up.
            print(f"zero: sent={ok} but olad returned NO DATA for universe "
                  f"{universe} - is the interface plugged in? "
                  f"THE MODULES MAY STILL BE HOLDING A VALUE. Check ola_dev_info, "
                  f"and use the 24 V switch if anything is up.")
        else:
            nonzero = [(i + 1, v) for i, v in enumerate(held) if v]
            print(f"zero: sent={ok} slots_held={len(held)} "
                  f"{'ALL ZERO' if clean else f'STILL SET {nonzero[:10]}'}")
    return clean


def height_channels(jet_count, nozzles_per_module=NOZZLES_PER_HD_MODULE):
    """1-based DMX channels carrying fountain height, for a strip of `jet_count`.

    Jets run across modules: jet 0 is module 1 nozzle 1, jet 10 is module 2
    nozzle 1. Returns them in jet order.
    """
    channels = []
    for jet in range(jet_count):
        module = jet // nozzles_per_module + 1
        nozzle = jet % nozzles_per_module + 1
        channels.append(channel_for(nozzle, HEIGHT, nozzles_per_module, module))
    return channels


def clamp_heights(frame, cap, jet_count):
    """Force every fountain-height slot down to `cap`. Colour slots are untouched.

    This is the last thing that runs before a frame goes out, and it is the only
    guard that does not depend on the wave logic being correct. The modules latch
    their last value, so one wrong height written once stays up until somebody cuts
    the 24 V. See the latch entry in DECISIONS.md.
    """
    cap = clamp(cap)
    for channel in height_channels(jet_count):
        if frame[channel - 1] > cap:
            frame[channel - 1] = cap
    return frame


@contextlib.contextmanager
def safe_output(universe=1, verbose=True):
    """Hold the DMX line, and put it back to zero whatever happens.

    This is the stop path that was proven on hardware with nozzle 1's red LED:
    the LED went out when the process was killed. Both `jog` and `show` run inside
    it so there is only ever one such path, and it is the tested one.

    It does NOT save you if olad dies, the interface is unplugged, or the process
    is SIGKILLed. The modules hold their last value forever in all three cases.
    The only stop that covers those is the switch on the 24 V supply.
    """
    import atexit
    import signal

    def stop(reason):
        try:
            zero(universe, verbose=verbose)
        except Exception as exc:                # never let the stop path throw
            print(f"\nZERO FAILED ({reason}): {exc}\n"
                  f"PULL THE 24 V POWER.", file=sys.stderr)

    atexit.register(stop, "atexit")

    def on_signal(signum, _frame):
        print(f"\ncaught {signal.Signals(signum).name}")
        raise SystemExit(0)                     # lets the finally below run

    previous = {}
    for name in ("SIGINT", "SIGTERM", "SIGHUP"):
        if hasattr(signal, name):
            number = getattr(signal, name)
            previous[number] = signal.signal(number, on_signal)

    if not zero(universe, verbose=verbose):
        raise RuntimeError(
            "olad is not holding 512 zeros - refusing to start. "
            "Check ola_dev_info, and use the 24 V switch if anything is up.")
    try:
        yield
    finally:
        stop("exit")
        atexit.unregister(stop)
        for number, handler in previous.items():
            signal.signal(number, handler)
