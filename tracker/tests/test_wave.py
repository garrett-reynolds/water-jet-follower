"""Tests for the wave: tracks in, DMX frame out.

The one that matters most is TestCap. The modules latch their last value forever
when DMX stops, so a height that escapes the cap is not a glitch that clears
itself - it is a jet stuck up until somebody cuts the 24 V.
"""

import unittest

from tracker import dmx, geometry, wave
from tracker.config import Config


def track(id=1, s=0.5, speed=0.0, vx=0.0, vy=0.0, confirmed=True):
    return {"id": id, "s": s, "speed": speed, "vx": vx, "vy": vy,
            "confirmed": confirmed, "jet": 0}


def frame_of(*tracks):
    return {"tracks": list(tracks)}


def config_20():
    """The original two-module geometry used by the broad wave tests."""
    return Config(strip_start=(0.10, 0.0), strip_end=(1.05, 0.0),
                  jet_count=20, strip_points=())


class TestDefaultScope(unittest.TestCase):
    def test_default_uses_only_the_first_module(self):
        cfg = Config()
        self.assertEqual(cfg.jet_count, 10)
        self.assertEqual(dmx.height_channels(cfg.jet_count),
                         [5, 10, 15, 20, 25, 30, 35, 40, 45, 50])

    def test_calibrated_position_aims_at_its_jet(self):
        cfg = Config()
        x, y = cfg.strip_points[7]
        jet_position = geometry.strip_projection(x, y, cfg)["jet_position"]
        heights, _ = wave.Wave(cfg).heights_and_colours(
            frame_of({**track(), "s": 0.0, "jet_position": jet_position,
                      "x": x, "y": y}), 0.0)
        self.assertEqual(heights.index(max(heights)), 7)


class TestHillProfile(unittest.TestCase):
    def test_peak_in_the_middle(self):
        self.assertAlmostEqual(wave.hill_profile(0, 5), 1.0)

    def test_zero_at_and_beyond_the_edge(self):
        self.assertEqual(wave.hill_profile(2.5, 5), 0.0)
        self.assertEqual(wave.hill_profile(4.0, 5), 0.0)
        self.assertEqual(wave.hill_profile(-3.0, 5), 0.0)

    def test_symmetric(self):
        self.assertAlmostEqual(wave.hill_profile(1.0, 5),
                               wave.hill_profile(-1.0, 5))

    def test_falls_off_from_the_middle(self):
        values = [wave.hill_profile(d, 5) for d in (0, 0.5, 1.0, 1.5, 2.0)]
        self.assertEqual(values, sorted(values, reverse=True))


class TestHill(unittest.TestCase):
    def setUp(self):
        self.cfg = config_20()
        self.wave = wave.Wave(self.cfg)

    def test_no_tracks_means_no_water(self):
        heights, _ = self.wave.heights_and_colours(frame_of(), 0.0)
        self.assertEqual(max(heights), 0)

    def test_an_unconfirmed_track_gets_no_hill(self):
        heights, _ = self.wave.heights_and_colours(
            frame_of(track(confirmed=False)), 0.0)
        self.assertEqual(max(heights), 0)

    def test_the_hill_is_under_the_walker(self):
        pitch = wave.jet_pitch(self.cfg)
        for jet in (2, 9, 17):
            w = wave.Wave(self.cfg)
            heights, _ = w.heights_and_colours(
                frame_of(track(s=jet * pitch)), 0.0)
            self.assertEqual(heights.index(max(heights)), jet)

    def test_the_hill_is_about_five_jets_wide(self):
        pitch = wave.jet_pitch(self.cfg)
        heights, _ = self.wave.heights_and_colours(
            frame_of(track(s=10 * pitch)), 0.0)
        wet = [i for i, h in enumerate(heights) if h > 0]
        self.assertLessEqual(len(wet), self.cfg.hill_jets)
        self.assertGreaterEqual(len(wet), self.cfg.hill_jets - 2)

    def test_the_middle_reaches_hill_peak(self):
        pitch = wave.jet_pitch(self.cfg)
        heights, _ = self.wave.heights_and_colours(
            frame_of(track(s=10 * pitch)), 0.0)
        self.assertEqual(max(heights), self.cfg.hill_peak)

    def test_a_stopped_walker_keeps_their_hill(self):
        """Hold. The track still exists, so the hill must not go away."""
        pitch = wave.jet_pitch(self.cfg)
        stopped = track(s=8 * pitch, speed=0.0)
        for t in (0.0, 1.0, 5.0, 30.0):
            heights, _ = self.wave.heights_and_colours(frame_of(stopped), t)
            self.assertEqual(heights.index(max(heights)), 8)
            self.assertEqual(max(heights), self.cfg.hill_peak)

    def test_the_hill_leads_a_moving_walker(self):
        cfg = self.cfg
        pitch = wave.jet_pitch(cfg)
        still, _ = wave.Wave(cfg).heights_and_colours(
            frame_of(track(s=10 * pitch, vx=0.0)), 0.0)
        moving, _ = wave.Wave(cfg).heights_and_colours(
            frame_of(track(s=10 * pitch, vx=1.5)), 0.0)
        # Leading means the weight shifts towards the jets ahead of them.
        self.assertGreater(sum(moving[11:]), sum(still[11:]))


