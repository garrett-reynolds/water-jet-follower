"""Make a two-person recording out of two one-person recordings.

Issue #12 asks whether one A2M8 survives two walkers crossing. That needs two
people. It does not need them at the same time.

A 2D LiDAR reports **the nearest thing on each ray**. Nothing else. So if one clip
has a walker going left to right and another clip has a walker going right to left,
taking the nearer return of the two clips on every ray gives exactly the scan the
sensor would have produced with both people in the room - shadows included. A body
in front really does hide the body behind it, because its return is nearer and wins
the ray. This is not an approximation of occlusion; it is the same rule the hardware
uses.

What it cannot reproduce is the two people reacting to each other - stepping aside,
slowing down, bumping. The question on the ticket is about the sensor, not about
manners, so that is an acceptable loss and it is stated here so nobody forgets it.

`--shift-b` is the useful knob. It slides the second clip in time, which moves where
the two walkers meet. One pair of recordings therefore gives the whole sweep: they
cross right in front of the sensor (worst shadow), cross at the far end (mildest),
or never meet at all (the control).
"""

import json
import math

from tracker import scanfile

# The measured sample spacing at PWM 800: 503 samples per turn.
DEFAULT_BIN_DEG = 360.0 / 503.0


def _relative(stream):
    """(t, points) list -> (seconds since the clip started, points) list."""
    if not stream:
        return []
    first = stream[0][0]
    return [(t - first, points) for t, points in stream]


def merge_scans(streams, shifts=None, bin_deg=DEFAULT_BIN_DEG):
    """Merge several scan streams into one, by nearest return per ray.

    `streams` is a list of [(timestamp, points), ...]. The first one is the clock:
    every output scan lines up with one of its scans, and the others contribute
    whichever of their scans is nearest in time. `shifts` slides each later stream
    in seconds, positive meaning "this walker set off later".

    Rays are matched by binning the angle at `bin_deg`, which is the sensor's own
    sample spacing, so two points only compete when they are the same ray. The angle
    that gets written out is the winning point's real angle, not the bin's, so
    nothing is quantised in the result.

    Outside a clip's own span - before it starts or after it ends, once shifted -
    its nearest scan is held. In practice that means the walker stands still at
    their start or end point, which is what a real recording of them waiting to set
    off would have looked like anyway.
    """
    if not streams:
        return []
    shifts = list(shifts or [])
    shifts += [0.0] * (len(streams) - len(shifts))

    reference = _relative(streams[0])
    others = []
    for stream, shift in zip(streams[1:], shifts[1:]):
        others.append([(t + shift, points) for t, points in _relative(stream)])

    bins = int(round(360.0 / bin_deg))
    merged = []

    for index, (relative_time, points) in enumerate(reference):
        ray = {}
        _fill(ray, points, bin_deg, bins)
        for other in others:
            match = _nearest_in_time(other, relative_time)
            if match is not None:
                _fill(ray, match, bin_deg, bins)
        winners = sorted(ray.values(), key=lambda point: point[0])
        merged.append((streams[0][index][0], winners))

    return merged


def _fill(ray, points, bin_deg, bins):
    """Drop each point into the ray slot it is nearest to, keeping the nearer hit.

    Rounding, not truncating. Truncating put two neighbouring rays in one slot
    whenever floating point landed a hair under the boundary, which silently threw
    away a third of the points.
    """
    for angle, distance in points:
        index = int(round(angle / bin_deg)) % bins
        current = ray.get(index)
        if current is None or distance < current[1]:
            ray[index] = (angle, distance)


def _nearest_in_time(stream, target):
    """The scan whose time is closest to `target`, or None if the clip is silent."""
    best = None
    best_gap = None
    for time_value, points in stream:
        gap = abs(time_value - target)
        if best_gap is None or gap < best_gap:
            best_gap, best = gap, points
        elif time_value > target:
            break                       # times only increase, so this is the turn
    return best


def merge_files(paths, out, shifts=None, bin_deg=DEFAULT_BIN_DEG):
    streams = [list(scanfile.read(path)) for path in paths]
    for path, stream in zip(paths, streams):
        if not stream:
            raise ValueError(f"{path} has no scans")
    merged = merge_scans(streams, shifts, bin_deg)

    shifts = list(shifts or [])
    shifts += [0.0] * (len(paths) - len(shifts))
    description = " + ".join(f"{path}@{shift:+.2f}s"
                             for path, shift in zip(paths, shifts))

    with open(out, "w") as handle:
        handle.write(json.dumps({
            "format": scanfile.FORMAT, "version": scanfile.VERSION,
            "started": merged[0][0] if merged else 0,
            "notes": f"merged: {description}",
            "merged_from": list(paths), "shifts": shifts,
        }) + "\n")
        for timestamp, points in merged:
            handle.write(json.dumps({
                "t": round(timestamp, 4),
                "p": [[round(a, 3), round(d, 1)] for a, d in points],
            }) + "\n")

    average = (sum(len(p) for _, p in merged) / len(merged)) if merged else 0
    print(f"merged {len(merged)} scans, {average:.0f} points each -> {out}")
    print(f"  from {description}")
    return merged


def crossing_report(path, cfg):
    """Run the merged clip and say whether the two walkers were both held.

    The honest measure of a crossing, and the one issue #12 item 5 asks for: how many
    scans carried two confirmed tracks at once, and how close the two got.

    An earlier version of this compared the nearest raw return of each clip. That was
    wrong - the nearest return in a scan is whatever clutter sits by the sensor, not a
    person - and it reported the same 0.08 m "closest approach" for every time shift.
    Foreground has to come out first, which means running the tracker.
    """
    from tracker import geometry
    from tracker.tracking import Tracker

    baseline = scanfile.build_baseline(path, cfg)
    baseline["distances"] = [math.inf if d is None else d
                             for d in baseline["distances"]]
    tracker = Tracker(cfg)
    scans = list(scanfile.read(path))
    if not scans:
        return None
    started = scans[0][0]

    both = 0
    most = 0
    closest = None
    when = None
    for timestamp, points in scans:
        foreground, _ = geometry.to_world(points, cfg, baseline)
        frame = tracker.update(timestamp, foreground)
        confirmed = [t for t in frame["tracks"] if t["confirmed"]]
        most = max(most, len(confirmed))
        if len(confirmed) < 2:
            continue
        both += 1
        for i in range(len(confirmed)):
            for j in range(i + 1, len(confirmed)):
                gap = math.hypot(confirmed[i]["x"] - confirmed[j]["x"],
                                 confirmed[i]["y"] - confirmed[j]["y"])
                if closest is None or gap < closest:
                    closest, when = gap, timestamp - started
    return {"scans": len(scans), "both": both, "most": most,
            "closest": closest, "when": when}
