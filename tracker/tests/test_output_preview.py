"""The Live map shows the last accepted output command."""

import array
import json
import shutil
import subprocess
import threading
import unittest
from types import SimpleNamespace
from unittest import mock

from tracker import dmx, run, wave
from tracker.config import Config
from tracker.viewer import PAGE, State


class TestOutputState(unittest.TestCase):
    def test_reverse_routing_decodes_to_logical_pixel_order(self):
        cfg = Config(jet_count=2, reverse_jets=True)
        state = State()
        frame = dmx.blank_frame()
        frame[0:5] = array.array("B", [1, 2, 3, 4, 5])
        frame[5:10] = array.array("B", [10, 20, 30, 40, 50])

        state.set_output(frame, (cfg.jet_count, cfg.reverse_jets))
        frame[5:10] = array.array("B", [0, 0, 0, 0, 0])

        self.assertEqual(state.get()["pixel_colours"],
                         [[10, 20, 30, 40], [1, 2, 3, 4]])
        self.assertEqual(state.get()["heights"], [50, 5])


class TestShowOutputPreview(unittest.TestCase):
    def test_profile_edit_during_held_test_build_keeps_one_settings_set(self):
        cfg = Config(jet_count=2, reverse_jets=True)
        building = threading.Event()
        edit_attempted = threading.Event()
        applied = threading.Event()
        pause_blank = threading.Event()
        errors = []
        state = None
        control = None
        editor = None

        class Server:
            def shutdown(self):
                pass

        def serve(live_state, _cfg, live_control):
            nonlocal state, control
            state, control = live_state, live_control
            return Server()

        def source():
            nonlocal editor
            control.set_test_mode(True)
            profile = control.profile()
            profile["settings"]["reverse_jets"] = False
            profile["settings"]["slow_colour"] = [10, 20, 30, 40]

            def edit_profile():
                try:
                    if not building.wait(2):
                        raise TimeoutError("held frame build did not start")
                    edit_attempted.set()
                    control.apply(profile)
                    applied.set()
                except Exception as exc:
                    errors.append(exc)

            editor = threading.Thread(target=edit_profile)
            editor.start()
            pause_blank.set()
            control.test_jet(0, 20)
            yield 1.0, []

        real_blank = dmx.blank_frame

        def paused_blank():
            if pause_blank.is_set() and not building.is_set():
                building.set()
                if not edit_attempted.wait(2):
                    raise TimeoutError("profile edit did not start")
                applied.wait(0.2)
            return real_blank()

        try:
            with mock.patch.object(run.viewer, "serve", serve), \
                    mock.patch.object(dmx, "blank_frame", paused_blank):
                run._show_loop(source(), cfg, None, "test",
                               SimpleNamespace(lights_only=False),
                               lambda _frame: True, lambda: True)
        finally:
            if editor is not None:
                editor.join(2)

        self.assertFalse(editor.is_alive())
        self.assertEqual(errors, [])
        self.assertTrue(applied.is_set())
        self.assertEqual(state.get()["pixel_colours"][0], [0, 0, 255, 0])
        self.assertEqual(state.get()["heights"], [20, 0])

    def test_profile_edit_during_frame_build_keeps_preview_in_logical_order(self):
        cfg = Config(jet_count=2, reverse_jets=True,
                     jet_enabled=(True, False), base_colour=(12, 34, 56, 78))
        building = threading.Event()
        edit_attempted = threading.Event()
        applied = threading.Event()
        errors = []
        state = None
        editor = None

        class Server:
            def shutdown(self):
                pass

        def serve(live_state, _cfg, control):
            nonlocal state, editor
            state = live_state
            profile = control.profile()
            profile["settings"]["reverse_jets"] = False

            def edit_profile():
                try:
                    if not building.wait(2):
                        raise TimeoutError("frame build did not start")
                    edit_attempted.set()
                    control.apply(profile)
                    applied.set()
                except Exception as exc:
                    errors.append(exc)

            editor = threading.Thread(target=edit_profile)
            editor.start()
            return Server()

        real_frame = wave.Wave.frame

        def paused_frame(self, tracker_frame, now, lights_only=False):
            building.set()
            if not edit_attempted.wait(2):
                raise TimeoutError("profile edit did not start")
            applied.wait(0.2)
            return real_frame(self, tracker_frame, now, lights_only)

        try:
            with mock.patch.object(run.viewer, "serve", serve), \
                    mock.patch.object(wave.Wave, "frame", paused_frame):
                run._show_loop(iter([(1.0, [])]), cfg, None, "test",
                               SimpleNamespace(lights_only=False),
                               lambda _frame: True, lambda: True)
        finally:
            if editor is not None:
                editor.join(2)

        self.assertFalse(editor.is_alive())
        self.assertEqual(errors, [])
        self.assertTrue(applied.is_set())
        self.assertEqual(state.get()["pixel_colours"],
                         [[12, 34, 56, 78], [0, 0, 0, 0]])

    def test_held_test_resend_keeps_its_original_logical_jet_after_routing_edit(self):
        cfg = Config(jet_count=3, reverse_jets=True, resend_seconds=0)
        views = []
        control = None
        state = None

        class Server:
            def shutdown(self):
                pass

        def serve(live_state, _cfg, live_control):
            nonlocal control, state
            control, state = live_control, live_state
            return Server()

        def source():
            control.set_test_mode(True)
            control.test_jet(0, 20)
            views.append(state.get())
            cfg.reverse_jets = False
            yield 1.0, []
            views.append(state.get())

        with mock.patch.object(run.viewer, "serve", serve):
            run._show_loop(source(), cfg, None, "test",
                           SimpleNamespace(lights_only=False),
                           lambda _frame: True, lambda: True)

        self.assertEqual(views[0]["heights"], [20, 0, 0])
        self.assertEqual(views[1]["heights"], [20, 0, 0])
        self.assertEqual(views[1]["pixel_colours"][0], list(cfg.slow_colour))

    def test_preview_keeps_routing_used_to_build_frame_when_profile_changes_during_send(self):
        cfg = Config(jet_count=2, reverse_jets=True,
                     jet_enabled=(True, False), base_colour=(12, 34, 56, 78))
        state = None

        class Server:
            def shutdown(self):
                pass

        def serve(live_state, _cfg, _control):
            nonlocal state
            state = live_state
            return Server()

        def send(_frame):
            cfg.reverse_jets = False
            cfg.jet_count = 3
            return True

        with mock.patch.object(run.viewer, "serve", serve):
            run._show_loop(iter([(1.0, [])]), cfg, None, "test",
                           SimpleNamespace(lights_only=False), send, lambda: True)

        self.assertEqual(state.get()["pixel_colours"],
                         [[12, 34, 56, 78], [0, 0, 0, 0]])
        self.assertEqual(state.get()["heights"], [0, 0])

    def test_show_modes_held_test_and_verified_zero_follow_sent_output(self):
        cfg = Config(viewer_host="127.0.0.1", viewer_port=0,
                     idle_water_animation="pulse", idle_seconds=2,
                     idle_height=20, base_colour=(7, 8, 9, 10),
                     resend_seconds=0)
        views = []
        sent = []
        control = None
        state = None

        class Server:
            def shutdown(self):
                pass

        def serve(live_state, _cfg, live_control):
            nonlocal control, state
            control, state = live_control, live_state
            return Server()

        def source():
            yield 1.0, []
            views.append(state.get())
            control.set_lights_only(True)
            yield 1.0, []
            views.append(state.get())
            control.set_lights_only(False)
            control.set_test_mode(True)
            views.append(state.get())
            control.test_jet(2, 30)
            views.append(state.get())
            control.all_off()
            views.append(state.get())
            yield 1.0, []
            views.append(state.get())

        def send(frame):
            sent.append(list(frame))
            return True

        def zero():
            sent.append(list(dmx.blank_frame()))
            return True

        with mock.patch.object(run.viewer, "serve", serve):
            run._show_loop(source(), cfg, None, "test",
                           SimpleNamespace(lights_only=False), send, zero)

        self.assertEqual(views[0]["heights"], [20] * cfg.jet_count)
        self.assertEqual(views[0]["pixel_colours"], [[7, 8, 9, 10]] * cfg.jet_count)
        self.assertEqual(views[1]["heights"], [0] * cfg.jet_count)
        self.assertEqual(views[1]["pixel_colours"], [[7, 8, 9, 10]] * cfg.jet_count)
        self.assertEqual(views[2]["pixel_colours"], [[0, 0, 0, 0]] * cfg.jet_count)
        self.assertEqual(views[3]["heights"][2], 30)
        self.assertEqual(views[3]["pixel_colours"][2], list(cfg.slow_colour))
        self.assertEqual(views[4]["heights"], [0] * cfg.jet_count)
        self.assertEqual(views[4]["pixel_colours"], [[0, 0, 0, 0]] * cfg.jet_count)
        self.assertEqual(views[5]["pixel_colours"], views[4]["pixel_colours"])


