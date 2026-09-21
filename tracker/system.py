"""What the Pi is doing, for the System page.

Standard library only, read from /proc and /sys where the Pi keeps them. Every
reader returns None when its file is missing, so the same page serves on the
laptop during a dry run without pretending the laptop is a Pi.
"""

import os
import platform
import shutil
import socket
import subprocess
import time

# When this process started. The show imports the viewer at start-up, so this is
# close enough to "show running since".
STARTED = time.time()


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read().strip("\x00\n ")
    except OSError:
        return None


def _model():
    return _read("/proc/device-tree/model")


def _os_name():
    text = _read("/etc/os-release") or ""
    for line in text.splitlines():
        if line.startswith("PRETTY_NAME="):
            return line.split("=", 1)[1].strip('"')
    return platform.platform()


def _uptime_seconds():
    text = _read("/proc/uptime")
    return float(text.split()[0]) if text else None


def _load():
    text = _read("/proc/loadavg")
    return [float(v) for v in text.split()[:3]] if text else None


def _memory():
    """Used and total in MiB, the way `free` counts it (total minus available)."""
    text = _read("/proc/meminfo")
    if not text:
        return None
    values = {}
    for line in text.splitlines():
        key, _, rest = line.partition(":")
        values[key] = int(rest.split()[0])          # kB
    total = values.get("MemTotal")
    available = values.get("MemAvailable")
    if total is None or available is None:
        return None
    return {"used_mib": (total - available) // 1024, "total_mib": total // 1024}


def _disk():
    usage = shutil.disk_usage(os.path.expanduser("~"))
    return {"used_gib": round(usage.used / 2 ** 30, 1),
            "total_gib": round(usage.total / 2 ** 30, 1)}


def _cpu_temperature():
    text = _read("/sys/class/thermal/thermal_zone0/temp")
    return round(int(text) / 1000, 1) if text else None


def _throttled():
    """The Pi firmware's throttle flags: under-voltage and thermal, now and ever.
    None where there is no vcgencmd (the laptop)."""
    try:
        result = subprocess.run(["vcgencmd", "get_throttled"], capture_output=True,
                                text=True, timeout=3)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0 or "=" not in result.stdout:
        return None
    flags = int(result.stdout.split("=", 1)[1], 16)
    return {
        "under_voltage_now": bool(flags & 0x1),
        "throttled_now": bool(flags & 0x4),
        "under_voltage_ever": bool(flags & 0x10000),
        "throttled_ever": bool(flags & 0x40000),
    }


def _addresses():
    """Every non-loopback IPv4 address the Pi answers on. `ip` is on every Pi;
    the socket fallback covers the laptop."""
    try:
        result = subprocess.run(["ip", "-4", "-o", "addr"], capture_output=True,
                                text=True, timeout=3)
        found = []
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) > 3 and parts[1] != "lo":
                found.append(f"{parts[3].split('/')[0]} ({parts[1]})")
        if found:
            return found
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        return [socket.gethostbyname(socket.gethostname())]
    except OSError:
        return []


def _olad_active():
    try:
        result = subprocess.run(["systemctl", "is-active", "olad"], capture_output=True,
                                text=True, timeout=3)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() == "active"


def snapshot(state, control):
    """Everything the System page shows, in one dict."""
    frame = state.get()
    return {
        "pi": {
            "hostname": socket.gethostname(),
            "model": _model(),
            "os": _os_name(),
            "kernel": platform.release(),
            "addresses": _addresses(),
            "clock": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "uptime_seconds": _uptime_seconds(),
        },
        "health": {
            "cpu_temp_c": _cpu_temperature(),
            "throttled": _throttled(),
            "load": _load(),
            "memory": _memory(),
            "disk": _disk(),
        },
        "show": {
            "pid": os.getpid(),
            "python": platform.python_version(),
            "running_seconds": round(time.time() - STARTED),
            "lights_only": control.lights_only,
            "test_mode": control.test_mode,
            "lidar_ok": frame.get("lidar_ok", True),
            "scan_hz": round(frame.get("hz", 0.0), 2),
            "source": frame.get("source"),
            "olad_active": _olad_active(),
            "power_available": control.zero_output is not None
            and control.run_command is not None,
        },
    }
