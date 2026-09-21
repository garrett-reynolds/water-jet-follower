"""HTTP checks for the browser viewer and settings map."""

import json
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tracker.config import Config
from tracker.settings import SettingsControl
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

    def test_settings_page_has_a_draggable_active_area(self):
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode("utf-8")
        for name in ("roi_x_min", "roi_x_max", "roi_y_min", "roi_y_max"):
            self.assertIn(f'id="{name}" type="range"', page)
        self.assertIn("nearestCorner(", page)
        self.assertIn("moveCorner(dragCorner", page)
        self.assertIn("clampToArea(", page)
        # The map's frame is padded past the defaults, so a shrunken area can be
        # dragged back out again.
        with urlopen(self.base + "/settings-data") as response:
            data = json.loads(response.read())
        self.assertEqual(data["roi"], {"xmin": -1.0, "xmax": 4.5, "ymin": -3.0, "ymax": 3.0})
        self.assertEqual(data["profile"]["settings"]["roi_x_max"], 3.5)

    def test_live_viewer_follows_the_active_area(self):
        with urlopen(self.base + "/") as response:
            page = response.read().decode("utf-8")
        self.assertIn("polls++ % 15 === 0", page)
        self.assertIn("ctx.setLineDash([6, 4]);", page)

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

    def test_settings_page_has_no_jet_tester_but_links_to_the_test_page(self):
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode("utf-8")
        self.assertNotIn("/actions/test-jet", page)
        self.assertIn('href="/test"', page)
        self.assertIn('id="test-banner"', page)
        self.assertIn('id="resume-live"', page)

    def test_test_page_enters_test_mode_and_holds_one_jet(self):
        with urlopen(self.base + "/test") as response:
            page = response.read().decode("utf-8")
        self.assertIn("'/actions/test-mode',{enabled:true}", page)
        self.assertIn("'/actions/test-mode',{enabled:false}", page)
        self.assertIn("'/actions/test-jet'", page)
        self.assertIn("'/actions/all-off'", page)
        self.assertIn('id="seen"', page)
        self.assertNotIn("pagehide", page)
        self.assertNotIn("beforeunload", page)

    def test_settings_page_applies_edits_live_but_never_the_hard_maximum(self):
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode("utf-8")
        self.assertIn("applyTimer=setTimeout(autoApply,250)", page)
        self.assertIn("p.settings.height_max=original.settings.height_max", page)
        self.assertIn("unlock_height_max:false", page)
        self.assertIn("$('idle_water_animation').onchange=dirty", page)
        self.assertNotIn("Preview only. Nothing is live yet.", page)

    def test_water_shape_fields_are_sliders_with_readouts(self):
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode("utf-8")
        for name in ("jet_count", "height_min", "hill_peak", "height_max",
                     "hill_jets", "lead_seconds", "follow_response",
                     "slow_speed", "fast_speed", "idle_brightness",
                     "idle_seconds", "idle_height"):
            self.assertIn(f'id="{name}" type="range"', page)
            self.assertIn(f'<output id="{name}_out">', page)
        self.assertIn('id="height_max" type="range" min="1" max="255" step="1" disabled', page)
        self.assertIn("$('height_min').max=s.height_max", page)
        self.assertIn("$('hill_peak').max=s.height_max", page)
        self.assertNotIn('type="number"', page)

    def test_test_page_uses_sliders_bounded_by_the_applied_profile(self):
        with urlopen(self.base + "/test") as response:
            page = response.read().decode("utf-8")
        self.assertIn('id="jet" type="range"', page)
        self.assertIn('id="height" type="range"', page)
        self.assertNotIn('type="number"', page)
        self.assertIn("$('jet').max=s.jet_count", page)
        self.assertIn("$('height').max=s.height_max", page)

    def test_test_page_keeps_stop_and_status_in_a_sticky_bar(self):
        # Issue #32: the stop and its answer never scroll apart. Resume lives
        # in the mode box, not next to the stop, so the two are never confused.
        with urlopen(self.base + "/test") as response:
            page = response.read().decode("utf-8")
        bar = page[page.index('<div class="bar" id="bar">'):page.index("</main>")]
        self.assertIn('id="status"', bar)
        self.assertIn('id="stop" class="danger">Stop test', bar)
        self.assertNotIn('id="resume"', bar)
        self.assertIn('<span id="mode-text" class="text">', page)
        self.assertIn('<button id="resume" hidden>', page)
        self.assertIn("$('resume').hidden=!on;", page)
        self.assertNotIn("Leave test mode", page)
        self.assertIn(".bar { position:sticky; bottom:0;", page)

    def test_test_page_reads_past_the_end_instead_of_a_clamped_jet(self):
        # Issue #33: the readout uses jet_position, never the clamped jet, so a
        # walker off the strip cannot read as the first or last jet.
        with urlopen(self.base + "/test") as response:
            page = response.read().decode("utf-8")
        self.assertIn("p<-0.5||p>n-0.5?'Past the end':'Jet '+(Math.round(p)+1)", page)
        self.assertNotIn("'Jet '+(x.jet+1)", page)
        # #32 guard: the mode text lives in a span so Resume is never wiped.
        self.assertNotIn("$('mode').textContent", page)

    def test_test_page_shows_the_held_jet_and_greys_lost_tracks(self):
        # Issue #34: the mode box is the one writer of the held state, fed from
        # /state, and a coasting track renders muted with "(lost)".
        with urlopen(self.base + "/test") as response:
            page = response.read().decode("utf-8")
        self.assertIn("'TEST MODE. Holding jet '+(held.jet+1)+' at '+held.height+'", page)
        self.assertIn("held=f.held||null;showMode(f.test_mode);", page)
        self.assertIn("const lost=!x.seen;", page)
        self.assertIn("#seen .track.lost { color:var(--muted);", page)
        with urlopen(self.base + "/state") as response:
            frame = json.loads(response.read())
        self.assertIs(frame["test_mode"], False)
        self.assertIsNone(frame["held"])

    def test_load_and_reset_stay_in_preview_until_apply(self):
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode("utf-8")
        self.assertIn("pending=true;fill();status('Loaded profile previewed.", page)
        self.assertIn("pending=true;fill();status('Default profile previewed.", page)

    def test_unlock_has_its_own_label_row(self):
        # Issue #26: the unlock must not sit inside the slider label, where the
        # label's click goes to the readout instead of the box.
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode("utf-8")
        self.assertIn('<label for="unlock" class="unlock"><input id="unlock"', page)
        self.assertNotIn('class="slider lock"', page)

    def test_apply_goes_amber_when_the_hard_maximum_waits(self):
        # Issue #27: the class, not the `pending` variable, so live-apply of the
        # other sliders keeps working while the cap waits.
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode("utf-8")
        self.assertIn("!==original.settings.height_max);}", page)
        self.assertIn("original=copy(r);markPending();", page)

    def test_map_clears_when_the_state_poll_fails(self):
        # Issue #28: dead looks dead. The catch wipes the frame and redraws once.
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode("utf-8")
        self.assertIn("linkDown=true;liveFrame=null;draw();status('LiDAR not available.',true)", page)

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

    def test_settings_page_has_power_buttons_in_the_profile_box_not_the_bar(self):
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode("utf-8")
        profile = page[page.index("<h2>Profile</h2>"):page.index('<div class="bar"')]
        self.assertIn('id="reboot"', profile)
        self.assertIn('id="shutdown"', profile)
        self.assertNotIn('id="reboot" class="danger"', page)   # only stops are red
        self.assertIn("confirm(POWER[action].ask)", page)
        self.assertIn("'/actions/'+action", page)
        self.assertIn("does not start again on its own", page)

    def _post(self, path):
        request = Request(self.base + path, data=b"{}",
                          headers={"Content-Type": "application/json"})
        try:
            with urlopen(request) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def test_power_routes_are_refused_without_a_verified_zero(self):
        # The default control has no hardware callbacks, so both routes must say
        # so. Nothing here may ever reach a real reboot command.
        for path in ("/actions/reboot", "/actions/shutdown"):
            status, body = self._post(path)
            self.assertEqual(status, 400)
            self.assertIn("not available", body["error"])

    def test_power_routes_zero_first_then_run_the_named_command(self):
        calls = []
        control = SettingsControl(Config(), zero_output=lambda: calls.append("zero") or True,
                                  run_command=calls.append)
        server = serve(self.state, Config(viewer_host="127.0.0.1", viewer_port=0),
                       control)
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            request = Request(base + "/actions/reboot", data=b"{}",
                              headers={"Content-Type": "application/json"})
            with urlopen(request) as response:
                self.assertEqual(json.load(response),
                                 {"action": "reboot", "all_zero": True})
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(calls, ["zero", ["sudo", "-n", "/usr/sbin/reboot"]])
        self.assertTrue(control.stopping.is_set())

    def test_power_routes_refuse_and_report_an_unverified_zero(self):
        ran = []
        control = SettingsControl(Config(), zero_output=lambda: False,
                                  run_command=ran.append)
        server = serve(self.state, Config(viewer_host="127.0.0.1", viewer_port=0),
                       control)
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            request = Request(base + "/actions/shutdown", data=b"{}",
                              headers={"Content-Type": "application/json"})
            with self.assertRaises(HTTPError) as caught:
                urlopen(request)
            self.assertEqual(caught.exception.code, 400)
            self.assertIn("Cut the 24 V", json.load(caught.exception)["error"])
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(ran, [])


if __name__ == "__main__":
    unittest.main()
