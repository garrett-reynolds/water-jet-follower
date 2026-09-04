"""Cluster -> legs -> people -> tracks.

The algorithm follows angusleigh/leg_tracker: split the scan into clusters, pair
clusters into legs, and follow each pair with a constant-velocity Kalman filter.
Parameter names and values are borrowed from it (see config.py). Two deliberate
differences:

  * No trained leg classifier. leg_tracker uses a random forest to tell a leg from
    a chair leg. Here the background baseline does that job: anything that was in
    the empty room is already gone before clustering starts.
  * A lone cluster still counts as a person. When two legs are together, or one
    leg hides the other, the scan holds one blob, not two. Dropping it would lose
    the walker exactly when they stand still, which is the Hold behaviour.

Pure Python on purpose: about 500 points a scan at 14.6 Hz does not need numpy,
and the Pi's venv does not have it.
"""

import math
from itertools import count

from tracker import geometry


# --- clustering ---------------------------------------------------------

class Cluster:
    def __init__(self, points):
        self.points = points
        self.x = sum(p[0] for p in points) / len(points)
        self.y = sum(p[1] for p in points) / len(points)
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        self.width = math.hypot(max(xs) - min(xs), max(ys) - min(ys))

    def __len__(self):
        return len(self.points)


def cluster_points(points, cfg):
    """Break the scan wherever consecutive points jump more than cluster_dist_euclid.

    Points arrive in sweep order, so consecutive-gap splitting is enough. The first
    and last clusters get merged if they meet across the 0/360 degree seam.
    """
    if not points:
        return []

    groups = [[points[0]]]
    for previous, current in zip(points, points[1:]):
        gap = math.hypot(current[0] - previous[0], current[1] - previous[1])
        if gap > cfg.cluster_dist_euclid:
            groups.append([current])
        else:
            groups[-1].append(current)

    if len(groups) > 1:
        first, last = groups[0][0], groups[-1][-1]
        if math.hypot(first[0] - last[0], first[1] - last[1]) <= cfg.cluster_dist_euclid:
            groups[0] = groups.pop() + groups[0]

    return [Cluster(g) for g in groups]


def leg_candidates(clusters, cfg):
    """Keep clusters that are the right size to be a leg, or a pair of legs."""
    return [c for c in clusters
            if len(c) >= cfg.min_points_per_cluster
            and cfg.min_cluster_width <= c.width <= cfg.max_cluster_width
            and math.hypot(c.x, c.y) <= cfg.max_detect_distance]


def pair_legs(legs, cfg):
    """Pair nearby legs into person detections; leave lone legs as their own person.

    Greedy shortest-first pairing. With at most a handful of legs in a 3 m room the
    optimal assignment and the greedy one agree, and greedy needs no solver.
    """
    pairs = []
    for i in range(len(legs)):
        for j in range(i + 1, len(legs)):
            distance = math.hypot(legs[i].x - legs[j].x, legs[i].y - legs[j].y)
            if distance <= cfg.max_leg_pairing_dist:
                pairs.append((distance, i, j))
    pairs.sort()

    used = set()
    detections = []
    for _, i, j in pairs:
        if i in used or j in used:
            continue
        used.add(i)
        used.add(j)
        detections.append({
            "x": (legs[i].x + legs[j].x) / 2.0,
            "y": (legs[i].y + legs[j].y) / 2.0,
            "kind": "pair",
            "points": len(legs[i]) + len(legs[j]),
        })

    for index, leg in enumerate(legs):
        if index not in used:
            detections.append({"x": leg.x, "y": leg.y,
                               "kind": "single", "points": len(leg)})
    return detections


# --- one axis of a constant-velocity Kalman filter -----------------------

class Axis:
    """State is [position, velocity]. Same model as leg_tracker, one axis at a time.

    The 4-state filter in leg_tracker has no cross terms between x and y, so two of
    these are equivalent to it and need no matrix library.
    """

    def __init__(self, position, var_pos, var_vel, var_obs):
        self.p = position
        self.v = 0.0
        self.P00, self.P01, self.P10, self.P11 = 0.5, 0.0, 0.0, 0.5
        self.var_pos = var_pos
        self.var_vel = var_vel
        self.var_obs = var_obs

    def predict(self, dt):
        self.p += self.v * dt
        # P = F P F_transpose + Q, with F = [[1, dt], [0, 1]]
        p00 = self.P00 + dt * (self.P10 + self.P01) + dt * dt * self.P11 + self.var_pos
        p01 = self.P01 + dt * self.P11
        p10 = self.P10 + dt * self.P11
        p11 = self.P11 + self.var_vel
        self.P00, self.P01, self.P10, self.P11 = p00, p01, p10, p11

    def update(self, measurement):
        innovation_cov = self.P00 + self.var_obs
        k0 = self.P00 / innovation_cov
        k1 = self.P10 / innovation_cov
        innovation = measurement - self.p
        self.p += k0 * innovation
        self.v += k1 * innovation
        p00 = self.P00 - k0 * self.P00
        p01 = self.P01 - k0 * self.P01
        p10 = self.P10 - k1 * self.P00
        p11 = self.P11 - k1 * self.P01
        self.P00, self.P01, self.P10, self.P11 = p00, p01, p10, p11


