"""RPLIDAR A2M8 source.

Wraps pyrplidar 0.1.2 with the two things the bench proved it needs (DECISIONS.md,
2026-09-04): connect with retry, and drain the serial buffer explicitly, because
pyrplidar does not drain on stop() and throws sync errors on the next connect.

Yields whole scans, not points: (timestamp, [(angle_deg, distance_mm), ...]).
"""

import sys
import time

from pyrplidar import PyRPlidar
from pyrplidar_protocol import RPLIDAR_ANS_TYPE

ULTRA_CAPSULED = 0x84   # the answer type Boost mode uses


class LidarError(RuntimeError):
    pass


def _flush(lidar):
    """Drain the serial input buffer. pyrplidar never does this itself."""
    serial_port = getattr(lidar.lidar_serial, "_serial", None)
    if serial_port is not None:
        serial_port.reset_input_buffer()
        serial_port.reset_output_buffer()


class Lidar:
    def __init__(self, cfg):
        self.cfg = cfg
        self.lidar = None
        self.mode_index = None
        self.mode = None
        # every measurement the device emitted, including the zero-distance ones
        self.raw_samples = 0

    # --- connection ------------------------------------------------------

    def connect(self, attempts=5, delay=1.0):
        last_error = None
        for attempt in range(1, attempts + 1):
            try:
                self._connect_once()
                return self
            except Exception as error:          # noqa: BLE001 - retry on anything
                last_error = error
                print(f"lidar: connect attempt {attempt}/{attempts} failed: {error}",
                      file=sys.stderr)
                self.close()
                time.sleep(delay)
        raise LidarError(f"could not connect to {self.cfg.port}: {last_error}")

    def _connect_once(self):
        self.lidar = PyRPlidar()
        self.lidar.connect(port=self.cfg.port, baudrate=self.cfg.baudrate, timeout=3)
        # pyrplidar swallows SerialException and leaves _serial as None.
        if getattr(self.lidar.lidar_serial, "_serial", None) is None:
            raise LidarError(f"serial port {self.cfg.port} did not open")
        _flush(self.lidar)

        health = self.lidar.get_health()
        if getattr(health, "status", 0) != 0:
            raise LidarError(f"device health status {health.status}")

        self._pick_mode()

    def _pick_mode(self):
        modes = self.lidar.get_scan_modes()
        boost = [i for i, m in enumerate(modes) if m.ans_type == ULTRA_CAPSULED]
        if not boost:
            names = ", ".join(f"{m.name}({RPLIDAR_ANS_TYPE.get(m.ans_type)})" for m in modes)
            if self.cfg.require_boost:
                raise LidarError(f"no ULTRA_CAPSULED (Boost) mode; device offers: {names}")
            boost = [len(modes) - 1]
        self.mode_index = boost[-1]
        self.mode = modes[self.mode_index]
        samples_per_sec = 1_000_000.0 / (self.mode.us_per_sample / 256.0)
        print(f"lidar: mode {self.mode_index} '{self.mode.name}' "
              f"~{samples_per_sec:,.0f} samples/s")

    def close(self):
        if self.lidar is None:
            return
        try:
            self.lidar.stop()
            self.lidar.set_motor_pwm(0)
            time.sleep(0.5)
            _flush(self.lidar)
            self.lidar.disconnect()
        except Exception as error:              # noqa: BLE001 - closing must not raise
            print(f"lidar: error while closing: {error}", file=sys.stderr)
        self.lidar = None

    # --- scanning --------------------------------------------------------

    def scans(self, spin_up=3.0):
        """Yield (timestamp, points) once per revolution.

        timestamp is time.time() at the end of the revolution. points are raw
        (angle_deg, distance_mm) with zero-distance returns already dropped.
        """
        self.lidar.set_motor_pwm(self.cfg.motor_pwm)
        time.sleep(spin_up)
        generator = self.lidar.start_scan_express(self.mode_index)

        points = []
        raw = 0
        for measurement in generator():
            raw += 1
            if measurement.start_flag and points:
                self.raw_samples += raw
                raw = 0
                yield time.time(), points
                points = []
            if measurement.distance > 0:
                points.append((measurement.angle, measurement.distance))


def health_check(cfg, seconds=5.0):
    """Spin for a few seconds and report scan rate. Verifies Boost is really live."""
    lidar = Lidar(cfg).connect()
    try:
        info = lidar.lidar.get_info()
        print(f"lidar: model {info.model} firmware {info.firmware_major}."
              f"{info.firmware_minor} hardware {info.hardware}")
        # The clock starts on the first scan, so the motor spin-up is not counted.
        started = None
        raw_at_start = 0
        scans = valid = 0
        for _, points in lidar.scans():
            if started is None:
                started = time.time()
                raw_at_start = lidar.raw_samples
                continue
            scans += 1
            valid += len(points)
            if time.time() - started >= seconds:
                break
        elapsed = time.time() - started
        raw = lidar.raw_samples - raw_at_start
        hz = scans / elapsed
        raw_per_scan = raw / scans if scans else 0
        print(f"lidar: {hz:.2f} Hz, {raw / elapsed:,.0f} samples/s, "
              f"{raw_per_scan:.0f} samples/scan "
              f"({360.0 / raw_per_scan if raw_per_scan else 0:.3f} deg), "
              f"{valid / scans if scans else 0:.0f} of them with a target")
        if raw_per_scan < 400:
            print("lidar: WARNING under 400 samples/scan - this is not Boost mode",
                  file=sys.stderr)
        return hz, raw_per_scan
    finally:
        lidar.close()
