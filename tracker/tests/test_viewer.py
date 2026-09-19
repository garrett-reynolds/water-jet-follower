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

    def test_state_endpoint_supplies_scan_points(self):
        with urlopen(self.base + "/state") as response:
            frame = json.load(response)
        self.assertEqual(frame["fg"], [[1.0, 0.5]])
        self.assertEqual(frame["bg"], [[1.2, 0.4]])


if __name__ == "__main__":
    unittest.main()
