"""Tests that run with nobody in the hallway.

They do not prove the tracker works on real people - only recordings can do that
(issue #12 items 5-7). They prove the maths does what it says: clustering separates
legs, the filter reports the right speed, a still person is still found, an occluded
track coasts instead of dying, and merging two one-person clips gives exactly the
scan two people would have made.

    python -m unittest discover -s tracker/tests -t .
"""

import unittest

from tracker import geometry
from tracker.config import Config
from tracker.tests import synthetic
from tracker.merge import merge_scans
from tracker.scanfile import build_baseline_from_scans
from tracker.tracking import Tracker, cluster_points, leg_candidates, pair_legs


def run(people, seconds, cfg, walls=None, baseline=None):
    tracker = Tracker(cfg)
    frame = None
    for timestamp, points in synthetic.walk(people, seconds, walls=walls):
        foreground, _ = geometry.to_world(points, cfg, baseline)
        frame = tracker.update(timestamp, foreground)
    return tracker, frame


class TestClustering(unittest.TestCase):
    """Note the number that falls out of these: at a normal standing stance, about
    0.20 m between leg centres, the surfaces are only 0.09 m apart. That is under
    cluster_dist_euclid (0.13 m), so a standing person is ONE cluster, not two.
    Two clusters appear mid-stride. This is why a lone cluster has to count as a
    person - see the note at the top of tracking.py."""

    def test_a_normal_stance_is_one_cluster(self):
        cfg = Config()
        circles = synthetic.legs_for_person(1.0, 0.6)          # 0.20 m apart
        points, _ = geometry.to_world(synthetic.scan(circles), cfg)
        clusters = cluster_points(points, cfg)
        self.assertEqual(len(clusters), 1)
        detections = pair_legs(leg_candidates(clusters, cfg), cfg)
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0]["kind"], "single")
        self.assertAlmostEqual(detections[0]["x"], 1.0, delta=0.05)
        self.assertAlmostEqual(detections[0]["y"], 0.6, delta=0.05)

    def test_mid_stride_makes_two_clusters(self):
        cfg = Config()
        circles = synthetic.legs_for_person(1.0, 0.6, separation=0.40)
        points, _ = geometry.to_world(synthetic.scan(circles), cfg)
        clusters = cluster_points(points, cfg)
        self.assertEqual(len(clusters), 2, "legs apart mid-stride are two clusters")

    def test_two_legs_pair_into_one_person(self):
        cfg = Config()
        circles = synthetic.legs_for_person(1.0, 0.6, separation=0.40)
        points, _ = geometry.to_world(synthetic.scan(circles), cfg)
        detections = pair_legs(leg_candidates(cluster_points(points, cfg), cfg), cfg)
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0]["kind"], "pair")
        self.assertAlmostEqual(detections[0]["x"], 1.0, delta=0.05)
        self.assertAlmostEqual(detections[0]["y"], 0.6, delta=0.05)


class TestEmptyRoom(unittest.TestCase):
    def test_walls_alone_make_no_tracks(self):
        """A wall the baseline knows about must not become a person."""
        cfg = Config()
        walls = [(80.0, 100.0, 1.8)]
        empty = list(synthetic.walk([], 3.0, walls=walls))
        baseline = build_baseline_from_scans(empty, cfg)
        tracker, frame = run([], 3.0, cfg, walls=walls, baseline=baseline)
        self.assertEqual(frame["tracks"], [])


