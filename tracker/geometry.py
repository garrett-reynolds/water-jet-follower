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


def strip_position(x, y, cfg):
    """Where a point sits along the strip.

    Returns (s, jet) where s is metres from jet 0 along the strip axis and jet is
    the nearest jet index, clamped to 0..jet_count-1.
    """
    x0, y0 = cfg.strip_start
    x1, y1 = cfg.strip_end
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length == 0:
        return 0.0, 0
    s = ((x - x0) * dx + (y - y0) * dy) / length
    pitch = length / (cfg.jet_count - 1)
    jet = int(round(s / pitch))
    jet = max(0, min(cfg.jet_count - 1, jet))
    return s, jet
