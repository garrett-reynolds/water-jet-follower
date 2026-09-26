"""Tracks in, one DMX frame out. The behaviour from issue #7.

A **hill** is `hill_jets` jets wide, highest in the middle. One hill per confirmed
walker, centred a little ahead of them so the water leads rather than chases. Where
two hills overlap the taller one wins - they are combined with max, never summed,
because summing would climb past the cap.

Hold falls out for free: a walker who stops still has a track, so their hill stays
where it is. Nothing here needs to know the difference between walking and standing.

Colour follows speed, slow blue to fast white, over a dim base colour on every pixel
outside a hill. Speed straight off the tracker jitters enough to make the colour
flicker, so it goes through an exponential moving average first.

Everything in here is a pure function of the tracker's frame plus a clock. No I/O,
no DMX, no OLA - `run.py` does the sending. That is what lets the whole behaviour be
tested against recorded walks with no water and no hardware.
"""

import math

from tracker import dmx, geometry


def hill_profile(distance_jets, hill_jets):
    """Height of a hill at `distance_jets` from its middle, as 0.0 to 1.0.

    A raised cosine: 1.0 in the middle, falling to 0.0 at the hill's edge. Smooth
    rather than triangular so the water does not step as the walker moves between
    two jets.
    """
    half_width = hill_jets / 2.0
    if half_width <= 0 or abs(distance_jets) >= half_width:
        return 0.0
    return 0.5 * (1.0 + math.cos(math.pi * distance_jets / half_width))


def jet_pitch(cfg):
    """Average path distance between two mapped jets."""
    points = geometry.strip_points(cfg)
    length = sum(math.hypot(b[0] - a[0], b[1] - a[1])
                 for a, b in zip(points, points[1:]))
    return length / max(1, cfg.jet_count - 1)


def strip_velocity(track, cfg):
    """The walker's speed along the strip axis, signed. Sideways motion ignored."""
    x0, y0 = cfg.strip_start
    x1, y1 = cfg.strip_end
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length == 0:
        return 0.0
    return (track.get("vx", 0.0) * dx + track.get("vy", 0.0) * dy) / length


def strip_velocity_jets(track, cfg):
    """Walk speed along the calibrated path, in jet gaps per second."""
    if "jet_position" not in track or "x" not in track or "y" not in track:
        pitch = jet_pitch(cfg)
        return strip_velocity(track, cfg) / pitch if pitch else 0.0
    projection = geometry.strip_projection(track["x"], track["y"], cfg)
    length = projection["segment_length"]
    if length == 0:
        return 0.0
    tx, ty = projection["tangent"]
    metres_per_second = (track.get("vx", 0.0) * tx
                         + track.get("vy", 0.0) * ty)
    return metres_per_second / length


def lerp_colour(a, b, amount):
    amount = max(0.0, min(1.0, amount))
    return tuple(int(round(x + (y - x) * amount)) for x, y in zip(a, b))