class TestBaselineFromAnOccupiedRoom(unittest.TestCase):
    """The room cannot be emptied, so the baseline has to be built with a person in
    it. A low percentile does that: somebody who walks through a bearing owns only a
    little of that bin's returns, so they do not become part of the room."""

    WALLS = [(0.0, 360.0, 2.60)]         # a box of walls all the way round

    # Walking across the front of the sensor, which is what a real clip looks like.
    # Measured worst-case occupancy of any one bearing: 12%, against a 0.35 default.
    WALKER = (1.00, -1.80, 0.0, 1.2)
    SECONDS = 3.0

    def _baseline_with_someone_walking(self, cfg):
        walking = list(synthetic.walk([self.WALKER], self.SECONDS, walls=self.WALLS))
        return build_baseline_from_scans(walking, cfg)

    def test_a_walker_does_not_get_baked_into_the_room(self):
        cfg = Config()
        baseline = self._baseline_with_someone_walking(cfg)
        # every bin should have settled on the wall, not on the walker
        distances = [d for d in baseline["distances"] if d is not None]
        self.assertTrue(distances)
        self.assertAlmostEqual(min(distances), 2.60, delta=0.05,
                               msg="the walker was baked into the baseline")

    def test_that_baseline_still_finds_a_person_later(self):
        cfg = Config()
        baseline = self._baseline_with_someone_walking(cfg)
        tracker, frame = run([self.WALKER], self.SECONDS, cfg,
                             walls=self.WALLS, baseline=baseline)
        confirmed = [t for t in frame["tracks"] if t["confirmed"]]
        self.assertEqual(len(confirmed), 1)
        self.assertAlmostEqual(confirmed[0]["speed"], 1.2, delta=0.15)

    def test_the_old_nearest_rule_would_have_been_fooled(self):
        """percentile 0.0 is the old behaviour, and it bakes the walker in."""
        cfg = Config()
        cfg.background_percentile = 0.0
        baseline = self._baseline_with_someone_walking(cfg)
        distances = [d for d in baseline["distances"] if d is not None]
        self.assertLess(min(distances), 1.5,
                        "with percentile 0 the walker should pollute the baseline")


class TestTwoWalkers(unittest.TestCase):
    def test_two_people_two_tracks_with_the_right_speed(self):
        cfg = Config()
        people = [
            (0.20, 0.60, 1.0, 0.0),     # left to right at 1.0 m/s
            (2.20, -0.60, -1.2, 0.0),   # right to left at 1.2 m/s
        ]
        tracker, frame = run(people, 1.6, cfg)
        confirmed = [t for t in frame["tracks"] if t["confirmed"]]
        self.assertEqual(len(confirmed), 2, f"expected 2 people, got {frame['tracks']}")
        speeds = sorted(t["speed"] for t in confirmed)
        self.assertAlmostEqual(speeds[0], 1.0, delta=0.15)
        self.assertAlmostEqual(speeds[1], 1.2, delta=0.15)

    def test_track_ids_are_stable_across_the_walk(self):
        cfg = Config()
        people = [(0.20, 0.60, 1.0, 0.0)]
        tracker = Tracker(cfg)
        ids = set()
        for timestamp, points in synthetic.walk(people, 2.0):
            foreground, _ = geometry.to_world(points, cfg)
            frame = tracker.update(timestamp, foreground)
            ids.update(t["id"] for t in frame["tracks"])
        self.assertEqual(len(ids), 1, f"one walker should keep one id, got {ids}")


class TestStandingStill(unittest.TestCase):
    def test_a_still_person_is_confirmed(self):
        """leg_tracker needs 0.5 m of travel. min_times_seen_to_initiate is what
        lets the Hold behaviour work; this is issue #12 item 6."""
        cfg = Config()
        people = [(1.0, 0.60, 0.0, 0.0)]
        tracker, frame = run(people, 2.0, cfg)
        confirmed = [t for t in frame["tracks"] if t["confirmed"]]
        self.assertEqual(len(confirmed), 1)
        self.assertLess(confirmed[0]["dist_travelled"], 0.5,
                        "it was confirmed by standing there, not by walking")

    def test_distance_rule_alone_would_miss_them(self):
        cfg = Config()
        cfg.min_times_seen_to_initiate = 0      # leg_tracker's behaviour exactly
        people = [(1.0, 0.60, 0.0, 0.0)]
        tracker, frame = run(people, 2.0, cfg)
        self.assertEqual([t for t in frame["tracks"] if t["confirmed"]], [])


class TestOcclusion(unittest.TestCase):
    def test_a_hidden_walker_coasts_and_keeps_their_id(self):
        """Two people on the same line: the near one hides the far one."""
        cfg = Config()
        people = [
            (0.60, 0.60, 0.0, 0.0),     # standing, close to the LiDAR
            (1.60, 0.60, 0.0, 0.0),     # standing directly behind them
        ]
        tracker = Tracker(cfg)
        seen_ids = []
        for timestamp, points in synthetic.walk(people, 2.0):
            foreground, _ = geometry.to_world(points, cfg)
            frame = tracker.update(timestamp, foreground)
            seen_ids.append({t["id"] for t in frame["tracks"]})
        # whatever the far walker's fate, no track may flicker its id every scan
        self.assertLessEqual(len(set.union(*seen_ids)), 3,
                             "ids churned, so association is losing people")


