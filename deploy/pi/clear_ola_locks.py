#!/usr/bin/env python3
"""Remove stale OLA serial lock files before olad starts."""

import os
from pathlib import Path
import re
import stat
import sys


LOCK_NAME = re.compile(r"LCK\.\.ttyUSB.*\Z")
PID_TEXT = re.compile(r"[1-9][0-9]*\Z")


def _read_pid(lock):
    data = lock.read_text(encoding="ascii")
    lines = data.splitlines()
    if len(lines) != 1 or not PID_TEXT.fullmatch(lines[0].strip()):
        raise ValueError(f"invalid PID in {lock}")
    return lines[0].strip()


def _device_is_open(proc_dir, device):
    with os.scandir(proc_dir) as processes:
        for process in processes:
            if not process.name.isdecimal():
                continue
            fd_dir = Path(process.path) / "fd"
            try:
                with os.scandir(fd_dir) as fds:
                    for fd in fds:
                        try:
                            target = os.readlink(fd.path)
                        except FileNotFoundError:
                            continue  # The process closed this descriptor.
                        if target == str(device):
                            return True
            except FileNotFoundError:
                continue  # The process exited while it was checked.
    return False


def clear_locks(lock_dir, proc_dir, dev_dir):
    """Validate every matching lock, then remove the stale locks."""
    stale = []
    with os.scandir(lock_dir) as locks:
        for entry in locks:
            if not LOCK_NAME.fullmatch(entry.name):
                continue
            lock = Path(entry.path)
            mode = entry.stat(follow_symlinks=False).st_mode
            if not stat.S_ISREG(mode):
                raise ValueError(f"not a regular lock file: {lock}")
            _read_pid(lock)
            device = Path(dev_dir) / entry.name.removeprefix("LCK..")
            if _device_is_open(proc_dir, device):
                raise ValueError(f"device is open: {device}")
            stale.append(lock)

    for lock in stale:
        lock.unlink()
        print(f"removed {lock}")


def main(lock_dir=Path("/var/lock"), proc_dir=Path("/proc"), dev_dir=Path("/dev")):
    try:
        clear_locks(lock_dir, proc_dir, dev_dir)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"OLA lock cleanup failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
