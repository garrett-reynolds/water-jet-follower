"""Issue #31: the show must survive the LiDAR plug coming out.

No real LiDAR here. A fake source stands in for Lidar so the reconnect loop and
the show loop's zero-and-wait path can be proven on the laptop.
"""

import json
import time
import unittest
from types import SimpleNamespace
from unittest import mock
from urllib.error import HTTPError
from urllib.request import urlopen

from tracker import run
from tracker.config import Config
from tracker.viewer import State, serve


class FakeLidar:
    """Streams a few scans, then fails once, then streams again after a reconnect."""

    def __init__(self):
        self.closed = 0
        self.connects = 0
        self.fail_connects = 1

    def scans(self):
        yield 1.0, [(0.0, 1000.0)]
        yield 2.0, [(0.0, 1000.0)]
        if self.connects == 0:
            raise OSError("device disconnected")
        yield 3.0, [(0.0, 1000.0)]

    def close(self):
        self.closed += 1

    def connect(self, attempts=5, delay=1.0):
        if self.fail_connects:
            self.fail_connects -= 1
            raise RuntimeError("no port")
        self.connects += 1
        return self


class TestReconnectingScans(unittest.TestCase):
    def test_yields_none_while_gone_then_scans_again(self):
        lidar = FakeLidar()
        with mock.patch.object(time, "sleep"):
            source = run._reconnecting_scans(lidar, delays=(0.0,))
            seen = [next(source) for _ in range(6)]
        points = [p for _, p in seen]
        # two good, one None per failed connect (1) plus one for the first wait, then good
        self.assertEqual(points[:2], [[(0.0, 1000.0)]] * 2)
        self.assertEqual(points[2:4], [None, None])
        self.assertEqual(points[4:], [[(0.0, 1000.0)]] * 2)
        self.assertGreaterEqual(lidar.closed, 1)
        self.assertEqual(lidar.connects, 1)


def _scan():
    # one return straight ahead at 1 m, well inside the default ROI
    return [(0.0, 1000.0)]


class TestShowLoopWhenTheSensorGoes(unittest.TestCase):
    def test_zeroes_once_marks_the_frame_dead_and_recovers(self):
        cfg = Config(viewer_host="127.0.0.1", viewer_port=0)
        zeroes = []
        sent = []
        frames = []
        real_serve = run.viewer.serve

        def capturing_serve(state, cfg, control=None):
            original_set = state.set
            state.set = lambda frame: (frames.append(frame), original_set(frame))
            return real_serve(state, cfg, control)

        source = iter([(1.0, _scan()), (2.0, None), (3.0, None), (4.0, _scan())])
        args = SimpleNamespace(lights_only=False)
        with mock.patch.object(run.viewer, "serve", capturing_serve):
            run._show_loop(source, cfg, None, "fake", args,
                           send_frame=lambda frame: sent.append(frame) or True,
                           zero_output=lambda: zeroes.append(True) or True)
        self.assertEqual(len(zeroes), 1, "zero fires once, on the edge")
        flags = [f.get("lidar_ok", True) for f in frames]
        self.assertEqual(flags, [True, False, True], "dead frame set once, then live again")

    def test_dead_frame_makes_state_answer_503(self):
        state = State()
        state.set(run._dead_frame(5.0, "fake"))
        server = serve(state, Config(viewer_host="127.0.0.1", viewer_port=0))
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            with self.assertRaises(HTTPError) as caught:
                urlopen(base + "/state")
            self.assertEqual(caught.exception.code, 503)
            body = json.loads(caught.exception.read().decode("utf-8"))
            self.assertEqual(body["error"], "LiDAR not available")
            with urlopen(base + "/") as response:
                page = response.read().decode("utf-8")
            self.assertIn("if (!r.ok) throw Error", page)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
