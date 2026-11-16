"""Mouse Test as a hosted demo: port from PORT, links that work under a path
prefix, and a built folder that cannot reach hardware or power."""

import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from tracker import run


class Server:
    def shutdown(self):
        pass

    def server_close(self):
        pass


def run_mouse_test(argv, env):
    made = []

    def serve_mouse(state, cfg, control=None, mouse_test=None):
        made.append(cfg)
        return Server()

    with mock.patch.dict(os.environ, env, clear=False), \
            mock.patch.object(run.viewer, "serve", serve_mouse), \
            mock.patch.object(run.time, "sleep", side_effect=KeyboardInterrupt):
        run.main(argv)
    return made[0]


class TestMouseTestPort(unittest.TestCase):
    def test_port_comes_from_the_environment(self):
        cfg = run_mouse_test(["mouse-test"], {"PORT": "8761"})
        self.assertEqual(cfg.viewer_port, 8761)

    def test_viewer_port_flag_beats_the_environment(self):
        cfg = run_mouse_test(["--viewer-port", "9001", "mouse-test"], {"PORT": "8761"})
        self.assertEqual(cfg.viewer_port, 9001)


PREFIX = "http://workshop.example/c/water-jet-follower/"


def page_urls(page):
    """Every address a page links to or fetches, as written in the page."""
    return (re.findall(r"""(?:fetch|api)\(\s*'([^']*)'""", page)
            + re.findall(r'href="([^"]*)"', page))


class TestMouseTestUnderAPrefix(unittest.TestCase):
    def test_every_mouse_page_address_stays_under_the_prefix(self):
        from tracker.viewer import MOUSE_PAGE, MOUSE_SETTINGS_PAGE

        for name, page, served_at in (("viewer", MOUSE_PAGE, PREFIX),
                                      ("settings", MOUSE_SETTINGS_PAGE,
                                       PREFIX + "settings")):
            urls = page_urls(page)
            self.assertIn("state", [u.split("?")[0] for u in urls], name)
            for url in urls:
                with self.subTest(page=name, url=url):
                    self.assertTrue(urljoin(served_at, url).startswith(PREFIX),
                                    f"{url} leaves the prefix")

    def test_links_between_mouse_pages_reach_each_other(self):
        from tracker.viewer import MOUSE_PAGE, MOUSE_SETTINGS_PAGE

        self.assertIn(PREFIX + "settings",
                      [urljoin(PREFIX, u) for u in page_urls(MOUSE_PAGE)])
        self.assertIn(PREFIX, [urljoin(PREFIX + "settings", u)
                               for u in page_urls(MOUSE_SETTINGS_PAGE)])


REPO = Path(__file__).resolve().parents[2]
BUILD = REPO / "deploy" / "workshop" / "build.py"

# Runs Mouse Test from a built folder with every hardware and power path cut:
# the hardware libraries cannot be imported, and any attempt to start a program
# (shutdown, reboot, OLA tools) is logged as BLOCKED and refused.
GUARD = r"""
import builtins, os, runpy, subprocess, sys
sys.path.insert(0, os.getcwd())
BANNED = ("ola", "pyrplidar", "pyrplidar_protocol", "serial", "gpiod", "RPi")
real_import = builtins.__import__
def guarded_import(name, *args, **kwargs):
    if name.split(".")[0] in BANNED:
        print("BLOCKED import " + name, file=sys.stderr, flush=True)
        raise ImportError("blocked: " + name)
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded_import
def refuse(what):
    def call(*args, **kwargs):
        print("BLOCKED " + what + " " + repr(args), file=sys.stderr, flush=True)
        raise PermissionError("blocked: " + what)
    return call
subprocess.Popen = refuse("subprocess")
for name in ("system", "execv", "execve", "execvp", "spawnv", "fork", "kill"):
    if hasattr(os, name):
        setattr(os, name, refuse("os." + name))
sys.argv = ["tracker.run", "mouse-test"]
runpy.run_module("tracker.run", run_name="__main__")
"""


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def files_in(folder):
    return sorted(str(p.relative_to(folder)) for p in Path(folder).rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


class TestWorkshopBuild(unittest.TestCase):
    """The folder the Workshop runs: Mouse Test only, and it sends nothing."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "water-jet-follower"
        subprocess.run([sys.executable, str(BUILD), str(cls.out)], check=True,
                       capture_output=True, text=True)
        cls.port = free_port()
        cls.before = files_in(cls.out)
        cls.proc = subprocess.Popen(
            [sys.executable, "-I", "-c", GUARD], cwd=cls.out,
            env=dict(os.environ, PORT=str(cls.port)),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        cls.base = f"http://127.0.0.1:{cls.port}"
        deadline = time.monotonic() + 15
        while True:
            try:
                urlopen(cls.base + "/state", timeout=1).close()
                break
            except OSError:
                if cls.proc.poll() is not None or time.monotonic() > deadline:
                    cls.proc.kill()
                    out, err = cls.proc.communicate()
                    cls.tmp.cleanup()
                    raise RuntimeError("Mouse Test did not start:\n" + out + err)
                time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        if cls.proc.returncode is None:
            cls.proc.kill()
            cls.proc.communicate()
        cls.tmp.cleanup()

    def request(self, path, method="GET", body=None):
        data = None if body is None else json.dumps(body).encode()
        req = Request(self.base + path, data=data, method=method,
                      headers={"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=5) as response:
                return response.status, response.read().decode()
        except HTTPError as exc:
            return exc.code, exc.read().decode()

    def test_built_folder_has_no_system_page_code_and_no_tests(self):
        names = files_in(self.out)
        self.assertIn(os.path.join("tracker", "run.py"), names)
        for gone in ("system.py", "lidar.py", "heartbeat.py"):
            self.assertNotIn(os.path.join("tracker", gone), names)
        self.assertFalse(any("tests" in n for n in names), names)

    def test_viewer_and_settings_pages_are_served(self):
        for path in ("/", "/settings", "/settings-data", "/state", "/config"):
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 200)

    def test_no_page_can_reboot_shut_down_or_send_to_hardware(self):
        for path in ("/system", "/system-data", "/test"):
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)
        for action, body in (("reboot", {}), ("shutdown", {}),
                             ("test-jet", {"jet": 0, "height": 10}),
                             ("all-off", {}), ("test-mode", {"enabled": True}),
                             ("lights-only", {"enabled": True})):
            with self.subTest(action=action):
                self.assertEqual(
                    self.request("/actions/" + action, "POST", body)[0], 404)

    def test_settings_and_mouse_work_and_touch_nothing(self):
        profile = json.loads(self.request("/settings-data")[1])["profile"]
        for path, body in (("/settings/apply", {"profile": profile}),
                           ("/settings/undo", {}), ("/settings/reset", {})):
            with self.subTest(path=path):
                self.assertEqual(self.request(path, "POST", body)[0], 200)
        status, reply = self.request("/mouse", "POST", {"x": 1.0, "y": 0.5, "t": 1})
        self.assertEqual(status, 200, reply)
        self.assertEqual(self.request("/mouse", "DELETE")[0], 200)
        # The Settings page wrote no profile and nothing else to disk.
        self.assertEqual(files_in(self.out), self.before)

    def test_zz_nothing_tried_to_reach_hardware_or_power(self):
        # Runs last (alphabetical): stop the server and read what it logged.
        self.proc.kill()
        _, err = self.proc.communicate()
        self.assertNotIn("BLOCKED", err)


if __name__ == "__main__":
    unittest.main()
