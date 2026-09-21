"""Tests for the browser settings boundary.

The browser sends a complete profile.  Nothing changes until the whole profile
validates, because a half-applied safety limit is worse than a rejected edit.
"""

import contextlib
import io
import json
import os
import tempfile
import unittest

from tracker import geometry
from tracker.config import Config
from tracker.settings import (POWER_COMMANDS, PROFILE_VERSION, UNDO_DEPTH,
                              SettingsControl, load_profile, profile_for,
                              save_profile)


class TestProfiles(unittest.TestCase):
    def setUp(self):
        self.cfg = Config()
        self.control = SettingsControl(self.cfg)

    def test_profile_is_versioned(self):
        self.assertEqual(profile_for(self.cfg)["version"], PROFILE_VERSION)

    def test_apply_is_all_or_nothing(self):
        profile = profile_for(self.cfg)
        profile["settings"]["hill_peak"] = 22
        profile["settings"]["jet_count"] = 99
        with self.assertRaises(ValueError):
            self.control.apply(profile)
        self.assertEqual(self.cfg.hill_peak, 30)
        self.assertEqual(self.cfg.jet_count, 10)

    def test_active_area_goes_live_on_the_shared_config(self):
        # (2.0, 0.0) is inside the default area. Pull x max in front of it and the
        # next scan must drop it, with no restart and no plumbing: to_world reads
        # the same cfg the profile lands on.
        scan = [(0.0, 2000.0)]           # straight ahead, 2 m
        self.assertEqual(len(geometry.to_world(scan, self.cfg)[0]), 1)
        profile = profile_for(self.cfg)
        profile["settings"]["roi_x_max"] = 1.9
        self.control.apply(profile)
        self.assertEqual(self.cfg.roi_x_max, 1.9)
        self.assertEqual(geometry.to_world(scan, self.cfg)[0], [])

    def test_active_area_must_be_a_real_rectangle(self):
        profile = profile_for(self.cfg)
        profile["settings"]["roi_y_min"] = profile["settings"]["roi_y_max"]
        with self.assertRaises(ValueError):
            self.control.apply(profile)

    def test_active_area_must_hold_every_path_point(self):
        profile = profile_for(self.cfg)
        profile["settings"]["roi_x_max"] = 1.7     # jet 1 sits at x 1.80
        with self.assertRaises(ValueError) as caught:
            self.control.apply(profile)
        self.assertIn("path point 1", str(caught.exception))
        self.assertEqual(self.cfg.roi_x_max, 3.5)

        profile = profile_for(self.cfg)
        points = list(profile["settings"]["strip_points"])
        points[-1] = (1.54, 2.5)                       # past y max
        profile["settings"]["strip_points"] = points
        with self.assertRaises(ValueError):
            self.control.apply(profile)
        self.assertEqual(self.cfg.strip_points[-1], (1.54, 1.20))

    def test_a_profile_from_before_the_active_area_is_refused_by_version(self):
        profile = profile_for(self.cfg)
        profile["version"] = 3
        with self.assertRaises(ValueError) as caught:
            self.control.apply(profile)
        self.assertIn("version", str(caught.exception))

    def test_undo_stack_is_bounded_for_live_apply(self):
        profile = profile_for(self.cfg)
        for step in range(UNDO_DEPTH + 10):
            profile["settings"]["hill_peak"] = 10 + step % 20
            self.control.apply(profile)
        self.assertEqual(len(self.control._undo), UNDO_DEPTH)

    def test_hard_max_needs_the_lock_open(self):
        profile = profile_for(self.cfg)
        profile["settings"]["height_max"] = 35
        with self.assertRaises(PermissionError):
            self.control.apply(profile)
        self.control.apply(profile, unlock_height_max=True)
        self.assertEqual(self.cfg.height_max, 35)

    def test_undo_restores_the_previous_profile(self):
        profile = profile_for(self.cfg)
        profile["settings"]["hill_peak"] = 20
        self.control.apply(profile)
        self.control.undo()
        self.assertEqual(self.cfg.hill_peak, 30)

    def test_bad_colour_rejects_the_whole_profile(self):
        profile = profile_for(self.cfg)
        profile["settings"]["slow_colour"] = [0, 0, 999, 0]
        with self.assertRaises(ValueError):
            self.control.apply(profile)

    def test_idle_speed_and_colour_are_validated(self):
        profile = profile_for(self.cfg)
        profile["settings"]["idle_seconds"] = 3.5
        profile["settings"]["idle_colour"] = [12, 34, 56, 7]
        self.control.apply(profile)
        self.assertEqual(self.cfg.idle_seconds, 3.5)
        self.assertEqual(self.cfg.idle_colour, (12, 34, 56, 7))

    def test_idle_height_must_stay_inside_the_water_limits(self):
        profile = profile_for(self.cfg)
        profile["settings"]["idle_height"] = 41
        with self.assertRaises(ValueError):
            self.control.apply(profile)


