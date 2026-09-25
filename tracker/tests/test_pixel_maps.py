"""Browser checks for commanded Pixel colours on both maps."""

import json
import shutil
import subprocess
import unittest

from tracker.viewer import PAGE, SETTINGS_PAGE


class TestPixelMaps(unittest.TestCase):
    def test_both_maps_show_the_same_live_pixels_and_settings_clears_on_loss(self):
        if not shutil.which("node"):
            self.skipTest("Node.js is needed for browser behavior")
        live_script = PAGE.split("<script>", 1)[1].split("</script>", 1)[0]
        settings_script = SETTINGS_PAGE.split("<script>", 1)[1].split("</script>", 1)[0]
        browser = r"""
const vm=require('node:vm');
const liveScript=process.argv[2].replace(/fit\(\); poll\(\);\s*$/, '');
const settingsScript=process.argv[3].replace(/init\(\);pollState\(\);\s*$/, '');
const frame=(colours)=>({pixel_colours:colours,heights:[0,40],
  fg:[[0.8,0.8]],bg:[[0.9,0.9]],tracks:[{id:1,x:1,y:1,vx:0,vy:0,
    speed:0,s:0,jet:1,times_seen:1,dist_travelled:0,confirmed:true,seen:true}],
  legs:[],clusters:[],detections:[],hz:16});
const pureColours=[[[255,0,0,0],[0,255,0,0]],[[0,0,255,0],[0,0,0,128]]];
function browser(script){
  const fills=[],outlines=[],labels=[],timers=[],rects=[],strokes=[];
  const ctx={fillStyle:'',strokeStyle:'',lineWidth:1,
    setTransform(){},fillRect(){},strokeRect(x,y,w,h){rects.push({colour:this.strokeStyle,w,h})},setLineDash(){},
    beginPath(){this.arcPending=false},moveTo(){},lineTo(){},
    arc(x,y,r){this.arcPending=true;this.radius=r},
    fill(){if(this.arcPending)fills.push({colour:this.fillStyle,radius:this.radius})},
    stroke(){strokes.push(this.strokeStyle);
      if(this.arcPending)outlines.push({colour:this.strokeStyle,radius:this.radius})},
    fillText(text){labels.push({text,colour:this.fillStyle})},strokeText(text){labels.push({text,outline:this.strokeStyle})}};
  const canvas={width:800,height:600,getContext(){return ctx},
    getBoundingClientRect(){return {width:800,height:600}}};
  const nodes=new Map([['c',canvas],['path',canvas]]);
  const getNode=id=>{if(!nodes.has(id))nodes.set(id,{classList:{toggle(){},add(){},remove(){}},
    style:{},hidden:false,textContent:'',value:'',getBoundingClientRect(){return {width:180,height:180}}});
    return nodes.get(id)};
  const states=[frame([[0,0,0,0],[250,10,20,20]]),
    frame([[20,40,60,10],[0,0,0,0]]),...pureColours.map(frame)];
  const context=vm.createContext({devicePixelRatio:1,
    document:{getElementById:getNode,querySelector(){return {addEventListener(){}}},
      querySelectorAll(){return []}},
    window:{innerWidth:800,innerHeight:600,addEventListener(){}},
    localStorage:{getItem(){return null},setItem(){}},
    setTimeout(fn,ms){timers.push(ms)},clearTimeout(){},
    fetch:async path=>{if(path!=='/state')throw Error('unexpected '+path);
      if(!states.length)throw Error('offline');return {ok:true,json:async()=>states.shift()}}});
  vm.runInContext(script,context);
  return {context,fills,outlines,labels,timers,rects,strokes};
}
const live=browser(liveScript);
vm.runInContext(`CFG={roi_x_min:0,roi_x_max:2,roi_y_min:0,roi_y_max:2,
  strip_points:[[0.5,0.5],[1.5,0.5]],jet_count:2,height_max:40};
  FRAME=(${JSON.stringify(frame([[0,0,0,0],[250,10,20,20]]))});draw()`,live.context);
const liveJets=live.fills.filter(x=>x.radius===2.5||x.radius===11.5);
const livePure=pureColours.map(colours=>{
  live.fills.length=0;
  vm.runInContext(`FRAME=(${JSON.stringify(frame(colours))});draw()`,live.context);
  return live.fills.filter(x=>x.radius===2.5||x.radius===11.5);
});
const settings=browser(settingsScript);
vm.runInContext(`profile={settings:{roi_x_min:0,roi_x_max:2,roi_y_min:0,roi_y_max:2,
  strip_points:[[0.5,0.5],[1.5,0.5]],jet_count:2,height_max:40}};
  roi={xmin:0,xmax:2,ymin:0,ymax:2}`,settings.context);
(async()=>{
  await vm.runInContext('pollState()',settings.context);
  const first=settings.fills.filter(x=>x.radius===4||x.radius===13);
  const firstColours=settings.fills.map(x=>x.colour);
  const firstOutlines=settings.outlines.filter(x=>x.radius===4||x.radius===13);
  const firstLabels=settings.labels.filter(x=>x.text==='1'||x.text==='2');
  const firstRects=settings.rects.slice(),firstStrokes=settings.strokes.slice();
  settings.fills.length=0;
  await vm.runInContext('pollState()',settings.context);
  const edited=settings.fills.filter(x=>x.radius===4||x.radius===13);
  const settingsPure=[];
  for(const colours of pureColours){
    settings.fills.length=0;
    await vm.runInContext('pollState()',settings.context);
    settingsPure.push(settings.fills.filter(x=>x.radius===4||x.radius===13));
  }
  settings.fills.length=0;
  await vm.runInContext('pollState()',settings.context);
  const lost=settings.fills.filter(x=>x.radius===4||x.radius===13);
  console.log(JSON.stringify({liveJets,first,firstColours,firstOutlines,firstLabels,
    firstRects,firstStrokes,edited,livePure,settingsPure,lost,
    frame:vm.runInContext('liveFrame',settings.context),timers:settings.timers,
  }));
})().catch(e=>{console.error(e);process.exitCode=1});
"""
        run = subprocess.run(["node", "-", live_script, settings_script],
                             input=browser, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        seen = json.loads(run.stdout)
        self.assertEqual(seen["liveJets"], [
            {"colour": "rgb(0, 0, 0)", "radius": 2.5},
            {"colour": "rgb(255, 30, 40)", "radius": 11.5},
        ])
        self.assertEqual(seen["first"], [
            {"colour": "rgb(0, 0, 0)", "radius": 4},
            {"colour": "rgb(255, 30, 40)", "radius": 13},
        ])
        self.assertIn({"colour": "#e9fffa", "radius": 4}, seen["firstOutlines"])
        self.assertIn({"text": "1", "outline": "#092f35"}, seen["firstLabels"])
        self.assertIn({"text": "2", "outline": "#092f35"}, seen["firstLabels"])
        self.assertIn("#527277", seen["firstColours"])
        self.assertIn("#45dce7", seen["firstColours"])
        self.assertGreater(seen["firstColours"].index("#0f6"),
                           seen["firstColours"].index("rgb(255, 30, 40)"))
        self.assertIn("#54d6c1", seen["firstStrokes"])
        self.assertEqual(sum(r["w"] == 12 for r in seen["firstRects"]), 2)
        self.assertTrue(any(r["w"] > 12 for r in seen["firstRects"]))
        self.assertEqual(seen["edited"], [
            {"colour": "rgb(30, 50, 70)", "radius": 4},
            {"colour": "rgb(0, 0, 0)", "radius": 13},
        ])
        for page in ("livePure", "settingsPure"):
            with self.subTest(page=page):
                self.assertEqual(
                    [[jet["colour"] for jet in pair] for pair in seen[page]],
                    [["rgb(255, 0, 0)", "rgb(0, 255, 0)"],
                     ["rgb(0, 0, 255)", "rgb(128, 128, 128)"]])
        self.assertEqual(seen["lost"], [
            {"colour": "#45dce7", "radius": 4},
            {"colour": "#45dce7", "radius": 4},
        ])
        self.assertIsNone(seen["frame"])
        self.assertEqual(seen["timers"], [100, 100, 100, 100, 100])


if __name__ == "__main__":
    unittest.main()