class Wave:
    """Holds the little state the wave needs: smoothed speeds and the attract clock.

    One instance per run. `frame()` is called once per scan.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self._smoothed_speed = {}       # track id -> EMA of speed
        self._smoothed_position = {}    # track id -> followed jet position
        self._last_time = None

    def _smooth(self, track, dt):
        """EMA the track's speed so the colour does not flicker."""
        cfg = self.cfg
        speed = track.get("speed", 0.0)
        previous = self._smoothed_speed.get(track["id"])
        if previous is None or cfg.colour_tau <= 0 or dt <= 0:
            value = speed
        else:
            alpha = 1.0 - math.exp(-dt / cfg.colour_tau)
            value = previous + alpha * (speed - previous)
        self._smoothed_speed[track["id"]] = value
        return value

    def heights_and_colours(self, tracker_frame, now):
        """The wave as plain numbers: a height and an RGBW per jet.

        Returns (heights, colours), both `jet_count` long. Heights are DMX values
        already capped at cfg.height_max; colours are RGBW tuples.
        """
        cfg = self.cfg
        dt = 0.0 if self._last_time is None else max(0.0, now - self._last_time)
        self._last_time = now

        pitch = jet_pitch(cfg)
        heights = [0.0] * cfg.jet_count
        # Weighted colour per jet: whichever hill is tallest at that jet owns it.
        owner_strength = [0.0] * cfg.jet_count
        colours = [tuple(cfg.base_colour)] * cfg.jet_count

        tracks = [t for t in tracker_frame.get("tracks", []) if t.get("confirmed")]
        live_ids = {t["id"] for t in tracks}
        for stale in set(self._smoothed_speed) - live_ids:
            del self._smoothed_speed[stale]
        for stale in set(self._smoothed_position) - live_ids:
            del self._smoothed_position[stale]

        for track in tracks:
            if "jet_position" in track:
                centre_jet = (track["jet_position"]
                              + strip_velocity_jets(track, cfg) * cfg.lead_seconds)
            else:
                centre_s = track["s"] + strip_velocity(track, cfg) * cfg.lead_seconds
                centre_jet = centre_s / pitch if pitch else 0.0
            previous_position = self._smoothed_position.get(track["id"])
            if previous_position is not None and cfg.follow_response > 0 and dt > 0:
                follow_alpha = 1.0 - math.exp(-dt / cfg.follow_response)
                centre_jet = previous_position + follow_alpha * (centre_jet - previous_position)
            self._smoothed_position[track["id"]] = centre_jet
            speed = self._smooth(track, dt)
            speed_range = cfg.fast_speed - cfg.slow_speed
            amount = ((speed - cfg.slow_speed) / speed_range
                      if speed_range > 0 else 0.0)
            colour = lerp_colour(cfg.slow_colour, cfg.fast_colour, amount)

            for jet in range(cfg.jet_count):
                strength = hill_profile(jet - centre_jet, cfg.hill_jets)
                if strength <= 0.0:
                    continue
                # max, not sum: two overlapping hills must not stack past the cap.
                heights[jet] = max(heights[jet], strength * cfg.hill_peak)
                if strength > owner_strength[jet]:
                    owner_strength[jet] = strength
                    colours[jet] = lerp_colour(cfg.base_colour, colour, strength)

        if not tracks:
            water_mode = cfg.idle_water_animation
            if cfg.attract_enabled and water_mode == "off":
                water_mode = "roll"
            self._idle_water(heights, now, water_mode)
            self._idle_colour(colours, now, cfg.idle_colour_animation)

        capped = [0 if h <= 0 else min(max(int(round(h)), cfg.height_min),
                                      cfg.height_max)
                  for h in heights]
        return capped, colours

    def _attract(self, heights, colours, now):
        """One half-height hill rolling end to end, for an empty hallway.

        Off unless cfg.attract_enabled. See the config comment for why: this runs
        with nobody watching, and the modules latch.
        """
        cfg = self.cfg
        if cfg.attract_seconds <= 0:
            return
        phase = (now % cfg.attract_seconds) / cfg.attract_seconds
        centre_jet = phase * (cfg.jet_count - 1)
        for jet in range(cfg.jet_count):
            strength = hill_profile(jet - centre_jet, cfg.hill_jets)
            if strength > 0.0:
                heights[jet] = max(heights[jet], strength * cfg.attract_height)
                colours[jet] = lerp_colour(cfg.base_colour, cfg.slow_colour,
                                           strength)

    def _idle_water(self, heights, now, mode):
        cfg = self.cfg
        if mode == "off" or cfg.idle_seconds <= 0:
            return
        phase = (now % cfg.idle_seconds) / cfg.idle_seconds
        if mode == "pulse":
            level = (0.5 - 0.5 * math.cos(2 * math.pi * phase)) * cfg.idle_height
            heights[:] = [level] * cfg.jet_count
            return
        width = cfg.hill_jets if mode == "roll" else max(2, cfg.hill_jets / 2)
        centre = phase * (cfg.jet_count - 1)
        for jet in range(cfg.jet_count):
            heights[jet] = hill_profile(jet - centre, width) * cfg.idle_height

    def _idle_colour(self, colours, now, mode):
        cfg = self.cfg
        if mode == "off" or cfg.idle_seconds <= 0:
            return
        phase = (now % cfg.idle_seconds) / cfg.idle_seconds
        amount = 0.5 - 0.5 * math.cos(2 * math.pi * phase)
        if mode == "fade":
            colours[:] = [lerp_colour(cfg.idle_start_colour,
                                      cfg.idle_end_colour, amount)] * cfg.jet_count
        elif mode == "breathe":
            palette_colour = lerp_colour(cfg.idle_start_colour,
                                         cfg.idle_end_colour, amount)
            colours[:] = [lerp_colour((0, 0, 0, 0), palette_colour,
                                      0.2 + 0.8 * amount)] * cfg.jet_count
        elif mode == "chase":
            centre = phase * (cfg.jet_count - 1)
            colours[:] = [lerp_colour(cfg.idle_start_colour, cfg.idle_end_colour,
                                      hill_profile(jet - centre, cfg.hill_jets))
                          for jet in range(cfg.jet_count)]
        colours[:] = [tuple(min(cfg.idle_brightness, value) for value in colour)
                      for colour in colours]

    def output_values(self, tracker_frame, now):
        """Logical Jet values after the same enabled-Jet rule used by output."""
        heights, colours = self.heights_and_colours(tracker_frame, now)
        enabled = tuple(self.cfg.jet_enabled)
        if len(enabled) != self.cfg.jet_count:
            enabled = (True,) * self.cfg.jet_count
        for jet, on in enumerate(enabled):
            if not on:
                heights[jet] = 0
                colours[jet] = (0, 0, 0, 0)
        return heights, colours

    def frame(self, tracker_frame, now, lights_only=False):
        """The full 512-slot DMX frame for one scan.

        `lights_only` zeroes every fountain channel and leaves the pixels alone. It
        is how the whole wave gets watched running against a recorded walk with no
        water moving at all.
        """
        cfg = self.cfg
        heights, colours = self.output_values(tracker_frame, now)
        frame = dmx.blank_frame()

        for jet in range(cfg.jet_count):
            output = cfg.jet_count - 1 - jet if cfg.reverse_jets else jet
            module = output // dmx.NOZZLES_PER_HD_MODULE + 1
            nozzle = output % dmx.NOZZLES_PER_HD_MODULE + 1
            base = dmx.channel_for(nozzle, dmx.RED, dmx.NOZZLES_PER_HD_MODULE,
                                   module)
            red, green, blue, white = colours[jet]
            frame[base - 1] = dmx.clamp(red)
            frame[base + 0] = dmx.clamp(green)
            frame[base + 1] = dmx.clamp(blue)
            frame[base + 2] = dmx.clamp(white)
            frame[base + 3] = 0 if lights_only else dmx.clamp(heights[jet])

        # Belt and braces. heights_and_colours already caps, but this is the one
        # guard that does not trust the wave logic above it.
        return dmx.clamp_heights(frame, cfg.height_max, cfg.jet_count)