class TestActions(unittest.TestCase):
    def test_all_off_uses_the_verified_zero_callback(self):
        calls = []
        control = SettingsControl(Config(), zero_output=lambda: calls.append(True) or True)
        self.assertTrue(control.all_off())
        self.assertEqual(calls, [True])

    def test_jet_test_sends_one_full_safe_frame(self):
        frames = []
        cfg = Config(height_min=7)
        control = SettingsControl(cfg, send_frame=frames.append)
        control.set_test_mode(True)
        control.test_jet(0)
        self.assertEqual(len(frames[0]), 512)
        self.assertEqual(frames[0][4], 7)
        self.assertFalse(any(frames[0][5:]))

    def test_water_test_uses_the_requested_safe_height(self):
        frames = []
        cfg = Config(height_max=40)
        control = SettingsControl(cfg, send_frame=frames.append)
        control.set_test_mode(True)
        control.test_jet(2, height=20)
        self.assertEqual(frames[0][14], 20)

    def test_water_test_rejects_height_above_the_hard_maximum(self):
        control = SettingsControl(Config(height_max=40), send_frame=lambda frame: None)
        control.set_test_mode(True)
        with self.assertRaises(ValueError):
            control.test_jet(0, height=41)

    def test_water_test_is_blocked_in_lights_only_mode(self):
        frames = []
        control = SettingsControl(Config(), send_frame=frames.append)
        control.set_test_mode(True)
        control.set_lights_only(True)
        with self.assertRaises(ValueError):
            control.test_jet(0, height=5)
        self.assertEqual(frames, [])

    def test_disabled_jet_cannot_be_tested(self):
        cfg = Config(jet_enabled=(False,) + (True,) * 9)
        control = SettingsControl(cfg, send_frame=lambda frame: None)
        control.set_test_mode(True)
        with self.assertRaises(ValueError):
            control.test_jet(0)

    def test_jet_test_holds_until_all_off(self):
        control = SettingsControl(Config(), send_frame=lambda frame: None,
                                  zero_output=lambda: True)
        normal = [0] * 512
        control.set_test_mode(True)
        control.test_jet(0)
        self.assertEqual(control.output_frame(normal)[4], 5)
        control.all_off()
        # Still in test mode: the show gets a blank frame, not the live one.
        self.assertFalse(any(control.output_frame(normal)))
        control.set_test_mode(False)
        self.assertIs(control.output_frame(normal), normal)

    def test_lights_only_forces_a_held_test_jet_dry(self):
        control = SettingsControl(Config(), send_frame=lambda frame: None)
        control.set_test_mode(True)
        control.test_jet(0)
        control.lights_only = True
        self.assertEqual(control.output_frame([0] * 512)[4], 0)


