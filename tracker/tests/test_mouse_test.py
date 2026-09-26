"""The local mouse viewer uses the real map and Wave with no output sender."""

import json
import shutil
import subprocess
import time
import unittest
from html.parser import HTMLParser
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
        # Break caught: the start page gives no way to open the safe Settings map.
        self.assertIn('href="/settings"', page)
        self.assertNotIn('href="/system"', page)
        for path in ("/test", "/system"):
            with self.assertRaises(HTTPError) as raised:
                urlopen(self.base + path)
            self.assertEqual(raised.exception.code, 404)

    def test_settings_edit_changes_the_next_real_wave_preview(self):
        # Break caught: Mouse Test blocks Settings or applies edits to a copy
        # that the real Wave never reads.
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode()
        self.assertIn("MOUSE TEST", page)
        with urlopen(self.base + "/settings-data") as response:
            profile = json.load(response)["profile"]
        profile["settings"]["jet_enabled"] = [False, True]
        body = json.dumps({"profile": profile}).encode()
        with urlopen(Request(self.base + "/settings/apply", data=body,
                             headers={"Content-Type": "application/json"})) as response:
            self.assertEqual(json.load(response)["settings"]["jet_enabled"],
                             [False, True])
        self.post(1, 0, 1)
        frame = self.state_frame()
        self.assertEqual(frame["heights"], [0, 30])
        self.assertEqual(frame["pixel_colours"],
                         [[0, 0, 0, 0], [0, 0, 255, 0]])

    def test_shrinking_active_area_clears_the_existing_walker(self):
        # Break caught: an old Walker keeps the Wave active after Settings
        # moves the active-area edge past it.
        self.post(1.5, 0, 1)
        self.assertEqual(len(self.state_frame()["tracks"]), 1)
        with urlopen(self.base + "/settings-data") as response:
            profile = json.load(response)["profile"]
        profile["settings"]["roi_x_max"] = 1.2
        body = json.dumps({"profile": profile}).encode()
        with urlopen(Request(self.base + "/settings/apply", data=body)):
            pass
        frame = self.state_frame()
        self.assertEqual(frame["tracks"], [])
        self.assertEqual(frame["heights"], [0, 0])

    def test_settings_rejects_a_non_boolean_safety_unlock(self):
        # Break caught: malformed input opens the hard height limit.
        with urlopen(self.base + "/settings-data") as response:
            profile = json.load(response)["profile"]
        profile["settings"]["height_max"] = 31
        body = json.dumps({"profile": profile,
                           "unlock_height_max": "yes"}).encode()
        with self.assertRaises(HTTPError) as raised:
            urlopen(Request(self.base + "/settings/apply", data=body))
        self.assertEqual(raised.exception.code, 400)
        with urlopen(self.base + "/settings-data") as response:
            saved = json.load(response)["profile"]
        self.assertEqual(saved["settings"]["height_max"], 40)

    def test_settings_page_hides_hardware_actions_and_server_refuses_them(self):
        # Break caught: the local preview offers a live hardware control.
        class Controls(HTMLParser):
            def __init__(self):
                super().__init__()
                self.buttons = {}
                self.links = []

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "button" and "id" in attrs:
                    self.buttons[attrs["id"]] = attrs
                if tag == "a":
                    self.links.append(attrs.get("href"))

        with urlopen(self.base + "/settings") as response:
            page = response.read().decode()
        controls = Controls()
        controls.feed(page)
        self.assertIn("MOUSE TEST", page)
        for action in ("lights", "all-off"):
            self.assertIn("hidden", controls.buttons[action])
            self.assertIn("disabled", controls.buttons[action])
        self.assertNotIn("/test", controls.links)
        self.assertNotIn("/system", controls.links)
        for action in ("/actions/test-mode", "/actions/test-jet",
                       "/actions/all-off", "/actions/lights-only",
                       "/actions/reboot", "/actions/shutdown"):
            with self.subTest(action=action):
                with self.assertRaises(HTTPError) as raised:
                    urlopen(Request(self.base + action, data=b"{}"))
                self.assertEqual(raised.exception.code, 404)

    def test_settings_map_hover_pauses_for_edits_and_clears_on_leave(self):
        # Break caught: Settings hover sends no Walker, or an edit drag sends
        # Walker moves, or a leave lets a queued move restore that Walker.
        if not shutil.which("node"):
            self.skipTest("Node.js is needed for browser behavior")
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode()
        script = page.split("<script>", 1)[1].split("</script>", 1)[0]
        browser = r"""
const vm=require('node:vm');
const script=process.argv[2].replace(/init\(\);pollState\(\);\s*$/, '');
const calls=[],listeners={},timers=new Map(),nodes={};
let now=1000,nextTimer=1;
const canvas={width:800,height:600,
  getBoundingClientRect:()=>({left:10,top:20,width:800,height:600}),
  setPointerCapture(){},addEventListener:(name,fn)=>listeners[name]=fn};
nodes.path=canvas;
const element=id=>nodes[id]||(nodes[id]={value:'',hidden:false,
  addEventListener(){},classList:{toggle(){}}});
const context=vm.createContext({
  document:{getElementById:element,querySelector:()=>({addEventListener(){}}),
    querySelectorAll:()=>[]},window:{},devicePixelRatio:1,
  performance:{timeOrigin:1000000,now:()=>now},
  setTimeout(fn,delay){const id=nextTimer++;timers.set(id,{fn,delay});return id},
  clearTimeout(id){timers.delete(id)},
  fetch:async(path,options)=>{calls.push({path,method:options.method,
    body:options.body&&JSON.parse(options.body)});return {ok:true}}
});
vm.runInContext(script,context);
vm.runInContext(`profile={settings:{strip_points:[[0,0],[1,0]],jet_count:2,
  roi_x_min:-1,roi_x_max:2,roi_y_min:-1,roi_y_max:1}};
  roi={xmin:-2,xmax:3,ymin:-2,ymax:2};draw=()=>{};dirty=()=>{};`,context);
const xy=(x,y)=>vm.runInContext(`xy([${x},${y}])`,context);
function emit(name,x,y){const e={clientX:10+x,clientY:20+y,pointerId:1};
  canvas['on'+name]?.(e);listeners[name]?.(e)}
async function drain(){await vm.runInContext(
  'typeof mousePending === "undefined" ? Promise.resolve() : mousePending',context)}
(async()=>{
  let [x,y]=xy(0.5,0.5);emit('pointermove',x,y);await drain();
  const hover=calls.slice();
  now=1100;[x,y]=xy(0,0);emit('pointerdown',x,y);
  [x,y]=xy(0.3,0);emit('pointermove',x,y);await drain();
  const duringJet=calls.slice();
  const editedPoint=vm.runInContext('profile.settings.strip_points[0]',context);
  emit('pointerup',x,y);
  now=1200;[x,y]=xy(0.6,0.4);emit('pointermove',x,y);await drain();
  const afterJet=calls.slice();
  now=1300;[x,y]=xy(-1,-1);emit('pointerdown',x,y);
  [x,y]=xy(-1.2,-1.1);emit('pointermove',x,y);await drain();
  const duringCorner=calls.slice();
  const editedArea=vm.runInContext(
    '[profile.settings.roi_x_min,profile.settings.roi_y_min]',context);
  emit('pointerup',x,y);
  now=1400;[x,y]=xy(0.7,0.4);emit('pointermove',x,y);
  now=1410;[x,y]=xy(0.8,0.4);emit('pointermove',x,y);
  const queued=timers.size;
  emit('pointerleave',x,y);
  now=1500;for(const [id,timer] of [...timers]){timers.delete(id);timer.fn()}
  await drain();
  console.log(JSON.stringify({hover,duringJet,editedPoint,afterJet,
    duringCorner,editedArea,queued,calls}));
})().catch(e=>{console.error(e);process.exitCode=1});
"""
        result = subprocess.run(["node", "-", script], input=browser,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        seen = json.loads(result.stdout)
        self.assertEqual([call["method"] for call in seen["hover"]], ["POST"])
        self.assertEqual(seen["hover"][0]["path"], "/mouse")
        self.assertAlmostEqual(seen["hover"][0]["body"]["x"], 0.5)
        self.assertAlmostEqual(seen["hover"][0]["body"]["y"], 0.5)
        self.assertEqual([call["method"] for call in seen["duringJet"]],
                         ["POST", "DELETE"])
        self.assertAlmostEqual(seen["editedPoint"][0], 0.3)
        self.assertEqual([call["method"] for call in seen["afterJet"]],
                         ["POST", "DELETE", "POST"])
        self.assertEqual([call["method"] for call in seen["duringCorner"]],
                         ["POST", "DELETE", "POST", "DELETE"])
        self.assertEqual(seen["editedArea"], [-1.2, -1.1])
        self.assertEqual([call["method"] for call in seen["calls"]],
                         ["POST", "DELETE", "POST", "DELETE", "POST", "POST",
                          "DELETE"])
        self.assertAlmostEqual(seen["calls"][-3]["body"]["x"], 0.7)
        self.assertAlmostEqual(seen["calls"][-2]["body"]["x"], 0.8)

    def test_settings_drag_cancel_restores_hover_for_point_and_corner(self):
        # Break caught: pointercancel leaves either drag flag set, so later
        # hover moves cannot reach the Walker.
        if not shutil.which("node"):
            self.skipTest("Node.js is needed for browser behavior")
        with urlopen(self.base + "/settings") as response:
            page = response.read().decode()
        script = page.split("<script>", 1)[1].split("</script>", 1)[0]
        browser = r"""
const vm=require('node:vm');
const script=process.argv[2].replace(/init\(\);pollState\(\);\s*$/, '');
async function run(kind){
  const calls=[],listeners={},nodes={};
  let now=1000;
  const canvas={width:800,height:600,
    getBoundingClientRect:()=>({left:10,top:20,width:800,height:600}),
    setPointerCapture(){},addEventListener:(name,fn)=>listeners[name]=fn};
  nodes.path=canvas;
  const element=id=>nodes[id]||(nodes[id]={value:'',hidden:false,
    addEventListener(){},classList:{toggle(){}}});
  const context=vm.createContext({
    document:{getElementById:element,querySelector:()=>({addEventListener(){}}),
      querySelectorAll:()=>[]},window:{},devicePixelRatio:1,
    performance:{timeOrigin:1000000,now:()=>now},
    setTimeout:()=>1,clearTimeout(){},
    fetch:async(path,options)=>{calls.push({path,method:options.method,
      body:options.body&&JSON.parse(options.body)});return {ok:true}}
  });
  vm.runInContext(script,context);
  vm.runInContext(`profile={settings:{strip_points:[[0,0],[1,0]],jet_count:2,
    roi_x_min:-1,roi_x_max:2,roi_y_min:-1,roi_y_max:1}};
    roi={xmin:-2,xmax:3,ymin:-2,ymax:2};draw=()=>{};dirty=()=>{};`,context);
  const xy=(x,y)=>vm.runInContext(`xy([${x},${y}])`,context);
  function emit(name,x,y){const e={clientX:10+x,clientY:20+y,pointerId:1};
    canvas['on'+name]?.(e);listeners[name]?.(e)}
  let [x,y]=xy(0.5,0.5);emit('pointermove',x,y);
  [x,y]=kind==='point'?xy(0,0):xy(-1,-1);
  emit('pointerdown',x,y);emit('pointercancel',x,y);
  now=1100;[x,y]=xy(0.5,0.5);emit('pointermove',x,y);
  await vm.runInContext('mousePending',context);
  return {kind,calls,state:vm.runInContext('[dragging,dragCorner]',context)};
}
(async()=>console.log(JSON.stringify(await Promise.all([
  run('point'),run('corner')]))))().catch(e=>{console.error(e);process.exitCode=1});
"""
        result = subprocess.run(["node", "-", script], input=browser,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        for seen in json.loads(result.stdout):
            with self.subTest(kind=seen["kind"]):
                self.assertEqual(seen["state"], [False, None])
                self.assertEqual([call["method"] for call in seen["calls"]],
                                 ["POST", "DELETE", "POST"])


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
    def test_fast_out_and_back_preserves_every_move_before_leave(self):
        # Break caught: a newer move replaces an older pending move, so a
        # fast trip out and back never reaches the real Wave.
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
  now=1010;move(2.1);
  now=1020;move(0.5);
  handlers.pointerleave();
  now=1100;
  for(const [id,timer] of [...timers]){timers.delete(id);timer.fn()}
  await vm.runInContext('mousePending',context);
  console.log(JSON.stringify({calls}));
})().catch(e=>{console.error(e);process.exitCode=1});
"""
        result = subprocess.run(["node", "-", script], input=browser,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        seen = json.loads(result.stdout)
        self.assertEqual([call["method"] for call in seen["calls"]],
                         ["POST", "POST", "POST", "DELETE"])
        self.assertEqual([round(call["body"]["x"], 1)
                          for call in seen["calls"][:3]], [0.5, 2.1, 0.5])
        self.assertLess(seen["calls"][0]["body"]["t"],
                        seen["calls"][1]["body"]["t"])

    def test_pointer_maps_each_world_move_and_leaves(self):
        # Break caught: rapid repeated moves disappear before they reach /mouse.
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
        self.assertEqual(len(seen["calls"]), 3)
        self.assertEqual(seen["calls"][0]["path"], "/mouse")
        self.assertEqual(seen["calls"][0]["method"], "POST")
        self.assertAlmostEqual(seen["calls"][0]["body"]["x"], 1.5)
        self.assertAlmostEqual(seen["calls"][0]["body"]["y"], 0.5)
        self.assertEqual(seen["calls"][0]["body"]["t"], 1001)
        self.assertEqual(seen["calls"][1]["method"], "POST")
        self.assertLess(seen["calls"][0]["body"]["t"],
                        seen["calls"][1]["body"]["t"])
        self.assertEqual(seen["calls"][2], {"path": "/mouse", "method": "DELETE"})