class TestOffStrip(unittest.TestCase):
    """Somebody across the room must not hold a jet up at the end of the strip.

    The tracker's `jet` field is clamped into 0..jet_count-1, so a person standing
    3 m away reports jet 19. The wave uses `s` in metres instead, which is what
    keeps them from raising water. Worth a test: reading `jet` here would look
    right in every unit test with a walker on the strip, and flood the last jet
    whenever anyone stood beyond it.
    """

    def setUp(self):
        self.cfg = config_20()
        self.strip_end_s = (self.cfg.jet_count - 1) * wave.jet_pitch(self.cfg)

    def test_a_walker_past_the_end_of_the_strip_gets_no_water(self):
        for s in (1.2, 2.0, 3.4):
            heights, _ = wave.Wave(self.cfg).heights_and_colours(
                frame_of(track(s=s)), 0.0)
            self.assertEqual(max(heights), 0, f"water raised for s={s}")

    def test_a_walker_before_the_start_gets_no_water(self):
        for s in (-0.5, -1.5):
            heights, _ = wave.Wave(self.cfg).heights_and_colours(
                frame_of(track(s=s)), 0.0)
            self.assertEqual(max(heights), 0, f"water raised for s={s}")

    def test_the_two_ends_of_the_strip_still_work(self):
        for s in (0.0, self.strip_end_s):
            heights, _ = wave.Wave(self.cfg).heights_and_colours(
                frame_of(track(s=s)), 0.0)
            self.assertEqual(max(heights), self.cfg.hill_peak)


class TestTwoWalkers(unittest.TestCase):
    def setUp(self):
        self.cfg = config_20()

    def test_two_walkers_get_two_hills(self):
        pitch = wave.jet_pitch(self.cfg)
        heights, _ = wave.Wave(self.cfg).heights_and_colours(
            frame_of(track(id=1, s=3 * pitch), track(id=2, s=15 * pitch)), 0.0)
        peaks = [i for i in range(1, 19)
                 if heights[i] > 0 and heights[i] >= heights[i - 1]
                 and heights[i] >= heights[i + 1]]
        self.assertEqual(peaks, [3, 15])

    def test_overlapping_hills_take_the_max_not_the_sum(self):
        """Summing two hills would climb past the cap. Max cannot."""
        pitch = wave.jet_pitch(self.cfg)
        heights, _ = wave.Wave(self.cfg).heights_and_colours(
            frame_of(track(id=1, s=10 * pitch), track(id=2, s=10 * pitch)), 0.0)
        self.assertEqual(max(heights), self.cfg.hill_peak)


