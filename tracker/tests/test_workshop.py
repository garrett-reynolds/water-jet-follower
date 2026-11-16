"""Mouse Test as a hosted demo: port from PORT, links that work under a path
prefix, and a built folder that cannot reach hardware or power."""

import os
import unittest
from unittest import mock

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


if __name__ == "__main__":
    unittest.main()