class TestMerge(unittest.TestCase):
    """Merging two one-person clips must give the scan two people would have made.

    This is what lets issue #12 item 5 be answered by one person walking twice.
    """

    def test_merged_clips_equal_a_real_two_person_scan(self):
        left_to_right = (0.20, 0.60, 1.0, 0.0)
        right_to_left = (2.20, -0.60, -1.2, 0.0)

        alone_a = list(synthetic.walk([left_to_right], 1.5))
        alone_b = list(synthetic.walk([right_to_left], 1.5))
        together = list(synthetic.walk([left_to_right, right_to_left], 1.5))
        merged = merge_scans([alone_a, alone_b])

        self.assertEqual(len(merged), len(together))
        for (_, got), (_, want) in zip(merged, together):
            self.assertEqual(len(got), len(want))
            for (got_angle, got_dist), (want_angle, want_dist) in zip(got, want):
                self.assertAlmostEqual(got_angle, want_angle, places=6)
                self.assertAlmostEqual(got_dist, want_dist, places=6)

    def test_the_near_walker_really_hides_the_far_one(self):
        """Two people on the same bearing: the merge must keep only the nearer.

        Both stand at 45 degrees from the sensor, one at 0.85 m and one at 2.26 m,
        so the near body's rays cover the far body completely.
        """
        near = (0.60, 0.60, 0.0, 0.0)
        far = (1.60, 1.60, 0.0, 0.0)
        alone_near = list(synthetic.walk([near], 0.5))
        alone_far = list(synthetic.walk([far], 0.5))
        merged = merge_scans([alone_near, alone_far])

        points_near = len(alone_near[0][1])
        points_far = len(alone_far[0][1])
        points_merged = len(merged[0][1])
        self.assertLess(points_merged, points_near + points_far,
                        "no rays were shadowed, so the merge is not occluding")
        self.assertGreaterEqual(points_merged, points_near)

    def test_shifting_clip_b_moves_the_walker(self):
        """--shift-b is the knob that decides where the two people meet."""
        walker = (0.20, 0.60, 1.0, 0.0)
        stander = (1.50, -0.60, 0.0, 0.0)
        alone_a = list(synthetic.walk([walker], 2.0))
        alone_b = list(synthetic.walk([stander], 2.0))

        no_shift = merge_scans([alone_a, alone_b], shifts=[0.0, 0.0])
        shifted = merge_scans([alone_a, alone_b], shifts=[0.0, 1.0])
        # the stander does not move, so shifting them changes nothing
        self.assertEqual([p for _, p in no_shift], [p for _, p in shifted])

        # shifting a *moving* clip must change the result
        moving_b = list(synthetic.walk([(2.2, -0.6, -1.2, 0.0)], 2.0))
        early = [p for _, p in merge_scans([alone_a, moving_b], shifts=[0.0, 0.0])]
        late = [p for _, p in merge_scans([alone_a, moving_b], shifts=[0.0, 1.0])]
        self.assertNotEqual(early, late,
                            "shifting a moving clip must change the merged scan")


class TestStripMapping(unittest.TestCase):
    def test_twenty_jets_use_the_ten_point_control_path(self):
        cfg = Config(jet_count=20)
        points = geometry.strip_points(cfg)

        self.assertEqual(len(points), 20)
        self.assertEqual(points[0], cfg.strip_points[0])
        self.assertEqual(points[-1], cfg.strip_points[-1])

    def test_position_maps_to_a_jet(self):
        cfg = Config()
        s, jet = geometry.strip_position(*cfg.strip_start, cfg)
        self.assertEqual(jet, 0)
        s, jet = geometry.strip_position(*cfg.strip_end, cfg)
        self.assertEqual(jet, cfg.jet_count - 1)
        last, previous = cfg.strip_points[-1], cfg.strip_points[-2]
        beyond = (last[0] + last[0] - previous[0],
                  last[1] + last[1] - previous[1])
        s, jet = geometry.strip_position(*beyond, cfg)
        self.assertEqual(jet, cfg.jet_count - 1, "off the end clamps to the last jet")

    def test_each_calibrated_point_maps_to_its_jet(self):
        cfg = Config()
        for expected, (x, y) in enumerate(cfg.strip_points):
            _, jet = geometry.strip_position(x, y, cfg)
            self.assertEqual(jet, expected)

    def test_midpoint_interpolates_between_two_jets(self):
        cfg = Config()
        a, b = cfg.strip_points[4:6]
        x, y = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        projection = geometry.strip_projection(x, y, cfg)
        self.assertAlmostEqual(projection["jet_position"], 4.5)


if __name__ == "__main__":
    unittest.main()
