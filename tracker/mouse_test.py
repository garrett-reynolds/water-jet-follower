"""One local test Walker and its Wave preview. No hardware output lives here."""

import math
import threading

from tracker import geometry
from tracker.wave import Wave


class MouseTest:
    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state
        self.wave = Wave(cfg)
        self._lock = threading.Lock()
        self._last = None
        self._distance = 0.0
        self._seen = 0
        self._publish(0.0, [])

    def _publish(self, timestamp, tracks):
        frame = {"t": timestamp, "tracks": tracks, "clusters": [], "legs": [],
                 "detections": [], "fg": [], "bg": [], "hz": 0.0,
                 "source": "mouse test"}
        heights, colours = self.wave.heights_and_colours(frame, timestamp)
        frame["heights"] = heights
        frame["pixel_colours"] = [list(colour) for colour in colours]
        self.state.set(frame)
        return frame

    def move(self, x, y, timestamp):
        values = (x, y, timestamp)
        if any(isinstance(value, bool) or not isinstance(value, (int, float))
               or not math.isfinite(value) for value in values):
            raise ValueError("x, y, and t must be finite numbers")
        with self._lock:
            last = self._last
            if last is not None and timestamp <= last[2]:
                raise ValueError("t must increase with each move")
            if last is None:
                vx = vy = 0.0
                self._distance = 0.0
                self._seen = 1
            else:
                dt = timestamp - last[2]
                vx, vy = (x - last[0]) / dt, (y - last[1]) / dt
                self._distance += math.hypot(x - last[0], y - last[1])
                self._seen += 1
            projection = geometry.strip_projection(x, y, self.cfg)
            track = {"id": 1, "x": x, "y": y, "vx": vx, "vy": vy,
                     "speed": math.hypot(vx, vy), "s": projection["s"],
                     "jet_position": projection["jet_position"],
                     "jet": projection["jet"], "confirmed": True,
                     "seen": True, "times_seen": self._seen,
                     "dist_travelled": self._distance, "kind": "mouse"}
            self._last = (x, y, timestamp)
            self._publish(timestamp, [track])
            return track

    def clear(self):
        with self._lock:
            timestamp = self._last[2] if self._last is not None else 0.0
            self._last = None
            self._distance = 0.0
            self._seen = 0
            self._publish(timestamp, [])
