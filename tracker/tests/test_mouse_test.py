"""The local mouse viewer uses the real map and Wave with no output sender."""

import json
import shutil
import subprocess
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest import mock

from tracker import run
from tracker.config import Config
from tracker.viewer import State, make_handler, serve


class TestMouseTestHTTP(unittest.TestCase):
    def setUp(self):
        from tracker.mouse_test import MouseTest

        self.cfg = Config(viewer_host="127.0.0.1", viewer_port=0,
                          roi_x_min=-1, roi_x_max=2,
                          roi_y_min=-1, roi_y_max=1,
                          strip_start=(0, 0), strip_end=(1, 0),
                          strip_points=((0, 0), (1, 0)), jet_count=2,
                          lead_seconds=0, colour_tau=0, fast_speed=2,
                          hill_jets=3, idle_water_animation="off",
                          idle_colour_animation="off")
        self.now = [0.0]
        self.state = State()
        self.server = serve(self.state, self.cfg,
                            mouse_test=MouseTest(self.cfg, self.state,
                                                 clock=lambda: self.now[0]))
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def post(self, x, y, t):
        body = json.dumps({"x": x, "y": y, "t": t}).encode()
        with urlopen(Request(self.base + "/mouse", data=body,
                             headers={"Content-Type": "application/json"})) as response:
            return json.load(response)

    def state_frame(self):
        with urlopen(self.base + "/state") as response:
            return json.load(response)

    def test_two_moves_change_one_walker_and_real_preview(self):
        first = self.state_frame()
        self.assertEqual(first["tracks"], [])
        self.assertEqual(first["heights"], [0, 0])
        self.assertEqual(first["pixel_colours"], [[0, 0, 40, 0]] * 2)
        self.post(0, 0, 1)
        self.post(1, 0, 2)
        frame = self.state_frame()
        self.assertEqual(len(frame["tracks"]), 1)
        walker = frame["tracks"][0]
        self.assertEqual((walker["x"], walker["y"]), (1, 0))
        self.assertEqual((walker["vx"], walker["vy"], walker["speed"]), (1, 0, 1))
        self.assertEqual((walker["s"], walker["jet_position"], walker["jet"]),
                         (1, 1, 1))
        self.assertTrue(walker["confirmed"])
        self.assertEqual(frame["heights"], [8, 30])
        self.assertEqual(frame["pixel_colours"],
                         [[32, 32, 94, 32], [128, 128, 255, 128]])

    def test_disabled_jet_stays_off_in_output_preview(self):
        self.cfg.jet_enabled = (False, True)
        self.post(1, 0, 1)
        frame = self.state_frame()
        self.assertEqual(frame["heights"], [0, 30])
        self.assertEqual(frame["pixel_colours"],
                         [[0, 0, 0, 0], [0, 0, 255, 0]])

    def test_clear_removes_walker_and_restores_no_walker_preview(self):
        self.post(0, 0, 1)
        with urlopen(Request(self.base + "/mouse", method="DELETE")) as response:
            self.assertEqual(json.load(response), {"cleared": True})
        frame = self.state_frame()
        self.assertEqual(frame["tracks"], [])
        self.assertEqual(frame["heights"], [0, 0])
        self.assertEqual(frame["pixel_colours"], [[0, 0, 40, 0]] * 2)
        for name in ("fg", "bg", "legs", "clusters", "detections"):
            self.assertEqual(frame[name], [])

    def test_move_outside_active_area_clears_walker(self):
        self.post(0, 0, 1)
        result = self.post(2.1, 0, 2)  # inside map pad; outside active area
        self.assertIsNone(result["track"])
        frame = self.state_frame()
        self.assertEqual(frame["tracks"], [])
        self.assertEqual(frame["heights"], [0, 0])
        self.assertEqual(frame["pixel_colours"], [[0, 0, 40, 0]] * 2)
        self.post(1, 0, 3)
        self.assertEqual(self.state_frame()["tracks"][0]["speed"], 0)

    def test_mouse_input_requires_a_json_object(self):
        for payload in (b"[]", b"null"):
            with self.subTest(payload=payload):
                request = Request(self.base + "/mouse", data=payload,
                                  headers={"Content-Type": "application/json"})
                with self.assertRaises(HTTPError) as raised:
                    urlopen(request)
                self.assertEqual(raised.exception.code, 400)
                self.assertIn("JSON object", json.load(raised.exception)["error"])

    def test_normal_viewer_has_no_mouse_input(self):
        state = State()
        server = serve(state, self.cfg)
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with self.assertRaises(HTTPError) as raised:
                urlopen(Request(base + "/mouse", data=b'{"x":0,"y":0,"t":1}'))
            self.assertEqual(raised.exception.code, 404)
            with urlopen(base + "/") as response:
                page = response.read().decode()
            self.assertNotIn("MOUSE TEST", page)
            self.assertNotIn("/mouse", page)
        finally:
            server.shutdown()
            server.server_close()

    def test_mouse_page_has_no_hardware_controls(self):
        with urlopen(self.base + "/") as response:
            page = response.read().decode()
        self.assertIn("MOUSE TEST", page)
        self.assertNotIn('href="/test"', page)
        self.assertNotIn('href="/settings"', page)
        self.assertNotIn('href="/system"', page)
        for path in ("/test", "/settings", "/system"):
            with self.assertRaises(HTTPError) as raised:
                urlopen(self.base + path)
            self.assertEqual(raised.exception.code, 404)


