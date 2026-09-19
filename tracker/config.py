"""All tunable numbers in one place.

Parameter names marked "leg_tracker" come from angusleigh/leg_tracker and keep that
project's spelling on purpose, so issue #12 item 6 maps straight onto a knob here.
Values marked "local" have no counterpart there and were chosen for this build.
"""

import json
from dataclasses import dataclass, field, asdict


@dataclass
class Config:
    # --- hardware -------------------------------------------------------
    port: str = "/dev/ttyLIDAR"          # udev name, see DECISIONS.md
    baudrate: int = 115200
    motor_pwm: int = 800                 # the logged decision; see the note below
    # Measured 2026-09-04 with tracker.run check, spin-up excluded:
    #   PWM 700 -> 13.71 Hz   PWM 730 -> 14.39 Hz
    #   PWM 760 -> 15.09 Hz   PWM 800 -> 16.25 Hz
    # PWM 800 is above the A2M8's rated 5-15 Hz band. PWM 760 is the rated edge.
    # Informational only: the tracker takes dt from the scan timestamps.
    scan_frequency: float = 16.25
    require_boost: bool = True           # ULTRA_CAPSULED only; Standard is unusable

    # --- geometry, metres ------------------------------------------------
    # World frame: LiDAR at (0, 0). +x runs along the strip, +y across the hallway.
    mount_angle_offset_deg: float = 0.0  # added to the raw LiDAR angle
    mirror: bool = False                 # flip angle sign if the scan comes out mirrored
    range_min: float = 0.15              # A2 minimum range
    range_max: float = 6.0
    # Nothing behind the sensor. Measured 2026-09-04: bench clutter beside the
    # LiDAR at x -0.35 to -0.05 held a false person for all 273 scans of a test
    # clip. Clipping at x >= 0 removed it. The cost is that the sensor is blind
    # behind itself, which is fine while it sits at one end of the strip.
    roi_x_min: float = 0.00
    roi_x_max: float = 3.50
    roi_y_min: float = -2.00
    roi_y_max: float = 2.00

    # --- the strip -------------------------------------------------------
    strip_start: tuple = (1.80, -1.64)   # measured person position for jet 0
    strip_end: tuple = (1.54, 1.20)      # measured person position for jet 9
    jet_count: int = 10                  # first HB-Laser module only, 50 mm pitch
    # Measured person positions for jets 0..9, in order. The tracker projects a
    # person onto the joined path and interpolates between each adjacent pair.
    strip_points: tuple = (
        (1.80, -1.64), (1.80, -1.32), (1.75, -1.00), (1.72, -0.73),
        (1.65, -0.48), (1.62, -0.19), (1.60, 0.07), (1.51, 0.47),
        (1.55, 0.65), (1.54, 1.20),
    )

    # --- background subtraction (local) ----------------------------------
    background_bin_deg: float = 1.0
    background_margin: float = 0.15      # a point must be this much nearer than baseline
    # Which percentile of a bin's distances counts as the room. 0.0 is the nearest
    # return, which needs a room with nobody in it. Higher ignores anybody who
    # spends less than that share of the clip on one bearing, so the baseline can be
    # built from a recording with somebody walking about in it.
    # Measured 2026-09-04 on synthetic walks: a person walking normally holds any
    # one bearing for about 12% of a clip. 0.35 leaves margin. A sweep on two real
    # bench recordings gave 0 false tracks at every value from 0.0 to 0.7, so the
    # margin costs nothing here. See scanfile.build_baseline.
    background_percentile: float = 0.35

    # --- clustering (leg_tracker) ----------------------------------------
    cluster_dist_euclid: float = 0.13
    min_points_per_cluster: int = 3
    max_detect_distance: float = 10.0

    # --- leg size gate (local) -------------------------------------------
    min_cluster_width: float = 0.02
    # Measured on a real 30 s walk, 2026-09-04: a person reads 0.45-0.62 m wide at
    # close range - both legs, the gap between them, and clothing. The first guess of
    # 0.45 threw him away for a whole pass; the tracker saw 20-50 foreground points
    # and produced no detection at all. A sweep put the knee at 0.65: it catches both
    # passes, and on the 60 s room clip it also cut the tracks from 8 to 7 and the
    # worst simultaneous count from 4 to 3. Above 0.65 nothing changes.
    max_cluster_width: float = 0.65

    # --- leg pairing (leg_tracker) ---------------------------------------
    max_leg_pairing_dist: float = 0.8

    # --- track lifecycle -------------------------------------------------
    # leg_tracker confirms a person only after the pair has travelled this far.
    # That rule is what fights the Hold behaviour; issue #12 item 6.
    dist_travelled_together_to_initiate_leg_pair: float = 0.5
    # local: the other way to confirm, so a person who is already standing is seen.
    # Set to 0 to disable and fall back to distance only.
    min_times_seen_to_initiate: int = 8
    max_seconds_unseen: float = 1.0      # local: coast this long through an occlusion

    # --- filter noise (leg_tracker) --------------------------------------
    std_obs: float = 0.1
    std_process_noise: float = 0.03333   # leg_tracker's value for 15 Hz
    max_association_dist: float = 0.6    # local: hard gate on top of the covariance gate

    # --- the wave --------------------------------------------------------
    # Heights are DMX values, 0-255. Measured on the bench 2026-09-04:
    # **0.762 cm per DMX unit**, linear through the origin, from two points
    # (DMX 20 -> 6 in, DMX 40 -> 12 in). So DMX 255 is about 1.94 m. Convert
    # before changing anything here: cm = dmx * 0.762, dmx = cm / 0.762.
    #
    # height_max is the safety cap and is not a design knob. dmx.clamp_heights
    # applies it to every height slot as the last step before a frame goes out,
    # so it holds even if the wave logic is wrong. The modules latch their last
    # value forever when DMX stops (see DECISIONS.md), so one bad height written
    # once stays up until somebody cuts the 24 V. 40 is 12 inches, which is what
    # has actually been run in the test basin.
    height_max: int = 40                 # 30.5 cm - the hard cap, tested
    hill_peak: int = 30                  # 22.9 cm - what the hill aims for
    hill_jets: int = 5                   # jets across one hill, from the wave decision
    # Where the hill sits relative to the walker. Positive leads them, which is
    # what the wave decision asks for. Lag is not modelled: the hill is symmetric
    # about a lead-shifted centre, which is close enough for v1.
    lead_seconds: float = 0.15

    # Attract: the empty-hallway roll. **Off by default and it must stay off**
    # until there is a contactor on the 24 V that a watchdog can drop. Attract is
    # unattended by definition, and the modules latch, so a crash mid-roll leaves
    # jets up in an empty room with nobody there to see it.
    attract_enabled: bool = False
    attract_height: int = 15             # 11.4 cm, about half the hill
    attract_seconds: float = 8.0         # one pass along the strip

    # Colour. Slow is blue, fast is white, on a dim base - the wave decision.
    # RGBW, 0-255 each.
    base_colour: tuple = (0, 0, 40, 0)
    slow_colour: tuple = (0, 0, 255, 0)
    fast_colour: tuple = (255, 255, 255, 255)
    fast_speed: float = 1.6              # m/s that counts as "fast"
    colour_tau: float = 0.5              # EMA seconds; raw speed is too jumpy

    # How often to re-send even when nothing changed. The modules latch, so a
    # repeat is not needed to hold a value - it is here so that a future watchdog
    # has a heartbeat to watch. Also keeps olad's buffer warm.
    resend_seconds: float = 0.5

    # --- viewer ----------------------------------------------------------
    viewer_host: str = "0.0.0.0"
    viewer_port: int = 8080

    @property
    def var_obs_local(self) -> float:
        return self.std_obs ** 2

    @property
    def var_obs(self) -> float:
        """leg_tracker weights association looser than the filter update."""
        return (self.std_obs + 0.4) ** 2

    def save(self, path):
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path):
        with open(path) as f:
            data = json.load(f)
        cfg = cls()
        for key, value in data.items():
            if hasattr(cfg, key):
                setattr(cfg, key, value)
        return cfg


DEFAULT = Config()
