"""Validated, atomic settings changes for the browser control screen."""

from copy import deepcopy

from tracker import dmx
from tracker.config import Config


PROFILE_VERSION = 3
EDITABLE = (
    "strip_points", "jet_count", "height_min", "hill_peak", "height_max",
    "hill_jets", "lead_seconds", "follow_response", "base_colour",
    "slow_colour", "fast_colour", "slow_speed", "fast_speed",
    "jet_enabled", "reverse_jets", "idle_water_animation",
    "idle_colour_animation", "idle_brightness",
    "idle_seconds", "idle_height", "idle_colour",
)


def _enabled(cfg):
    values = tuple(getattr(cfg, "jet_enabled", ()))
    return values if len(values) == cfg.jet_count else (True,) * cfg.jet_count


def profile_for(cfg):
    settings = {}
    for name in EDITABLE:
        value = _enabled(cfg) if name == "jet_enabled" else getattr(cfg, name)
        settings[name] = deepcopy(value)
    return {"version": PROFILE_VERSION, "settings": settings}


def _number(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    if not low <= value <= high:
        raise ValueError(f"{name} must be from {low} to {high}")
    return value


def validate_profile(profile):
    if not isinstance(profile, dict) or profile.get("version") != PROFILE_VERSION:
        raise ValueError(f"profile version must be {PROFILE_VERSION}")
    values = profile.get("settings")
    if not isinstance(values, dict) or set(values) != set(EDITABLE):
        raise ValueError("profile must contain the complete settings set")

    clean = {}
    clean["jet_count"] = int(_number(values["jet_count"], "jet_count", 1, 20))
    clean["height_max"] = int(_number(values["height_max"], "height_max", 1, 255))
    clean["height_min"] = int(_number(values["height_min"], "height_min", 1,
                                      clean["height_max"]))
    clean["hill_peak"] = int(_number(values["hill_peak"], "hill_peak",
                                     clean["height_min"], clean["height_max"]))
    clean["hill_jets"] = int(_number(values["hill_jets"], "hill_jets", 1, 20))
    clean["lead_seconds"] = float(_number(values["lead_seconds"], "lead_seconds", 0, 2))
    clean["follow_response"] = float(_number(values["follow_response"],
                                               "follow_response", 0, 5))
    clean["slow_speed"] = float(_number(values["slow_speed"], "slow_speed", 0, 10))
    clean["fast_speed"] = float(_number(values["fast_speed"], "fast_speed", 0, 10))
    clean["idle_brightness"] = int(_number(values["idle_brightness"],
                                             "idle_brightness", 0, 255))
    clean["idle_seconds"] = float(_number(values["idle_seconds"],
                                           "idle_seconds", 0.5, 120))
    clean["idle_height"] = int(_number(values["idle_height"], "idle_height",
                                         clean["height_min"], clean["height_max"]))
    if clean["fast_speed"] <= clean["slow_speed"]:
        raise ValueError("fast_speed must be greater than slow_speed")

    points = values["strip_points"]
    if not isinstance(points, (list, tuple)) or not 2 <= len(points) <= 20:
        raise ValueError("strip_points must contain 2 to 20 points")
    clean["strip_points"] = tuple(
        (float(_number(point[0], "point x", -20, 20)),
         float(_number(point[1], "point y", -20, 20)))
        for point in points
        if isinstance(point, (list, tuple)) and len(point) == 2
    )
    if len(clean["strip_points"]) != len(points):
        raise ValueError("each strip point must contain x and y")

    for name in ("base_colour", "slow_colour", "fast_colour", "idle_colour"):
        colour = values[name]
        if not isinstance(colour, (list, tuple)) or len(colour) != 4:
            raise ValueError(f"{name} must contain RGBW")
        clean[name] = tuple(int(_number(item, name, 0, 255)) for item in colour)

    enabled = values["jet_enabled"]
    if (not isinstance(enabled, (list, tuple))
            or len(enabled) != clean["jet_count"]
            or any(not isinstance(item, bool) for item in enabled)):
        raise ValueError("jet_enabled must have one true or false per jet")
    clean["jet_enabled"] = tuple(enabled)
    if not isinstance(values["reverse_jets"], bool):
        raise ValueError("reverse_jets must be true or false")
    clean["reverse_jets"] = values["reverse_jets"]
    for name, allowed in (
            ("idle_water_animation", {"off", "roll", "ripple", "pulse"}),
            ("idle_colour_animation", {"off", "chase", "fade", "breathe"})):
        if values[name] not in allowed:
            raise ValueError(f"{name} is not valid")
        clean[name] = values[name]
    return clean


UNDO_DEPTH = 50


class SettingsControl:
    """Own settings history and hardware actions for one viewer process."""

    def __init__(self, cfg, send_frame=None, zero_output=None):
        self.cfg = cfg
        self.send_frame = send_frame
        self.zero_output = zero_output
        self.lights_only = False
        # Test mode: the live show sends nothing. Only a held jet test or zeros go
        # out, so a person walking past the LiDAR cannot put water up while somebody
        # has their hand on a jet. Entered by the /test page or by ALL OFF. Left only
        # by an explicit resume, never by a page closing.
        self.test_mode = False
        self._manual_frame = None
        # The held jet test, {"jet", "height"}, so a reloaded page can show it.
        self.held = None
        self._undo = []
        self._reset = profile_for(Config())

    def profile(self):
        return profile_for(self.cfg)

    def defaults(self):
        return deepcopy(self._reset)

    def apply(self, profile, unlock_height_max=False):
        clean = validate_profile(profile)
        if clean["height_max"] != self.cfg.height_max and not unlock_height_max:
            raise PermissionError("unlock the hard maximum before changing it")
        previous = self.profile()
        clean["strip_start"] = clean["strip_points"][0]
        clean["strip_end"] = clean["strip_points"][-1]
        self.cfg.__dict__.update(clean)
        self._undo.append(previous)
        # Live-apply sends a profile per edit burst, so the stack is bounded.
        del self._undo[:-UNDO_DEPTH]
        return self.profile()

    def undo(self):
        if not self._undo:
            raise ValueError("nothing to undo")
        profile = self._undo.pop()
        clean = validate_profile(profile)
        clean["strip_start"] = clean["strip_points"][0]
        clean["strip_end"] = clean["strip_points"][-1]
        self.cfg.__dict__.update(clean)
        return self.profile()

    def reset(self):
        return self.apply(deepcopy(self._reset), unlock_height_max=True)

    def set_lights_only(self, enabled):
        if not isinstance(enabled, bool):
            raise ValueError("lights_only must be true or false")
        self.lights_only = enabled
        return self.lights_only

    def set_test_mode(self, enabled):
        """Turn test mode on or off. Both directions zero the output first.

        On: the live show stops sending, so the modules must not be left latched
        at whatever hill was up. Off: any held jet test is dropped before the show
        gets the output back. The flag changes even when the zero cannot be
        verified, because halting the live show is the safer half of either move;
        the caller gets the verification result to report.
        """
        if not isinstance(enabled, bool):
            raise ValueError("test_mode must be true or false")
        all_zero = self._zero_if_possible()
        self._manual_frame = None
        self.held = None
        self.test_mode = enabled
        return {"enabled": self.test_mode, "all_zero": all_zero}

    def _zero_if_possible(self):
        if self.zero_output is None:
            return None
        return bool(self.zero_output())

    def all_off(self):
        """Zero everything and halt the live show. ALL OFF always enters test mode,
        otherwise the next scan puts the hill straight back and the button looks dead."""
        if self.zero_output is None:
            raise RuntimeError("ALL OFF is not available in this run mode")
        result = bool(self.zero_output())
        self._manual_frame = None
        self.held = None
        self.test_mode = True
        return result

    def test_jet(self, jet, height=None):
        if self.send_frame is None:
            raise RuntimeError("jet test is not available in this run mode")
        if self.lights_only:
            raise ValueError("turn lights-only off before starting a water test")
        if not self.test_mode:
            raise ValueError("open the test page first; jet tests only run in test mode")
        if not isinstance(jet, int) or not 0 <= jet < self.cfg.jet_count:
            raise ValueError("jet is outside the configured range")
        if not _enabled(self.cfg)[jet]:
            raise ValueError("jet is disabled")
        height = self.cfg.height_min if height is None else height
        if isinstance(height, bool) or not isinstance(height, (int, float)):
            raise ValueError("test height must be a number")
        if not self.cfg.height_min <= height <= self.cfg.height_max:
            raise ValueError(
                f"test height must be from {self.cfg.height_min} to {self.cfg.height_max}")
        output = self.cfg.jet_count - 1 - jet if self.cfg.reverse_jets else jet
        module = output // dmx.NOZZLES_PER_HD_MODULE + 1
        nozzle = output % dmx.NOZZLES_PER_HD_MODULE + 1
        base = dmx.channel_for(nozzle, dmx.RED, module=module)
        frame = dmx.blank_frame()
        for offset, value in enumerate(self.cfg.slow_colour):
            frame[base - 1 + offset] = dmx.clamp(value)
        frame[base + 3] = dmx.clamp(height, high=self.cfg.height_max)
        self._manual_frame = frame
        self.held = {"jet": jet, "height": height}
        self.send_frame(frame)
        return dict(self.held)

    def output_frame(self, normal_frame):
        """Return a held jet-test frame, a blank frame in test mode, or the normal
        live-show frame. The show loop keeps sending on its resend cadence in test
        mode so the watchdog keeps its heartbeat and olad's buffer stays warm."""
        if self._manual_frame is None:
            return dmx.blank_frame() if self.test_mode else normal_frame
        frame = self._manual_frame[:]
        if self.lights_only:
            for channel in dmx.height_channels(self.cfg.jet_count):
                frame[channel - 1] = 0
        return frame