class TestMouseTestPreviewClock(unittest.TestCase):
    def setUp(self):
        from tracker.mouse_test import MouseTest

        self.now = [0.0]
        self.cfg = Config(viewer_host="127.0.0.1", viewer_port=0,
                          roi_x_min=-1, roi_x_max=2,
                          roi_y_min=-1, roi_y_max=1,
                          strip_start=(0, 0), strip_end=(1, 0),
                          strip_points=((0, 0), (1, 0)), jet_count=2,
                          lead_seconds=1, follow_response=0,
                          colour_tau=0, fast_speed=1, hill_jets=3)
        self.state = State()
        self.mouse = MouseTest(self.cfg, self.state, clock=lambda: self.now[0])
        self.server = serve(self.state, self.cfg, mouse_test=self.mouse)
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def wait_for_time(self, timestamp):
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            frame = self.state.get()
            if frame["t"] == timestamp:
                return frame
            time.sleep(0.01)
        self.fail(f"preview did not advance to {timestamp}")

    def post(self, x, y, timestamp):
        data = json.dumps({"x": x, "y": y, "t": timestamp}).encode()
        with urlopen(Request(self.base + "/mouse", data=data)) as response:
            return json.load(response)

    def test_resting_pointer_stops_speed_and_updates_lead_and_colour(self):
        self.post(0, 0, 1)
        self.post(0.5, 0, 2)
        moving = self.state.get()
        self.assertEqual(moving["tracks"][0]["speed"], 0.5)
        self.assertEqual(moving["heights"], [8, 30])
        self.assertGreater(moving["pixel_colours"][1][0], 0)

        self.now[0] = 0.2
        resting = self.wait_for_time(0.2)
        self.assertEqual((resting["tracks"][0]["x"], resting["tracks"][0]["y"]),
                         (0.5, 0))
        self.assertEqual((resting["tracks"][0]["vx"], resting["tracks"][0]["vy"],
                          resting["tracks"][0]["speed"]), (0, 0, 0))
        self.assertGreater(resting["heights"][0], moving["heights"][0])
        self.assertLess(resting["heights"][1], moving["heights"][1])
        self.assertEqual(resting["pixel_colours"][1][0], 0)

    def test_idle_wave_keeps_advancing_without_a_walker(self):
        self.cfg.idle_water_animation = "pulse"
        self.cfg.idle_colour_animation = "fade"
        self.cfg.idle_brightness = 255
        self.cfg.idle_seconds = 4
        self.post(0, 0, 1)
        with urlopen(Request(self.base + "/mouse", method="DELETE")) as response:
            self.assertTrue(json.load(response)["cleared"])
        self.now[0] = 1.0
        first = self.wait_for_time(1.0)
        self.now[0] = 2.0
        second = self.wait_for_time(2.0)
        self.assertEqual(first["tracks"], [])
        self.assertEqual(second["tracks"], [])
        self.assertEqual(first["heights"], [7, 7])
        self.assertEqual(second["heights"], [15, 15])
        self.assertEqual(first["pixel_colours"], [[0, 0, 127, 0]] * 2)
        self.assertEqual(second["pixel_colours"], [[0, 0, 255, 0]] * 2)


