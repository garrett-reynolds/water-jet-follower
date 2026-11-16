"""Build the Mouse Test copy that a hosted demo (the Workshop) runs.

    py -3.12 deploy/workshop/build.py build/workshop

Copies only the tracker modules Mouse Test needs into <out>/tracker/. Left out
on purpose: system.py (the System page that reboots or shuts down the host),
lidar.py, heartbeat.py, merge.py and the tests. Standard library only, so the
folder needs no pip install. Run it on the host with:

    /usr/bin/python3 -m tracker.run mouse-test

in <out>, with the port in PORT. Mouse Test sends nothing to any hardware.
"""

import shutil
import sys
from pathlib import Path

MODULES = ("__init__.py", "config.py", "dmx.py", "geometry.py", "mouse_test.py",
           "run.py", "scanfile.py", "settings.py", "tracking.py", "viewer.py",
           "wave.py")


def build(out):
    src = Path(__file__).resolve().parents[2] / "tracker"
    dest = Path(out) / "tracker"
    dest.mkdir(parents=True, exist_ok=True)
    for name in MODULES:
        shutil.copy2(src / name, dest / name)
    return dest


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: build.py <out-folder>")
    print(f"built {build(sys.argv[1])}")
