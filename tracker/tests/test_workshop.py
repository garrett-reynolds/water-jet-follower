"""Mouse Test as a hosted demo: port from PORT, links that work under a path
prefix, and a built folder that cannot reach hardware or power."""

import os
import re
import unittest
from unittest import mock
from urllib.parse import urljoin

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


if __name__ == "__main__":
    unittest.main()