class TestMouseTestCommand(unittest.TestCase):
    def test_direct_mouse_server_binds_only_to_loopback(self):
        from tracker.mouse_test import MouseTest

        cfg = Config(viewer_host="0.0.0.0", viewer_port=0)
        state = State()
        server = serve(state, cfg, mouse_test=MouseTest(cfg, state))
        try:
            self.assertEqual(server.server_address[0], "127.0.0.1")
        finally:
            server.shutdown()
            server.server_close()

    def test_mouse_handler_rejects_show_control(self):
        from tracker.mouse_test import MouseTest

        cfg = Config()
        state = State()
        with self.assertRaises(ValueError):
            make_handler(state, cfg, control=object(),
                         mouse_test=MouseTest(cfg, state))

    def test_command_opens_local_viewer_without_output_sender(self):
        made = []

        class Server:
            def shutdown(self):
                pass

            def server_close(self):
                pass

        def serve_mouse(state, cfg, control=None, mouse_test=None):
            made.append((state, cfg, control, mouse_test))
            return Server()

        with mock.patch.object(run.viewer, "serve", serve_mouse), \
                mock.patch.object(run, "_lidar_source", side_effect=AssertionError("LiDAR")), \
                mock.patch.object(run.time, "sleep", side_effect=KeyboardInterrupt), \
                mock.patch("tracker.dmx.send", side_effect=AssertionError("DMX")):
            self.assertEqual(run.main(["mouse-test"]), 0)
        self.assertEqual(len(made), 1)
        _, cfg, control, mouse_test = made[0]
        self.assertEqual(cfg.viewer_host, "127.0.0.1")
        self.assertIsNone(control)
        self.assertIsNotNone(mouse_test)


