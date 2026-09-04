"""Record scans to disk and play them back.

The Pi runs Raspberry Pi OS Lite, so there is no window to plot in and no way to
re-run a walk-past on demand. Recordings are how the tracker gets tuned without
somebody standing in the hallway.

Format is JSON Lines. Line 1 is a header, every line after it is one revolution:

    {"format": "wj-scan", "version": 1, "started": 1757030000.0, "notes": "..."}
    {"t": 1757030000.07, "p": [[angle_deg, distance_mm], ...]}
"""

import json
import math
import time

FORMAT = "wj-scan"
VERSION = 1


def record(source, path, seconds, notes=""):
    """Write `seconds` of scans from `source` (a Lidar.scans() generator) to `path`."""
    started = time.time()
    count = 0
    with open(path, "w") as handle:
        handle.write(json.dumps({
            "format": FORMAT, "version": VERSION,
            "started": started, "notes": notes,
        }) + "\n")
        for timestamp, points in source:
            handle.write(json.dumps({
                "t": round(timestamp, 4),
                "p": [[round(a, 3), round(d, 1)] for a, d in points],
            }) + "\n")
            count += 1
            elapsed = time.time() - started
            if elapsed >= seconds:
                break
            if count % 15 == 0:
                print(f"\r  {elapsed:5.1f}s  {count} scans", end="", flush=True)
    elapsed = time.time() - started
    print(f"\rrecorded {count} scans in {elapsed:.1f}s "
          f"({count / elapsed:.2f} Hz) to {path}")
    return count


def read(path):
    """Yield (timestamp, points) from a recording. Skips the header line."""
    with open(path) as handle:
        header = json.loads(handle.readline())
        if header.get("format") != FORMAT:
            raise ValueError(f"{path} is not a {FORMAT} file")
        for line in handle:
            line = line.strip()
            if not line:
                continue
            scan = json.loads(line)
            yield scan["t"], [(a, d) for a, d in scan["p"]]


def replay(path, speed=1.0, loop=False):
    """Yield (timestamp, points) in real time, so the tracker sees true scan gaps."""
    while True:
        first_real = None
        wall_start = time.time()
        for timestamp, points in read(path):
            if first_real is None:
                first_real = timestamp
            if speed > 0:
                target = (timestamp - first_real) / speed
                lag = target - (time.time() - wall_start)
                if lag > 0:
                    time.sleep(lag)
            yield timestamp, points
        if not loop:
            return


# --- background baseline ------------------------------------------------

def build_baseline(path, cfg):
    """Per-angle-bin horizon distance, in metres. Bins never hit stay at infinity.

    The horizon is a low **percentile** of that bin's distances, not the minimum.
    The minimum is what a room with nobody in it wants, but this room cannot be
    emptied - somebody has to be in it to start the recording, and clutter comes
    and goes from the scan.

    Sort a bin's returns nearest first. A person standing in that bin for a
    fraction f of the clip owns the first f of the list. Take the percentile p and
    the person is ignored whenever p > f, while a static object that answers for
    more than p of the clip is still captured. So p sits between "how long a person
    lingers on any one bearing" and "how reliably the furniture answers".

    `background_percentile` defaults to 0.2. At 0.0 this is exactly the old
    nearest-distance rule.
    """
    return build_baseline_from_scans(read(path), cfg)


def build_baseline_from_scans(scans, cfg):
    """Same as build_baseline, but from any (timestamp, points) source."""
    bins = int(round(360.0 / cfg.background_bin_deg))
    seen = [[] for _ in range(bins)]
    count = 0
    for _, points in scans:
        count += 1
        for angle, distance_mm in points:
            metres = distance_mm / 1000.0
            if metres < cfg.range_min:
                continue
            seen[int(angle / cfg.background_bin_deg) % bins].append(metres)

    baseline = [_percentile(values, cfg.background_percentile) for values in seen]
    return {
        "bin_deg": cfg.background_bin_deg,
        "scans": count,
        "percentile": cfg.background_percentile,
        "distances": [None if math.isinf(d) else round(d, 4) for d in baseline],
    }


def _percentile(values, fraction):
    """Nearest-rank percentile of a bin's distances. Empty bin -> infinity."""
    if not values:
        return math.inf
    values = sorted(values)
    index = int(fraction * (len(values) - 1))
    return values[index]


def save_baseline(baseline, path):
    with open(path, "w") as handle:
        json.dump(baseline, handle)
    filled = sum(1 for d in baseline["distances"] if d is not None)
    print(f"baseline: {filled}/{len(baseline['distances'])} bins filled "
          f"from {baseline['scans']} scans -> {path}")


def load_baseline(path):
    with open(path) as handle:
        baseline = json.load(handle)
    baseline["distances"] = [math.inf if d is None else d
                             for d in baseline["distances"]]
    return baseline
