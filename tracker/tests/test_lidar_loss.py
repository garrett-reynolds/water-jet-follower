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

from tracker import dmx, run
from tracker.tests import synthetic
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
    def _check_reconnect_keeps_water_off(self, held_test):
        # Losing the safe-state latch must fail this test on actual DMX output.
        cfg = Config(viewer_host="127.0.0.1", viewer_port=0,
                     strip_start=(0.1, 0.6), strip_end=(2.0, 0.6),
                     strip_points=(), resend_seconds=0)
        points = synthetic.scan(synthetic.legs_for_person(1.0, 0.6))
        sent = {"before": [], "returned": [], "enabled": []}
        phase = "before"
        control = None
        real_serve = run.viewer.serve

        def capturing_serve(state, config, ctl=None):
            nonlocal control
            control = ctl
            return real_serve(state, config, ctl)

        def source():
            nonlocal phase
            if held_test:
                control.set_test_mode(True)
                control.test_jet(0, 30)
            for i in range(12):
                yield i / 10, points
            yield 2.0, None
            phase = "returned"
            for i in range(12):
                yield 3.0 + i / 10, points
            self.assertTrue(sent["returned"])
            self.assertTrue(all(not any(frame) for frame in sent["returned"]),
                            "reconnect must not restore water")
            self.assertTrue(control.lights_only)
            self.assertIsNone(control.held)
            # A fresh operator action can permit water again.
            phase = "enabled"
            control.set_lights_only(False)
            if held_test:
                control.test_jet(0, 30)
            for i in range(12):
                yield 5.0 + i / 10, points

        def send(frame):
            sent[phase].append([frame[c - 1] for c in dmx.height_channels(cfg.jet_count)])
            return True

        with mock.patch.object(run.viewer, "serve", capturing_serve):
            run._show_loop(source(), cfg, None, "fake", SimpleNamespace(lights_only=False),
                           send_frame=send, zero_output=lambda: True)
        self.assertTrue(any(any(frame) for frame in sent["before"]))
        self.assertTrue(sent["returned"], "the page and show keep running after reconnect")
        self.assertTrue(all(not any(frame) for frame in sent["returned"]))
        self.assertTrue(any(any(frame) for frame in sent["enabled"]))

    def test_reconnect_keeps_live_follow_water_off_until_operator_action(self):
        self._check_reconnect_keeps_water_off(held_test=False)

    def test_reconnect_clears_held_water_test_until_operator_action(self):
        self._check_reconnect_keeps_water_off(held_test=True)

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

    def test_show_loop_returns_once_a_power_action_is_under_way(self):
        # Reboot Pi sets control.stopping after the command is accepted. The loop
        # must notice on the next scan and return, so the process leaves through
        # dmx.safe_output's exit zero instead of an OS kill mid-frame.
        cfg = Config(viewer_host="127.0.0.1", viewer_port=0)
        seen = []

        def source():
            yield (1.0, _scan())
            control.stopping.set()
            control.stop_reason = "reboot"
            for t in (2.0, 3.0, 4.0):
                seen.append(t)
                yield (t, _scan())

        real_serve = run.viewer.serve
        control = None

        def capturing_serve(state, cfg, ctl=None):
            nonlocal control
            control = ctl
            return real_serve(state, cfg, ctl)

        args = SimpleNamespace(lights_only=False)
        with mock.patch.object(run.viewer, "serve", capturing_serve),                 mock.patch.object(run.time, "sleep", lambda s: None):
            result = run._show_loop(source(), cfg, None, "fake", args,
                                    send_frame=lambda frame: True,
                                    zero_output=lambda: True,
                                    run_command=lambda command: None)
        self.assertEqual(result, 0)
        self.assertEqual(seen, [2.0], "one more scan is pulled, then the loop leaves")

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