class TestMouseTestBrowser(unittest.TestCase):
    def test_rapid_move_sends_latest_and_leave_cancels_queued_move(self):
        if not shutil.which("node"):
            self.skipTest("Node.js is needed for browser behavior")
        from tracker.viewer import MOUSE_PAGE

        script = MOUSE_PAGE.split("<script>", 1)[1].split("</script>", 1)[0]
        browser = r"""
const vm=require('node:vm');
const script=process.argv[2].replace(/fit\(\); poll\(\);\s*$/, '');
let now=1000, nextTimer=1;
const calls=[],handlers={},timers=new Map();
const canvas={width:800,height:600,addEventListener:(name,fn)=>handlers[name]=fn,
  getBoundingClientRect:()=>({left:10,top:20,width:800,height:600})};
const context=vm.createContext({document:{getElementById:()=>canvas},
  window:{addEventListener(){}},performance:{timeOrigin:1000000,now:()=>now},
  setTimeout(fn,delay){const id=nextTimer++;timers.set(id,{fn,delay});return id},
  clearTimeout(id){timers.delete(id)},
  fetch:async(path,options)=>{calls.push({path,method:options.method,
    body:options.body&&JSON.parse(options.body)});return {ok:true}}});
vm.runInContext(script,context);
vm.runInContext('CFG={roi_x_min:0,roi_x_max:2,roi_y_min:0,roi_y_max:2}',context);
const t=vm.runInContext('transform(document.getElementById("c"))',context);
function move(x){handlers.pointermove({clientX:10+t.sx(x),clientY:20+t.sy(0.5)})}
(async()=>{
  move(0.5);
  now=1020;move(2.1);
  const queued=timers.size;
  now=1050;
  for(const [id,timer] of [...timers]){timers.delete(id);timer.fn()}
  await vm.runInContext('mousePending',context);
  const afterFlush=calls.slice();
  now=1060;move(1.5);
  const queuedBeforeLeave=timers.size;
  handlers.pointerleave();
  const timersAfterLeave=timers.size;
  now=1110;
  for(const [id,timer] of [...timers]){timers.delete(id);timer.fn()}
  await vm.runInContext('mousePending',context);
  console.log(JSON.stringify({queued,afterFlush,queuedBeforeLeave,
    timersAfterLeave,calls}));
})().catch(e=>{console.error(e);process.exitCode=1});
"""
        result = subprocess.run(["node", "-", script], input=browser,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        seen = json.loads(result.stdout)
        self.assertEqual(seen["queued"], 1)
        self.assertEqual([call["method"] for call in seen["afterFlush"]],
                         ["POST", "POST"])
        self.assertAlmostEqual(seen["afterFlush"][1]["body"]["x"], 2.1)
        self.assertEqual(seen["queuedBeforeLeave"], 1)
        self.assertEqual(seen["timersAfterLeave"], 0)
        self.assertEqual([call["method"] for call in seen["calls"]],
                         ["POST", "POST", "DELETE"])

    def test_pointer_maps_world_moves_at_bounded_rate_and_leaves(self):
        if not shutil.which("node"):
            self.skipTest("Node.js is needed for browser behavior")
        from tracker.viewer import MOUSE_PAGE

        script = MOUSE_PAGE.split("<script>", 1)[1].split("</script>", 1)[0]
        browser = r"""
const vm=require('node:vm');
const script=process.argv[2].replace(/fit\(\); poll\(\);\s*$/, '');
const calls=[],handlers={};
const canvas={width:800,height:600,addEventListener:(name,fn)=>handlers[name]=fn,
  getBoundingClientRect:()=>({left:10,top:20,width:800,height:600})};
const nodes={'c':canvas,'mouse-mode':{textContent:'MOUSE TEST'}};
const context=vm.createContext({document:{getElementById:id=>nodes[id]},
  window:{innerWidth:800,innerHeight:600,addEventListener(){}},
  performance:{timeOrigin:1000000,now:()=>1000},
  setTimeout:()=>1,clearTimeout(){},
  fetch:async(path,options)=>{calls.push({path,method:options.method,
    body:options.body&&JSON.parse(options.body)});return {ok:true}}});
vm.runInContext(script,context);
vm.runInContext(`CFG={roi_x_min:0,roi_x_max:2,roi_y_min:0,roi_y_max:2};`,context);
(async()=>{
  const t=vm.runInContext('transform(document.getElementById("c"))',context);
  const event={clientX:10+t.sx(1.5),clientY:20+t.sy(0.5)};
  handlers.pointermove(event);
  handlers.pointermove(event);
  handlers.pointerleave();
  await vm.runInContext('mousePending',context);
  console.log(JSON.stringify({calls,mark:nodes['mouse-mode'].textContent}));
})().catch(e=>{console.error(e);process.exitCode=1});
"""
        result = subprocess.run(["node", "-", script], input=browser,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        seen = json.loads(result.stdout)
        self.assertEqual(seen["mark"], "MOUSE TEST")
        self.assertEqual(len(seen["calls"]), 2)
        self.assertEqual(seen["calls"][0]["path"], "/mouse")
        self.assertEqual(seen["calls"][0]["method"], "POST")
        self.assertAlmostEqual(seen["calls"][0]["body"]["x"], 1.5)
        self.assertAlmostEqual(seen["calls"][0]["body"]["y"], 0.5)
        self.assertEqual(seen["calls"][0]["body"]["t"], 1001)
        self.assertEqual(seen["calls"][1], {"path": "/mouse", "method": "DELETE"})