class TestCap(unittest.TestCase):
    """No frame may ever carry a height above cfg.height_max. The modules latch."""

    def test_hill_peak_above_the_cap_is_still_capped(self):
        cfg = config_20()
        cfg.hill_peak = 250                     # someone edits this badly
        pitch = wave.jet_pitch(cfg)
        heights, _ = wave.Wave(cfg).heights_and_colours(
            frame_of(track(s=10 * pitch)), 0.0)
        self.assertEqual(max(heights), cfg.height_max)

    def test_no_height_slot_in_a_real_frame_exceeds_the_cap(self):
        cfg = config_20()
        cfg.hill_peak = 255
        pitch = wave.jet_pitch(cfg)
        w = wave.Wave(cfg)
        frame = w.frame(frame_of(track(id=1, s=4 * pitch, speed=2.0),
                                 track(id=2, s=12 * pitch, speed=0.1)), 0.0)
        for channel in dmx.height_channels(cfg.jet_count):
            self.assertLessEqual(frame[channel - 1], cfg.height_max)

    def test_clamp_heights_leaves_colour_alone(self):
        cfg = config_20()
        frame = dmx.blank_frame()
        for i in range(100):
            frame[i] = 200
        dmx.clamp_heights(frame, 40, cfg.jet_count)
        heights = set(dmx.height_channels(cfg.jet_count))
        for channel in range(1, 101):
            if channel in heights:
                self.assertEqual(frame[channel - 1], 40)
            else:
                self.assertEqual(frame[channel - 1], 200)

    def test_positive_water_is_raised_to_the_active_minimum(self):
        cfg = config_20()
        cfg.height_min = 12
        cfg.hill_peak = 20
        heights, _ = wave.Wave(cfg).heights_and_colours(
            frame_of(track(s=10 * wave.jet_pitch(cfg))), 0.0)
        self.assertTrue(all(height == 0 or height >= 12 for height in heights))


class TestFrameLayout(unittest.TestCase):
    def setUp(self):
        self.cfg = config_20()

    def test_frame_is_512_slots(self):
        frame = wave.Wave(self.cfg).frame(frame_of(), 0.0)
        self.assertEqual(len(frame), 512)

    def test_jet_zero_maps_to_channels_one_to_five(self):
        cfg = self.cfg
        cfg.base_colour = (11, 22, 33, 44)
        frame = wave.Wave(cfg).frame(frame_of(), 0.0)
        self.assertEqual(list(frame[0:4]), [11, 22, 33, 44])
        self.assertEqual(frame[4], 0)           # no track, so no water

    def test_jet_ten_starts_the_second_module_at_channel_51(self):
        cfg = self.cfg
        cfg.base_colour = (7, 0, 0, 0)
        frame = wave.Wave(cfg).frame(frame_of(), 0.0)
        self.assertEqual(frame[50], 7)          # channel 51

    def test_lights_only_forces_every_fountain_to_zero(self):
        cfg = self.cfg
        pitch = wave.jet_pitch(cfg)
        frame = wave.Wave(cfg).frame(
            frame_of(track(s=10 * pitch)), 0.0, lights_only=True)
        for channel in dmx.height_channels(cfg.jet_count):
            self.assertEqual(frame[channel - 1], 0)
        self.assertGreater(sum(frame), 0)       # pixels still lit

    def test_only_the_twenty_jets_are_touched(self):
        cfg = self.cfg
        pitch = wave.jet_pitch(cfg)
        frame = wave.Wave(cfg).frame(frame_of(track(s=10 * pitch)), 0.0)
        self.assertEqual(sum(frame[100:]), 0)   # nothing past channel 100

    def test_disabled_jet_is_all_off(self):
        cfg = self.cfg
        cfg.base_colour = (20, 20, 20, 20)
        cfg.jet_enabled = (False,) + (True,) * 19
        frame = wave.Wave(cfg).frame(frame_of(), 0.0)
        self.assertEqual(list(frame[:5]), [0, 0, 0, 0, 0])

    def test_reverse_order_swaps_the_output_ends(self):
        cfg = self.cfg
        cfg.base_colour = (0, 0, 0, 0)
        pitch = wave.jet_pitch(cfg)
        normal = wave.Wave(cfg).frame(frame_of(track(s=0.0)), 0.0)
        cfg.reverse_jets = True
        reversed_frame = wave.Wave(cfg).frame(frame_of(track(s=0.0)), 0.0)
        self.assertEqual(normal[4], reversed_frame[99])
        self.assertEqual(reversed_frame[4], 0)


