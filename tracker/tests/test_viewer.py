"""HTTP checks for the browser viewer and settings map."""

import json
import unittest
from urllib.request import urlopen

from tracker.config import Config
from tracker.viewer import State, serve


class TestSettingsMap(unittest.TestCase):
    def setUp(self):
        self.state = State()
        self.state.set({
            "t": 1, "tracks": [], "clusters": [], "legs": [],
            "detections": [], "fg": [[1.0, 0.5]], "bg": [[1.2, 0.4]],
            "hz": 16.0,
        })
        self.server = serve(self.state, Config(viewer_host="127.0.0.1",
                                               viewer_port=0))
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_settings_page_has_zoom_and_live_scan(self):
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode("utf-8")
        self.assertIn('id="zoom-in"', page)
        self.assertIn('id="zoom-out"', page)
        self.assertIn('id="zoom-fit"', page)
        self.assertIn("pollState()", page)

    def test_settings_page_draws_each_jet_on_the_control_path(self):
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode("utf-8")
        self.assertIn("jetPoints(profile.settings.strip_points", page)

    def test_jet_count_change_makes_one_movable_point_per_jet(self):
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode("utf-8")
        self.assertIn(
            "profile.settings.strip_points=jetPoints("
            "profile.settings.strip_points,count)", page)

    def test_settings_page_has_a_water_jet_tester(self):
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode("utf-8")
        self.assertIn('id="water-test-jet"', page)
        self.assertIn('id="water-test-height"', page)
        self.assertIn('id="start-water-test"', page)
        self.assertIn('id="stop-water-test"', page)
        self.assertIn('Holds one jet until you stop the test.', page)

    def test_settings_page_uses_an_inline_colour_wheel_and_mode_selector(self):
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode("utf-8")
        self.assertIn('id="colour_mode"', page)
        self.assertIn('id="colour_wheel"', page)
        self.assertIn('id="colour_value" type="range"', page)
        self.assertIn('id="white_level" type="range"', page)
        self.assertNotIn('type="color"', page)
        self.assertNotIn('id="base_colour_0"', page)

    def test_idle_height_follows_the_editable_hard_maximum(self):
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode("utf-8")
        self.assertIn("$('idle_height').max=s.height_max", page)
        self.assertNotIn('id="idle_height" type="number" min="1" max="40"', page)

    def test_state_endpoint_supplies_scan_points(self):
        with urlopen(self.base + "/state") as response:
            frame = json.load(response)
        self.assertEqual(frame["fg"], [[1.0, 0.5]])
        self.assertEqual(frame["bg"], [[1.2, 0.4]])


if __name__ == "__main__":
    unittest.main()
