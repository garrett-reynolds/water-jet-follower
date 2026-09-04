"""Fake scans, so the tracker can be tested with nobody in the hallway.

A leg is a circle. A scan is one ray per angle bin, and the nearest circle the ray
touches wins, which gives real occlusion for free: a walker in front of another
walker really does hide them, the same way the A2M8 sees it.
"""

import math

LEG_RADIUS = 0.055          # a shin is roughly 110 mm across
LEG_SEPARATION = 0.20       # centre to centre, feet apart
BINS = 503                  # measured: 7,338 samples/s at 14.57 Hz


def legs_for_person(x, y, heading_deg=0.0, separation=LEG_SEPARATION):
    """Two leg circles, set either side of the walking line."""
    across = math.radians(heading_deg + 90.0)
    dx = math.cos(across) * separation / 2.0
    dy = math.sin(across) * separation / 2.0
    return [(x + dx, y + dy), (x - dx, y - dy)]


def scan(circles, bins=BINS, radius=LEG_RADIUS, walls=None):
    """One revolution. Returns [(angle_deg, distance_mm), ...] in sweep order.

    `walls` is an optional list of (angle_from, angle_to, distance_m) to stand in
    for the room, so background subtraction can be exercised.
    """
    points = []
    for index in range(bins):
        angle_deg = 360.0 * index / bins
        theta = math.radians(angle_deg)
        cos_t, sin_t = math.cos(theta), math.sin(theta)

        nearest = None
        for cx, cy in circles:
            # distance along the ray to the near face of the circle
            along = cx * cos_t + cy * sin_t
            if along <= 0:
                continue
            perpendicular = abs(-cx * sin_t + cy * cos_t)
            if perpendicular > radius:
                continue
            hit = along - math.sqrt(radius * radius - perpendicular * perpendicular)
            if hit > 0 and (nearest is None or hit < nearest):
                nearest = hit

        for wall_from, wall_to, wall_distance in (walls or []):
            if wall_from <= angle_deg <= wall_to:
                if nearest is None or wall_distance < nearest:
                    nearest = wall_distance

        if nearest is not None:
            points.append((angle_deg, nearest * 1000.0))
    return points


def walk(people, seconds, hz=14.57, walls=None, start_time=1000.0):
    """Yield (timestamp, points) for people described as (x0, y0, vx, vy).

    A person with vx == vy == 0 is standing still, which is the Hold case.
    """
    dt = 1.0 / hz
    steps = int(seconds * hz)
    for step in range(steps):
        t = step * dt
        circles = []
        for x0, y0, vx, vy in people:
            heading = math.degrees(math.atan2(vy, vx)) if (vx or vy) else 0.0
            circles += legs_for_person(x0 + vx * t, y0 + vy * t, heading)
        yield start_time + t, scan(circles, walls=walls)