class TestLiveBrowserPreview(unittest.TestCase):
    def test_pixel_fill_uses_white_caps_values_and_keeps_black_visible(self):
        if not shutil.which("node"):
            self.skipTest("Node.js is needed for Live browser behavior")
        page_script = PAGE.split("<script>", 1)[1].split("</script>", 1)[0]
        browser_script = """
const vm=require('node:vm');
const arcs=[],outlines=[],requests=[],clears=[];
const ctx={fillStyle:'',strokeStyle:'',lineWidth:1,
  fillRect(){clears.push(this.fillStyle)},beginPath(){this.arcPending=false},moveTo(){},lineTo(){},
  stroke(){if(this.arcPending)outlines.push({colour:this.strokeStyle,radius:this.lastRadius})},
  strokeRect(){},setLineDash(){},fillText(){},
  arc(x,y,r){this.lastRadius=r;this.arcPending=true},
  fill(){arcs.push({colour:this.fillStyle,radius:this.lastRadius})}};
const canvas={width:800,height:600,getContext(){return ctx}};
const hud={textContent:''},position={className:'',textContent:''};
const nodes={c:canvas,hud,position};
const context=vm.createContext({document:{getElementById:id=>nodes[id]},
  window:{innerWidth:800,innerHeight:600,addEventListener(){}},
  setTimeout(){},fetch:async path=>{requests.push(path);
    if(path==='/config')return {json:async()=>({roi_x_min:0,roi_x_max:2,
      roi_y_min:0,roi_y_max:2,strip_points:[[0.5,0.5],[1.5,0.5]],
      jet_count:2,height_max:40})};
    throw Error('state offline')}});
vm.runInContext(process.argv[2].replace(/fit\\(\\); poll\\(\\);\\s*$/, ''),context);
vm.runInContext(`CFG={roi_x_min:0,roi_x_max:2,roi_y_min:0,roi_y_max:2,
  strip_points:[[0.5,0.5],[1.5,0.5]],jet_count:2,height_max:40};
  FRAME={pixel_colours:[[0,0,0,0],[250,10,20,20]],heights:[0,40],
  fg:[],bg:[],legs:[],tracks:[],clusters:[],detections:[],hz:16};draw();`,context);
const before=arcs.slice();
vm.runInContext('poll()',context).then(()=>{
  console.log(JSON.stringify({before,outlines,requests,clears,
    frame:vm.runInContext('FRAME',context),position:position.className,
    arcs:arcs.length}));
});
"""
        run_result = subprocess.run(["node", "-", page_script], input=browser_script,
                                    capture_output=True, text=True)
        self.assertEqual(run_result.returncode, 0, run_result.stderr)
        result = json.loads(run_result.stdout)
        self.assertEqual(result["before"][0], {"colour": "rgb(0, 0, 0)", "radius": 2.5})
        self.assertEqual(result["before"][1], {"colour": "rgb(255, 30, 40)",
                                                "radius": 11.5})
        self.assertEqual(result["before"][2]["colour"], "#ff0")
        self.assertEqual(result["outlines"][0], {"colour": "#bbc", "radius": 2.5})
        self.assertEqual(result["requests"], ["/config", "/state"])
        self.assertEqual(result["clears"], ["#111", "#111"])
        self.assertIsNone(result["frame"])
        self.assertEqual(result["position"], "stale")


if __name__ == "__main__":
    unittest.main()