class TestColour(unittest.TestCase):
    def setUp(self):
        self.cfg = config_20()

    def test_base_colour_where_there_is_no_hill(self):
        _, colours = wave.Wave(self.cfg).heights_and_colours(frame_of(), 0.0)
        self.assertEqual(set(colours), {tuple(self.cfg.base_colour)})

    def test_base_colour_outside_a_walker_hill(self):
        pitch = wave.jet_pitch(self.cfg)
        _, colours = wave.Wave(self.cfg).heights_and_colours(
            frame_of(track(s=10 * pitch, speed=0.0)), 0.0)
        self.assertEqual(colours[0], tuple(self.cfg.base_colour))

    def test_shoulder_colour_blends_from_base_by_hill_strength(self):
        pitch = wave.jet_pitch(self.cfg)
        _, colours = wave.Wave(self.cfg).heights_and_colours(
            frame_of(track(s=10 * pitch, speed=0.0)), 0.0)
        self.assertEqual(colours[9], (0, 0, 181, 0))

    def test_slow_walker_is_the_slow_colour(self):
        pitch = wave.jet_pitch(self.cfg)
        _, colours = wave.Wave(self.cfg).heights_and_colours(
            frame_of(track(s=10 * pitch, speed=0.0)), 0.0)
        self.assertEqual(colours[10], tuple(self.cfg.slow_colour))

    def test_fast_walker_is_the_fast_colour(self):
        cfg = self.cfg
        pitch = wave.jet_pitch(cfg)
        _, colours = wave.Wave(cfg).heights_and_colours(
            frame_of(track(s=10 * pitch, speed=cfg.fast_speed)), 0.0)
        self.assertEqual(colours[10], tuple(cfg.fast_colour))

    def test_tallest_overlapping_hill_owns_the_colour(self):
        cfg = self.cfg
        pitch = wave.jet_pitch(cfg)
        _, colours = wave.Wave(cfg).heights_and_colours(
            frame_of(track(id=1, s=10 * pitch, speed=0.0),
                     track(id=2, s=12 * pitch, speed=cfg.fast_speed)), 0.0)
        self.assertEqual(colours[10], tuple(cfg.slow_colour))

    def test_speed_is_smoothed_not_followed_instantly(self):
        """Raw tracker speed jitters; the colour must not strobe with it."""
        cfg = self.cfg
        pitch = wave.jet_pitch(cfg)
        w = wave.Wave(cfg)
        w.heights_and_colours(frame_of(track(s=10 * pitch, speed=0.0)), 0.0)
        _, colours = w.heights_and_colours(
            frame_of(track(s=10 * pitch, speed=cfg.fast_speed)), 0.05)
        self.assertNotEqual(colours[10], tuple(cfg.fast_colour))

    def test_a_gone_walker_stops_being_remembered(self):
        cfg = self.cfg
        w = wave.Wave(cfg)
        w.heights_and_colours(frame_of(track(id=9, speed=1.0)), 0.0)
        self.assertIn(9, w._smoothed_speed)
        w.heights_and_colours(frame_of(), 1.0)
        self.assertEqual(w._smoothed_speed, {})


