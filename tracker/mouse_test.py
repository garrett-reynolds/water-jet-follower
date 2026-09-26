"""One local test Walker and its Wave preview. No hardware output lives here."""

import math
import threading
import time

from tracker import geometry
from tracker.wave import Wave


class MouseTest:
    STOP_AFTER = 0.15

    def __init__(self, cfg, state, clock=None):
        self.cfg = cfg
        self.state = state
        self.clock = clock or time.time
        self.wave = Wave(cfg)
        self._lock = threading.Lock()
        self._last = None
        self._last_move_at = None
        self._track = None
        self._distance = 0.0
        self._seen = 0
        self._publish(self.clock(), [])

    def _publish(self, timestamp, tracks):
        frame = {"t": timestamp, "tracks": tracks, "clusters": [], "legs": [],
                 "detections": [], "fg": [], "bg": [], "hz": 0.0,
                 "source": "mouse test"}
        heights, colours = self.wave.output_values(frame, timestamp)
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
            if not self._inside(x, y):
                self._clear(self.clock())
                return None
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
            self._last_move_at = self.clock()
            self._track = track
            self._publish(self._last_move_at, [track])
            return track

    def _inside(self, x, y):
        return (self.cfg.roi_x_min <= x <= self.cfg.roi_x_max
                and self.cfg.roi_y_min <= y <= self.cfg.roi_y_max)

    def edit_settings(self, edit):
        """Apply a local profile edit and refresh one consistent Wave frame."""
        with self._lock:
            result = edit()
            if self._track is not None:
                x, y = self._track["x"], self._track["y"]
                if not self._inside(x, y):
                    self._clear(self.clock())
                    return result
                projection = geometry.strip_projection(x, y, self.cfg)
                self._track = dict(self._track, **projection)
            self._publish(self.clock(), [self._track] if self._track else [])
            return result

    def tick(self):
        """Refresh Wave and stop pointer speed when no new move arrives."""
        with self._lock:
            now = self.clock()
            if (self._track is not None and self._last_move_at is not None
                    and now - self._last_move_at >= self.STOP_AFTER):
                self._track = dict(self._track, vx=0.0, vy=0.0, speed=0.0)
            self._publish(now, [self._track] if self._track is not None else [])

    def _clear(self, timestamp):
        self._last = None
        self._last_move_at = None
        self._track = None
        self._distance = 0.0
        self._seen = 0
        self._publish(timestamp, [])

    def clear(self):
        with self._lock:
            self._clear(self.clock())