class TestTestMode(unittest.TestCase):
    """Test mode is the one state where a walker cannot put water up."""

    def test_jet_test_is_refused_outside_test_mode(self):
        frames = []
        control = SettingsControl(Config(), send_frame=frames.append)
        with self.assertRaises(ValueError):
            control.test_jet(0)
        self.assertEqual(frames, [])

    def test_entering_test_mode_zeroes_first(self):
        calls = []
        control = SettingsControl(Config(), zero_output=lambda: calls.append(True) or True)
        result = control.set_test_mode(True)
        self.assertEqual(calls, [True])
        self.assertEqual(result, {"enabled": True, "all_zero": True})
        self.assertTrue(control.test_mode)

    def test_test_mode_hides_the_live_frame(self):
        control = SettingsControl(Config(), zero_output=lambda: True)
        live = [30] * 512
        control.set_test_mode(True)
        out = control.output_frame(live)
        self.assertEqual(len(out), 512)
        self.assertFalse(any(out))

    def test_leaving_test_mode_zeroes_and_drops_the_held_jet(self):
        calls = []
        control = SettingsControl(Config(), send_frame=lambda frame: None,
                                  zero_output=lambda: calls.append(True) or True)
        control.set_test_mode(True)
        control.test_jet(0)
        control.set_test_mode(False)
        self.assertEqual(len(calls), 2)
        self.assertFalse(control.test_mode)
        live = [30] * 512
        self.assertIs(control.output_frame(live), live)

    def test_held_jet_is_reported_and_cleared_by_stop_and_resume(self):
        # Issue #34: the page shows the held jet from the server's record, so a
        # reload cannot hide water that is up.
        control = SettingsControl(Config(), send_frame=lambda frame: None,
                                  zero_output=lambda: True)
        self.assertIsNone(control.held)
        control.set_test_mode(True)
        self.assertEqual(control.test_jet(6, 30), {"jet": 6, "height": 30})
        self.assertEqual(control.held, {"jet": 6, "height": 30})
        control.all_off()
        self.assertIsNone(control.held)
        control.test_jet(2)
        control.set_test_mode(False)
        self.assertIsNone(control.held)

    def test_test_mode_flag_changes_even_when_zero_fails(self):
        control = SettingsControl(Config(), zero_output=lambda: False)
        result = control.set_test_mode(True)
        self.assertEqual(result, {"enabled": True, "all_zero": False})
        self.assertTrue(control.test_mode)

    def test_test_mode_works_with_no_hardware_callbacks(self):
        control = SettingsControl(Config())
        self.assertEqual(control.set_test_mode(True),
                         {"enabled": True, "all_zero": None})

    def test_all_off_enters_test_mode(self):
        control = SettingsControl(Config(), zero_output=lambda: True)
        control.all_off()
        self.assertTrue(control.test_mode)

    def test_test_mode_rejects_non_booleans(self):
        control = SettingsControl(Config())
        with self.assertRaises(ValueError):
            control.set_test_mode("yes")


class TestPower(unittest.TestCase):
    """Reboot and shut down from the page: zero first, refuse if unverified."""

    def _control(self, zero=True):
        self.calls = []
        return SettingsControl(
            Config(),
            zero_output=lambda: self.calls.append("zero") or zero,
            run_command=lambda command: self.calls.append(command))

    def test_reboot_zeroes_before_the_command_and_stops_the_show(self):
        control = self._control()
        self.assertEqual(control.power("reboot"),
                         {"action": "reboot", "all_zero": True})
        self.assertEqual(self.calls, ["zero", ["sudo", "-n", "/usr/sbin/reboot"]])
        self.assertTrue(control.test_mode)
        self.assertTrue(control.stopping.is_set())
        self.assertEqual(control.stop_reason, "reboot")

    def test_shutdown_runs_poweroff_by_its_full_path(self):
        control = self._control()
        control.power("shutdown")
        self.assertEqual(self.calls[-1], ["sudo", "-n", "/usr/sbin/poweroff"])
        self.assertEqual(self.calls[-1], POWER_COMMANDS["shutdown"])

    def test_power_refuses_when_zero_is_not_verified(self):
        control = self._control(zero=False)
        with self.assertRaises(RuntimeError) as caught:
            control.power("reboot")
        self.assertIn("24 V", str(caught.exception))
        self.assertEqual(self.calls, ["zero"])       # the command never ran
        self.assertFalse(control.stopping.is_set())

    def test_a_refused_command_leaves_the_show_halted_not_dead(self):
        def refuse(command):
            raise RuntimeError("sudo: a password is required")
        control = SettingsControl(Config(), zero_output=lambda: True,
                                  run_command=refuse)
        with self.assertRaises(RuntimeError):
            control.power("shutdown")
        self.assertTrue(control.test_mode)
        self.assertFalse(control.stopping.is_set())

    def test_power_is_unavailable_without_both_callbacks(self):
        for control in (SettingsControl(Config()),
                        SettingsControl(Config(), zero_output=lambda: True),
                        SettingsControl(Config(), run_command=lambda c: None)):
            with self.assertRaises(RuntimeError):
                control.power("reboot")
            self.assertFalse(control.stopping.is_set())

    def test_power_drops_a_held_jet_test(self):
        calls = []
        control = SettingsControl(Config(), send_frame=calls.append,
                                  zero_output=lambda: True,
                                  run_command=lambda c: None)
        control.set_test_mode(True)
        control.test_jet(2, 10)
        control.power("reboot")
        self.assertIsNone(control.held)
        self.assertFalse(any(control.output_frame(None)))

    def test_power_rejects_any_other_action(self):
        control = self._control()
        with self.assertRaises(ValueError):
            control.power("halt")
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()