class TestAttract(unittest.TestCase):
    def test_attract_is_off_by_default(self):
        """It runs unattended and the modules latch. It stays off until there is
        a watchdog that can drop the 24 V."""
        self.assertFalse(config_20().attract_enabled)
        heights, _ = wave.Wave(config_20()).heights_and_colours(frame_of(), 3.0)
        self.assertEqual(max(heights), 0)

    def test_attract_rolls_along_the_strip_when_enabled(self):
        cfg = config_20()
        cfg.attract_enabled = True
        seen = []
        for t in (0.0, 2.0, 4.0, 6.0):
            heights, _ = wave.Wave(cfg).heights_and_colours(frame_of(), t)
            seen.append(heights.index(max(heights)))
        self.assertEqual(seen, sorted(seen))
        self.assertGreater(seen[-1], seen[0])

    def test_attract_never_exceeds_its_own_height(self):
        cfg = config_20()
        cfg.attract_enabled = True
        for t in (0.0, 1.0, 2.5, 4.0, 7.9):
            heights, _ = wave.Wave(cfg).heights_and_colours(frame_of(), t)
            self.assertLessEqual(max(heights), cfg.attract_height)

    def test_a_walker_beats_attract(self):
        cfg = config_20()
        cfg.attract_enabled = True
        pitch = wave.jet_pitch(cfg)
        heights, _ = wave.Wave(cfg).heights_and_colours(
            frame_of(track(s=10 * pitch)), 3.0)
        self.assertEqual(max(heights), cfg.hill_peak)
        self.assertEqual(heights.index(max(heights)), 10)


class TestIdleAnimations(unittest.TestCase):
    def test_water_modes_are_off_by_default(self):
        cfg = config_20()
        self.assertEqual(cfg.idle_water_animation, "off")
        self.assertEqual(max(wave.Wave(cfg).heights_and_colours(frame_of(), 2)[0]), 0)

    def test_each_water_mode_is_capped(self):
        for mode in ("roll", "ripple", "pulse"):
            cfg = config_20()
            cfg.idle_water_animation = mode
            heights, _ = wave.Wave(cfg).heights_and_colours(frame_of(), 2)
            self.assertGreater(max(heights), 0)
            self.assertLessEqual(max(heights), cfg.height_max)

    def test_idle_height_sets_the_water_peak(self):
        cfg = config_20()
        cfg.idle_water_animation = "roll"
        cfg.idle_height = 9
        heights, _ = wave.Wave(cfg).heights_and_colours(frame_of(), 0)
        self.assertEqual(max(heights), 9)

    def test_each_colour_mode_obeys_brightness_limit(self):
        for mode in ("chase", "fade", "breathe"):
            cfg = config_20()
            cfg.idle_colour_animation = mode
            cfg.idle_brightness = 25
            _, colours = wave.Wave(cfg).heights_and_colours(frame_of(), 2)
            self.assertLessEqual(max(max(colour) for colour in colours), 25)

    def test_chase_has_a_dark_background_and_a_visible_peak(self):
        cfg = config_20()
        cfg.idle_colour_animation = "chase"
        cfg.idle_brightness = 64
        _, colours = wave.Wave(cfg).heights_and_colours(frame_of(), 0)
        self.assertEqual(colours[0], (0, 0, 64, 0))
        self.assertEqual(colours[-1], (0, 0, 0, 0))

    def test_idle_colour_sets_the_chase_colour(self):
        cfg = config_20()
        cfg.idle_colour_animation = "chase"
        cfg.idle_colour = (50, 10, 0, 0)
        _, colours = wave.Wave(cfg).heights_and_colours(frame_of(), 0)
        self.assertEqual(colours[0], (50, 10, 0, 0))

    def test_idle_seconds_sets_cycle_speed(self):
        cfg = config_20()
        cfg.idle_colour_animation = "chase"
        cfg.idle_seconds = 4
        _, start = wave.Wave(cfg).heights_and_colours(frame_of(), 0)
        _, end = wave.Wave(cfg).heights_and_colours(frame_of(), 4)
        self.assertEqual(start, end)

    def test_a_person_takes_control(self):
        cfg = config_20()
        cfg.idle_water_animation = "pulse"
        cfg.idle_colour_animation = "fade"
        heights, _ = wave.Wave(cfg).heights_and_colours(
            frame_of(track(s=10 * wave.jet_pitch(cfg))), 2)
        self.assertEqual(max(heights), cfg.hill_peak)


if __name__ == "__main__":
    unittest.main()