# --- one person ---------------------------------------------------------

class Track:
    _ids = count(1)

    def __init__(self, detection, timestamp, cfg):
        self.id = next(Track._ids)
        var_pos = cfg.std_process_noise ** 2
        var_vel = cfg.std_process_noise ** 2
        self.x_axis = Axis(detection["x"], var_pos, var_vel, cfg.var_obs_local)
        self.y_axis = Axis(detection["y"], var_pos, var_vel, cfg.var_obs_local)
        self.born = timestamp
        self.last_seen = timestamp
        self.times_seen = 1
        self.dist_travelled = 0.0
        self.confirmed = False
        self.seen_this_scan = True
        self.kind = detection["kind"]

    @property
    def x(self):
        return self.x_axis.p

    @property
    def y(self):
        return self.y_axis.p

    @property
    def vx(self):
        return self.x_axis.v

    @property
    def vy(self):
        return self.y_axis.v

    @property
    def speed(self):
        return math.hypot(self.vx, self.vy)

    @property
    def position_variance(self):
        return self.x_axis.P00

    def predict(self, dt):
        self.x_axis.predict(dt)
        self.y_axis.predict(dt)
        self.seen_this_scan = False

    def correct(self, detection, timestamp, cfg):
        before_x, before_y = self.x, self.y
        self.x_axis.update(detection["x"])
        self.y_axis.update(detection["y"])
        self.dist_travelled += math.hypot(self.x - before_x, self.y - before_y)
        self.times_seen += 1
        self.last_seen = timestamp
        self.seen_this_scan = True
        self.kind = detection["kind"]
        self._check_confirmed(cfg)

    def _check_confirmed(self, cfg):
        if self.confirmed:
            return
        travelled_enough = (
            self.dist_travelled >= cfg.dist_travelled_together_to_initiate_leg_pair)
        stood_still_long_enough = (
            cfg.min_times_seen_to_initiate > 0
            and self.times_seen >= cfg.min_times_seen_to_initiate)
        self.confirmed = travelled_enough or stood_still_long_enough


# --- the tracker --------------------------------------------------------

class Tracker:
    def __init__(self, cfg):
        self.cfg = cfg
        self.tracks = []
        self.last_time = None

    def update(self, timestamp, world_points):
        """Run one scan. Returns a dict the viewer and the wave logic both read."""
        cfg = self.cfg
        dt = 0.0 if self.last_time is None else max(1e-3, timestamp - self.last_time)
        self.last_time = timestamp

        clusters = cluster_points(world_points, cfg)
        legs = leg_candidates(clusters, cfg)
        detections = pair_legs(legs, cfg)

        for track in self.tracks:
            track.predict(dt)

        self._associate(detections, timestamp)

        self.tracks = [t for t in self.tracks
                       if timestamp - t.last_seen <= cfg.max_seconds_unseen]

        return {
            "t": timestamp,
            "dt": dt,
            "clusters": [{"x": c.x, "y": c.y, "n": len(c), "w": c.width}
                         for c in clusters],
            "legs": [{"x": c.x, "y": c.y, "w": c.width} for c in legs],
            "detections": detections,
            "tracks": [self._report(t) for t in self.tracks],
        }

    def _associate(self, detections, timestamp):
        """Greedy nearest neighbour, gated by the filter's own uncertainty."""
        cfg = self.cfg
        costs = []
        for track_index, track in enumerate(self.tracks):
            gate = min(cfg.max_association_dist,
                       2.0 * math.sqrt(track.position_variance + cfg.var_obs))
            for det_index, detection in enumerate(detections):
                distance = math.hypot(detection["x"] - track.x,
                                      detection["y"] - track.y)
                if distance <= gate:
                    costs.append((distance, track_index, det_index))
        costs.sort()

        matched_tracks = set()
        matched_detections = set()
        for _, track_index, det_index in costs:
            if track_index in matched_tracks or det_index in matched_detections:
                continue
            matched_tracks.add(track_index)
            matched_detections.add(det_index)
            self.tracks[track_index].correct(detections[det_index], timestamp, cfg)

        for det_index, detection in enumerate(detections):
            if det_index not in matched_detections:
                self.tracks.append(Track(detection, timestamp, cfg))

    def _report(self, track):
        s, jet = geometry.strip_position(track.x, track.y, self.cfg)
        return {
            "id": track.id,
            "x": round(track.x, 4),
            "y": round(track.y, 4),
            "vx": round(track.vx, 4),
            "vy": round(track.vy, 4),
            "speed": round(track.speed, 4),
            "s": round(s, 4),
            "jet": jet,
            "confirmed": track.confirmed,
            "seen": track.seen_this_scan,
            "times_seen": track.times_seen,
            "dist_travelled": round(track.dist_travelled, 4),
            "kind": track.kind,
        }