class TestProfileFile(unittest.TestCase):
    """The last applied profile outlives the process (NEXT_STEPS: the unlocked cap
    read 40 again after a restart)."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "data", "profile.json")

    def tearDown(self):
        self.dir.cleanup()

    def test_apply_writes_the_file_and_a_new_process_reads_it_back(self):
        control = SettingsControl(Config(), profile_path=self.path)
        profile = profile_for(control.cfg)
        profile["settings"]["hill_peak"] = 22
        profile["settings"]["height_max"] = 156
        control.apply(profile, unlock_height_max=True)
        fresh = Config()
        self.assertTrue(load_profile(fresh, self.path))
        self.assertEqual(fresh.hill_peak, 22)
        self.assertEqual(fresh.height_max, 156)
        self.assertEqual(fresh.strip_start, fresh.strip_points[0])

    def test_undo_and_reset_write_too(self):
        control = SettingsControl(Config(), profile_path=self.path)
        profile = profile_for(control.cfg)
        profile["settings"]["hill_peak"] = 22
        control.apply(profile)
        control.undo()
        fresh = Config()
        load_profile(fresh, self.path)
        self.assertEqual(fresh.hill_peak, 30)
        control.apply(profile)
        control.reset()
        load_profile(fresh, self.path)
        self.assertEqual(fresh.hill_peak, 30)

    def test_no_path_means_no_file(self):
        control = SettingsControl(Config())
        profile = profile_for(control.cfg)
        profile["settings"]["hill_peak"] = 22
        control.apply(profile)
        self.assertFalse(os.path.exists(self.path))

    def test_missing_file_is_silent(self):
        cfg = Config()
        self.assertFalse(load_profile(cfg, self.path))
        self.assertEqual(cfg.hill_peak, 30)

    def test_bad_file_is_skipped_not_fatal(self):
        os.makedirs(os.path.dirname(self.path))
        for text in ['{"version": 4, "settings"', '{"version": 1, "settings": {}}',
                     json.dumps({"version": PROFILE_VERSION,
                                 "settings": dict(profile_for(Config())["settings"], jet_count=99)})]:
            with open(self.path, "w") as f:
                f.write(text)
            cfg = Config()
            with contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertFalse(load_profile(cfg, self.path))
            self.assertIn("ignoring", err.getvalue())
            self.assertEqual(cfg.jet_count, 10)

    def test_write_is_whole_or_nothing(self):
        save_profile(profile_for(Config()), self.path)
        self.assertFalse(os.path.exists(self.path + ".tmp"))
        with open(self.path) as f:
            self.assertEqual(json.load(f)["version"], PROFILE_VERSION)

