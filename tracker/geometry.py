"""Turning a scan into world points, and world points back into jet numbers.

World frame: the LiDAR sits at (0, 0). +x runs along the strip, +y across the
hallway. Both are metres. `mount_angle_offset_deg` and `mirror` in the config are
what line the real sensor up with that frame; check them by eye in the viewer.
"""

import math


def to_world(points, cfg, baseline=None):
    """Polar scan -> list of world points.

    Returns two lists: foreground points (people) and background points (the room).
    With no baseline every in-range point is foreground.
    """
    foreground = []
    background = []
    bins = None
    if baseline is not None:
        distances = baseline["distances"]
        bin_deg = baseline["bin_deg"]
        bins = len(distances)

    for angle_deg, distance_mm in points:
        metres = distance_mm / 1000.0
        if metres < cfg.range_min or metres > cfg.range_max:
            continue

        world_angle = angle_deg + cfg.mount_angle_offset_deg
        if cfg.mirror:
            world_angle = -world_angle
        radians = math.radians(world_angle)
        x = metres * math.cos(radians)
        y = metres * math.sin(radians)

        if not (cfg.roi_x_min <= x <= cfg.roi_x_max
                and cfg.roi_y_min <= y <= cfg.roi_y_max):
            continue

        is_foreground = True
        if bins:
            index = int(angle_deg / bin_deg) % bins
            horizon = distances[index]
            if metres >= horizon - cfg.background_margin:
                is_foreground = False

        (foreground if is_foreground else background).append((x, y))

    return foreground, background


def strip_points(cfg):
    """Return calibrated points, or the old straight-line end points."""
    points = tuple(getattr(cfg, "strip_points", ()))
    if len(points) == cfg.jet_count and len(points) >= 2:
        return points
    return (cfg.strip_start, cfg.strip_end)


def strip_projection(x, y, cfg):
    """Project a world point onto the joined path through the calibrated jets.

    `jet_position` is continuous. A value of 4.5 is halfway from jet 4 to jet 5.
    `s` is physical distance in metres along the joined path from jet 0.
    """
    points = strip_points(cfg)
    best = None
    distance_before = 0.0
    total_length = sum(math.hypot(b[0] - a[0], b[1] - a[1])
                       for a, b in zip(points, points[1:]))

    for index, (a, b) in enumerate(zip(points, points[1:])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length_squared = dx * dx + dy * dy
        if length_squared == 0:
            continue
        length = math.sqrt(length_squared)
        raw_t = ((x - a[0]) * dx + (y - a[1]) * dy) / length_squared
        t = max(0.0, min(1.0, raw_t))
        px, py = a[0] + t * dx, a[1] + t * dy
        distance_squared = (x - px) ** 2 + (y - py) ** 2
        if best is None or distance_squared < best[0]:
            position_t = raw_t if ((index == 0 and raw_t < 0.0)
                                   or (index == len(points) - 2 and raw_t > 1.0)) else t
            best = (distance_squared, distance_before + position_t * length,
                    index + position_t, dx / length, dy / length, length)
        distance_before += length

    if best is None:
        return {"s": 0.0, "jet_position": 0.0, "jet": 0,
                "tangent": (0.0, 0.0), "segment_length": 0.0,
                "path_length": total_length}

    _, s, jet_position, tx, ty, segment_length = best
    jet = max(0, min(cfg.jet_count - 1, int(round(jet_position))))
    return {"s": s, "jet_position": jet_position, "jet": jet,
            "tangent": (tx, ty), "segment_length": segment_length,
            "path_length": total_length}


def strip_position(x, y, cfg):
    """Return physical distance along the path and the nearest jet index."""
    projection = strip_projection(x, y, cfg)
    return projection["s"], projection["jet"]
