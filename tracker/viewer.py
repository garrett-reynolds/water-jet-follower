"""A web scan viewer, because Raspberry Pi OS Lite has no window to plot in.

Serves one page from the Pi. Open it on a laptop:

    http://water-jets.local:8080/

Standard library only - no Flask, no numpy. The page polls /state and draws a
top-down view: the room, the strip, the raw scan, and the tracks.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from tracker import geometry
from tracker.settings import SettingsControl


class State:
    """The one frame the viewer is allowed to see. Written by the tracker thread."""

    def __init__(self):
        self._lock = threading.Lock()
        self._frame = {"t": 0, "tracks": [], "clusters": [], "legs": [],
                       "detections": [], "fg": [], "bg": [], "hz": 0.0}

    def set(self, frame):
        with self._lock:
            self._frame = frame

    def get(self):
        with self._lock:
            return self._frame


PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>water-jet tracker</title>
<style>
  body { margin:0; background:#111; color:#ddd; font:13px/1.4 monospace; }
  #hud { position:fixed; top:8px; left:8px; background:#000a; padding:8px 10px;
         border:1px solid #333; white-space:pre; }
  #position { position:fixed; top:8px; right:8px; background:#000e; color:#fff;
              padding:10px 16px; border:2px solid #0f6; font:bold 48px/1.15 monospace;
              white-space:pre; text-align:right; }
  canvas { display:block; }
  #settings-link { position:fixed; right:12px; bottom:12px; color:#fff;
    background:#126b72; padding:10px 14px; text-decoration:none; border-radius:4px; }
</style></head><body>
<div id="hud">connecting...</div>
<div id="position">x=--\ny=--\njet=--</div>
<a id="settings-link" href="/settings">Settings</a>
<canvas id="c"></canvas>
<script>
let CFG = null, FRAME = null;

function fit() {
  const c = document.getElementById('c');
  c.width = window.innerWidth; c.height = window.innerHeight;
}
window.addEventListener('resize', () => { fit(); draw(); });

function transform(c) {
  const w = CFG.roi_x_max - CFG.roi_x_min, h = CFG.roi_y_max - CFG.roi_y_min;
  const scale = Math.min(c.width / w, c.height / h) * 0.92;
  // +x right, +y up
  return {
    scale: scale,
    sx: (x) => (x - CFG.roi_x_min) * scale + (c.width - w * scale) / 2,
    sy: (y) => c.height - ((y - CFG.roi_y_min) * scale + (c.height - h * scale) / 2)
  };
}

function dot(ctx, t, x, y, r, colour) {
  ctx.fillStyle = colour;
  ctx.beginPath(); ctx.arc(t.sx(x), t.sy(y), r, 0, 6.2832); ctx.fill();
}

function draw() {
  const c = document.getElementById('c');
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#111'; ctx.fillRect(0, 0, c.width, c.height);
  if (!CFG || !FRAME) return;
  const t = transform(c);

  // half-metre grid
  ctx.strokeStyle = '#222'; ctx.lineWidth = 1;
  for (let x = Math.ceil(CFG.roi_x_min * 2) / 2; x <= CFG.roi_x_max; x += 0.5) {
    ctx.beginPath(); ctx.moveTo(t.sx(x), t.sy(CFG.roi_y_min));
    ctx.lineTo(t.sx(x), t.sy(CFG.roi_y_max)); ctx.stroke();
  }
  for (let y = Math.ceil(CFG.roi_y_min * 2) / 2; y <= CFG.roi_y_max; y += 0.5) {
    ctx.beginPath(); ctx.moveTo(t.sx(CFG.roi_x_min), t.sy(y));
    ctx.lineTo(t.sx(CFG.roi_x_max), t.sy(y)); ctx.stroke();
  }

  // the strip and its jets
  const path = CFG.strip_points || [CFG.strip_start, CFG.strip_end];
  ctx.strokeStyle = '#2a6'; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(t.sx(path[0][0]), t.sy(path[0][1]));
  for (let j = 1; j < path.length; j++) {
    ctx.lineTo(t.sx(path[j][0]), t.sy(path[j][1]));
  }
  ctx.stroke();
  // Each jet is drawn at the size of the height it has actually been commanded,
  // so the hill is visible. Without this every jet is the same dot and the only
  // thing the page can tell you is that something is happening.
  const H = FRAME.heights || [];
  for (let j = 0; j < CFG.jet_count; j++) {
    const x = path[j][0], y = path[j][1];
    const h = H[j] || 0;
    const up = CFG.height_max > 0 ? Math.min(1, h / CFG.height_max) : 0;
    dot(ctx, t, x, y, 2.5 + 9 * up, up > 0 ? '#4cf' : '#2a6');
    if (h > 0) {
      ctx.fillStyle = '#9ef'; ctx.font = '10px system-ui';
      ctx.fillText(h, t.sx(x) - 6, t.sy(y) - 14);
    }
  }
  const peak = H.length ? Math.max.apply(null, H) : 0;
  ctx.fillStyle = peak > 0 ? '#4cf' : '#666'; ctx.font = '13px system-ui';
  ctx.fillText('tallest jet ' + peak + ' / ' + CFG.height_max
               + '  (' + (peak * 0.762).toFixed(1) + ' cm)', 12, 22);

  // the LiDAR itself
  dot(ctx, t, 0, 0, 6, '#ff0');

  // scan points
  for (const p of FRAME.bg) dot(ctx, t, p[0], p[1], 1.2, '#3a3a3a');
  for (const p of FRAME.fg) dot(ctx, t, p[0], p[1], 1.8, '#8cf');

  // leg clusters
  for (const g of FRAME.legs) {
    ctx.strokeStyle = '#f80'; ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(t.sx(g.x), t.sy(g.y), Math.max(4, g.w * t.scale / 2), 0, 6.2832);
    ctx.stroke();
  }

  // tracks
  for (const k of FRAME.tracks) {
    const colour = k.confirmed ? (k.seen ? '#0f6' : '#f44') : '#888';
    dot(ctx, t, k.x, k.y, 8, colour);
    ctx.strokeStyle = colour; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(t.sx(k.x), t.sy(k.y));
    ctx.lineTo(t.sx(k.x + k.vx * 0.5), t.sy(k.y + k.vy * 0.5)); ctx.stroke();
    ctx.fillStyle = '#fff'; ctx.font = '12px monospace';
    ctx.fillText('#' + k.id + '  ' + k.speed.toFixed(2) + ' m/s  jet ' + k.jet,
                 t.sx(k.x) + 12, t.sy(k.y) - 8);
  }

  const lines = [
    'scan rate   ' + FRAME.hz.toFixed(2) + ' Hz',
    'points      ' + (FRAME.fg.length + FRAME.bg.length) +
      '  (' + FRAME.fg.length + ' moving)',
    'clusters    ' + FRAME.clusters.length + '   legs ' + FRAME.legs.length +
      '   people ' + FRAME.detections.length,
    'tracks      ' + FRAME.tracks.length + '   confirmed ' +
      FRAME.tracks.filter(k => k.confirmed).length,
    'source      ' + (FRAME.source || '-')
  ];
  for (const k of FRAME.tracks) {
    lines.push('  #' + k.id + ' ' + (k.confirmed ? 'ok  ' : 'new ') +
      'x=' + k.x.toFixed(2) + ' y=' + k.y.toFixed(2) +
      ' s=' + k.s.toFixed(2) + ' v=' + k.speed.toFixed(2) +
      ' seen=' + k.times_seen + ' d=' + k.dist_travelled.toFixed(2) +
      (k.seen ? '' : ' OCCLUDED'));
  }
  document.getElementById('hud').textContent = lines.join('\\n');
  const person = FRAME.tracks.find(k => k.seen) || FRAME.tracks[0];
  document.getElementById('position').textContent = person
    ? 'x=' + person.x.toFixed(2) + '\\ny=' + person.y.toFixed(2)
      + '\\njet=' + person.jet
    : 'x=--\\ny=--\\njet=--';
}

async function poll() {
  try {
    if (!CFG) CFG = await (await fetch('/config')).json();
    FRAME = await (await fetch('/state')).json();
    draw();
  } catch (e) {
    document.getElementById('hud').textContent = 'lost the Pi: ' + e;
  }
  setTimeout(poll, 66);
}
fit(); poll();
</script></body></html>
"""


SETTINGS_PAGE = r"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Water jet settings</title>
<style>
:root { --ink:#16353a; --paper:#edf5f3; --panel:#fff; --water:#087e8b;
  --light:#d9fff5; --danger:#b9382f; --line:#b7cbc8; --muted:#587276; }
* { box-sizing:border-box; }
body { margin:0; color:var(--ink); background:var(--paper);
  font:15px/1.35 "Segoe UI", Arial, sans-serif; }
header { display:flex; align-items:center; justify-content:space-between; gap:16px;
  padding:16px 22px; background:var(--ink); color:white; }
h1 { margin:0; font-size:22px; font-weight:650; }
header a { color:var(--light); }
main { display:grid; grid-template-columns:minmax(360px,1.35fr) minmax(340px,1fr);
  min-height:calc(100vh - 62px); }
.map { position:sticky; top:0; height:calc(100vh - 62px); background:#092f35; }
#path { width:100%; height:100%; display:block; touch-action:none; }
.map-tools { position:absolute; left:16px; bottom:16px; display:flex; gap:8px; flex-wrap:wrap; }
.map-view { position:absolute; right:16px; top:16px; display:flex; gap:6px; align-items:center;
  padding:6px; border:1px solid #3e686c; border-radius:5px; background:#08272ccc; color:#d7efeb; }
.map-view button { min-width:38px; background:#123f45; border-color:#47777b; color:white; }
#live-state { padding:0 5px; font-size:13px; }
.controls { padding:18px; overflow:auto; }
section { background:var(--panel); border:1px solid var(--line); margin:0 0 14px;
  padding:16px; border-radius:6px; }
h2 { font-size:17px; margin:0 0 12px; }
.grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px 14px; }
label { display:grid; gap:4px; color:var(--muted); font-size:13px; }
input, button { font:inherit; }
input[type=number] { width:100%; padding:8px; border:1px solid var(--line); border-radius:3px; }
button, .file { border:1px solid #789b9c; background:white; color:var(--ink);
  border-radius:4px; padding:8px 11px; cursor:pointer; }
button.primary { background:var(--water); border-color:var(--water); color:white; font-weight:650; }
button.danger { border-color:var(--danger); color:var(--danger); font-weight:650; }
button:focus-visible, input:focus-visible { outline:3px solid #f3b61f; outline-offset:2px; }
.actions { display:flex; flex-wrap:wrap; gap:8px; }
.lock { border-left:4px solid var(--danger); padding-left:10px; }
.colours { display:grid; grid-template-columns:70px repeat(4,1fr); gap:6px; align-items:end; }
.jets { display:grid; grid-template-columns:repeat(4,1fr); gap:6px; }
.jet { border:1px solid var(--line); padding:7px; display:grid; gap:5px; border-radius:4px; }
.jet button { padding:4px; }
#status { min-height:42px; padding:10px; background:#dce9e6; border-radius:4px; }
#status.bad { background:#ffe4df; color:#7d211b; }
.note { color:var(--muted); font-size:13px; }
@media (max-width:850px) { main { grid-template-columns:1fr; } .map { position:relative; height:52vh; } }
</style></head><body>
<header><h1>Water and light control</h1><a href="/">Live viewer</a></header>
<main>
  <div class="map"><canvas id="path"></canvas><div class="map-view">
    <span id="live-state">LiDAR waiting</span><button id="zoom-out" aria-label="Zoom out">−</button>
    <button id="zoom-fit">Fit</button><button id="zoom-in" aria-label="Zoom in">+</button>
  </div><div class="map-tools">
    <button id="add-point">Add point</button><button id="remove-point">Remove point</button>
    <button id="undo">Undo applied</button><button id="reset">Reset defaults</button>
  </div></div>
  <div class="controls">
    <div id="status">Loading settings.</div>
    <section><h2>Water shape</h2><div class="grid">
      <label>Jet count<input id="jet_count" type="number" min="1" max="20"></label>
      <label>Minimum active height<input id="height_min" type="number" min="1" max="255"></label>
      <label>Normal hill height<input id="hill_peak" type="number" min="1" max="255"></label>
      <label class="lock">Hard maximum height<input id="height_max" type="number" min="1" max="255" disabled>
        <span><input id="unlock" type="checkbox"> Unlock this safety limit</span></label>
      <label>Hill width in jets<input id="hill_jets" type="number" min="1" max="20"></label>
      <label>Lead time in seconds<input id="lead_seconds" type="number" min="0" max="2" step="0.01"></label>
      <label>Follow response in seconds<input id="follow_response" type="number" min="0" max="5" step="0.01"></label>
      <label><span><input id="reverse_jets" type="checkbox"> Reverse jet order</span></label>
    </div></section>
    <section><h2>Speed colours</h2><div class="colours" id="colours"></div>
      <div class="grid" style="margin-top:10px">
        <label>Slow speed<input id="slow_speed" type="number" min="0" max="10" step="0.1"></label>
        <label>Fast speed<input id="fast_speed" type="number" min="0" max="10" step="0.1"></label>
      </div></section>
    <section><h2>Jet controls</h2><div class="jets" id="jets"></div></section>
    <section><h2>Run controls</h2><div class="actions">
      <button id="lights">Lights only: off</button>
      <button id="all-off" class="danger">ALL OFF</button>
    </div></section>
    <section><h2>Profile</h2><p class="note">Edits stay in preview until you apply the complete profile.</p>
      <div class="actions"><button id="apply" class="primary">Apply profile</button>
      <button id="save">Save JSON</button><label class="file">Load JSON<input id="load" type="file" accept="application/json" hidden></label></div>
    </section>
  </div>
</main>
<script>
let profile, original, defaultProfile, roi, liveFrame=null, selected=0, dragging=false, lightsOnly=false;
let zoom=1, viewCentre=null;
const $=id=>document.getElementById(id);
const fields=['jet_count','height_min','hill_peak','height_max','hill_jets','lead_seconds','follow_response','slow_speed','fast_speed'];
const colourNames=['base_colour','slow_colour','fast_colour'];
const labels={base_colour:'Base',slow_colour:'Slow',fast_colour:'Fast'};
function status(text,bad=false){$('status').textContent=text;$('status').className=bad?'bad':'';}
function copy(v){return JSON.parse(JSON.stringify(v));}
async function api(path,body){const r=await fetch(path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});const data=await r.json();if(!r.ok)throw Error(data.error||r.statusText);return data;}
function buildColours(){const box=$('colours');box.innerHTML='<span></span><span>R</span><span>G</span><span>B</span><span>W</span>';for(const name of colourNames){box.insertAdjacentHTML('beforeend','<strong>'+labels[name]+'</strong>'+[0,1,2,3].map(i=>'<input type="number" min="0" max="255" id="'+name+'_'+i+'">').join(''));}}
function readForm(){const s=copy(profile.settings);for(const n of fields)s[n]=Number($(n).value);s.reverse_jets=$('reverse_jets').checked;s.jet_enabled=[...document.querySelectorAll('.jet input')].map(x=>x.checked);for(const n of colourNames)s[n]=[0,1,2,3].map(i=>Number($(n+'_'+i).value));profile.settings=s;return profile;}
function fill(){const s=profile.settings;for(const n of fields)$(n).value=s[n];$('reverse_jets').checked=s.reverse_jets;$('height_max').disabled=!$('unlock').checked;for(const n of colourNames)for(let i=0;i<4;i++)$(n+'_'+i).value=s[n][i];buildJets();draw();status('Preview only. Apply the complete profile when it looks right.');}
function buildJets(){const count=Number($('jet_count').value)||profile.settings.jet_count;let e=profile.settings.jet_enabled||[];while(e.length<count)e.push(true);e=e.slice(0,count);profile.settings.jet_enabled=e;const box=$('jets');box.innerHTML='';e.forEach((on,i)=>box.insertAdjacentHTML('beforeend','<div class="jet"><label><span>Jet '+(i+1)+'</span><input type="checkbox" '+(on?'checked':'')+'></label><button data-test="'+i+'">Test</button></div>'));box.querySelectorAll('button').forEach(b=>b.onclick=()=>testJet(Number(b.dataset.test)));}
function size(){const c=$('path'),r=c.getBoundingClientRect();c.width=r.width*devicePixelRatio;c.height=r.height*devicePixelRatio;draw();}
function bounds(){const cx=viewCentre?viewCentre[0]:(roi.xmin+roi.xmax)/2,cy=viewCentre?viewCentre[1]:(roi.ymin+roi.ymax)/2,hw=(roi.xmax-roi.xmin)/zoom/2,hh=(roi.ymax-roi.ymin)/zoom/2;return {xmin:cx-hw,xmax:cx+hw,ymin:cy-hh,ymax:cy+hh};}
function xy(p){const c=$('path'),v=bounds(),pad=45,w=c.width/devicePixelRatio-pad*2,h=c.height/devicePixelRatio-pad*2;return [pad+(p[0]-v.xmin)/(v.xmax-v.xmin)*w,pad+h-(p[1]-v.ymin)/(v.ymax-v.ymin)*h];}
function world(x,y){const c=$('path'),v=bounds(),pad=45,w=c.width/devicePixelRatio-pad*2,h=c.height/devicePixelRatio-pad*2;return [v.xmin+(x-pad)/w*(v.xmax-v.xmin),v.ymin+(pad+h-y)/h*(v.ymax-v.ymin)];}
function scanDot(ctx,p,r,colour){const q=xy(p);ctx.fillStyle=colour;ctx.beginPath();ctx.arc(q[0],q[1],r,0,Math.PI*2);ctx.fill();}
function jetPoints(points,count){if(count===points.length)return points;const lengths=points.slice(1).map((p,i)=>Math.hypot(p[0]-points[i][0],p[1]-points[i][1])),total=lengths.reduce((a,b)=>a+b,0);if(count<=1||!total)return [points[0]];let segment=0,before=0;return Array.from({length:count},(_,i)=>{const target=total*i/(count-1);while(segment<lengths.length-1&&before+lengths[segment]<target){before+=lengths[segment++]}const a=points[segment],b=points[segment+1],t=lengths[segment]?(target-before)/lengths[segment]:0;return [a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])]});}
function draw(){if(!profile||!roi)return;const c=$('path'),ctx=c.getContext('2d');ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);ctx.fillStyle='#092f35';ctx.fillRect(0,0,c.width,c.height);const v=bounds();ctx.strokeStyle='#17474d';ctx.lineWidth=1;for(let x=Math.ceil(v.xmin*2)/2;x<=v.xmax;x+=.5){const a=xy([x,v.ymin]),b=xy([x,v.ymax]);ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke()}for(let y=Math.ceil(v.ymin*2)/2;y<=v.ymax;y+=.5){const a=xy([v.xmin,y]),b=xy([v.xmax,y]);ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke()}if(liveFrame){for(const p of liveFrame.bg||[])scanDot(ctx,p,1.3,'#527277');for(const p of liveFrame.fg||[])scanDot(ctx,p,2.2,'#45dce7');for(const t of liveFrame.tracks||[])scanDot(ctx,[t.x,t.y],t.confirmed?7:5,t.confirmed?'#f3b61f':'#92aaa8')}scanDot(ctx,[0,0],6,'#fff06a');const pts=profile.settings.strip_points;ctx.strokeStyle='#54d6c1';ctx.lineWidth=3;ctx.beginPath();pts.forEach((p,i)=>{const q=xy(p);i?ctx.lineTo(...q):ctx.moveTo(...q)});ctx.stroke();jetPoints(profile.settings.strip_points,profile.settings.jet_count).forEach((p,i)=>{const q=xy(p);ctx.fillStyle='#45dce7';ctx.beginPath();ctx.arc(...q,4,0,Math.PI*2);ctx.fill();ctx.fillStyle='#fff';ctx.fillText(String(i+1),q[0]+6,q[1]-6)});pts.forEach((p,i)=>{const q=xy(p);ctx.strokeStyle=i===selected?'#f3b61f':'#e9fffa';ctx.lineWidth=2;ctx.strokeRect(q[0]-6,q[1]-6,12,12)});}
function nearest(x,y){let best=0,dist=Infinity;profile.settings.strip_points.forEach((p,i)=>{const q=xy(p),d=(q[0]-x)**2+(q[1]-y)**2;if(d<dist){dist=d;best=i}});return dist<900?best:null;}
function dirty(){readForm();draw();status('Preview only. Nothing is live yet.');}
async function apply(){try{readForm();profile=await api('/settings/apply',{profile,unlock_height_max:$('unlock').checked});original=copy(profile);$('unlock').checked=false;fill();status('Profile applied.');}catch(e){status(e.message,true)}}
async function testJet(i){try{await api('/actions/test-jet',{jet:i});status('Jet '+(i+1)+' test sent. Use ALL OFF when finished.');}catch(e){status(e.message,true)}}
async function init(){buildColours();try{const data=await api('/settings-data');profile=data.profile;original=copy(profile);defaultProfile=data.default_profile;roi=data.roi;lightsOnly=data.lights_only;fill();$('lights').textContent='Lights only: '+(lightsOnly?'on':'off');size();}catch(e){status(e.message,true)}}
async function pollState(){try{liveFrame=await api('/state');const count=(liveFrame.fg||[]).length+(liveFrame.bg||[]).length;$('live-state').textContent='LiDAR live · '+count+' points';draw()}catch(e){$('live-state').textContent='LiDAR not available'}setTimeout(pollState,100)}
function setZoom(value){zoom=Math.max(1,Math.min(8,value));if(zoom===1)viewCentre=null;else if(profile)viewCentre=profile.settings.strip_points[selected];draw()}
$('unlock').onchange=()=>{$('height_max').disabled=!$('unlock').checked};
$('jet_count').onchange=()=>{readForm();buildJets();dirty()};
$('colours').onchange=dirty;
document.querySelector('.controls').addEventListener('change',e=>{if(e.target.matches('input')&&!['load','jet_count','unlock'].includes(e.target.id))dirty()});
$('apply').onclick=apply;
$('save').onclick=()=>{readForm();const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(profile,null,2)],{type:'application/json'}));a.download='water-jet-profile.json';a.click();URL.revokeObjectURL(a.href)};
$('load').onchange=async e=>{try{profile=JSON.parse(await e.target.files[0].text());fill()}catch(err){status('Could not read that JSON file.',true)}};
$('undo').onclick=async()=>{try{profile=await api('/settings/undo',{});fill();status('Last applied profile restored.')}catch(e){status(e.message,true)}};
$('reset').onclick=()=>{profile=copy(defaultProfile);fill();status('Default profile previewed. Press Apply profile to make it live.');};
$('lights').onclick=async()=>{try{const d=await api('/actions/lights-only',{enabled:!lightsOnly});lightsOnly=d.enabled;$('lights').textContent='Lights only: '+(lightsOnly?'on':'off');}catch(e){status(e.message,true)}};
$('all-off').onclick=async()=>{try{const d=await api('/actions/all-off',{});status(d.all_zero?'ALL OFF verified. All 512 slots are zero.':'ALL OFF could not be verified.',!d.all_zero)}catch(e){status(e.message,true)}};
$('zoom-in').onclick=()=>setZoom(zoom*1.5);$('zoom-out').onclick=()=>setZoom(zoom/1.5);$('zoom-fit').onclick=()=>setZoom(1);
$('add-point').onclick=()=>{readForm();const p=profile.settings.strip_points, a=p[Math.max(0,p.length-2)], b=p[p.length-1];p.splice(p.length-1,0,[(a[0]+b[0])/2,(a[1]+b[1])/2]);selected=p.length-2;dirty()};
$('remove-point').onclick=()=>{readForm();if(profile.settings.strip_points.length<=2)return status('The path needs at least two points.',true);profile.settings.strip_points.splice(selected,1);selected=Math.max(0,selected-1);dirty()};
const canvas=$('path');canvas.onwheel=e=>{e.preventDefault();setZoom(e.deltaY<0?zoom*1.2:zoom/1.2)};canvas.onpointerdown=e=>{const r=canvas.getBoundingClientRect();const n=nearest(e.clientX-r.left,e.clientY-r.top);if(n!==null){selected=n;if(zoom>1)viewCentre=profile.settings.strip_points[selected];dragging=true;canvas.setPointerCapture(e.pointerId);draw()}};
canvas.onpointermove=e=>{if(!dragging)return;const r=canvas.getBoundingClientRect();profile.settings.strip_points[selected]=world(e.clientX-r.left,e.clientY-r.top);dirty()};
canvas.onpointerup=()=>dragging=false;window.onresize=size;init();pollState();
</script></body></html>"""


def make_handler(state, cfg, control=None):
    control = control or SettingsControl(cfg)

    class Handler(BaseHTTPRequestHandler):
        def _send(self, body, content_type, status=200):
            payload = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def _json(self, value, status=200):
            self._send(json.dumps(value), "application/json", status)

        def _body(self):
            length = int(self.headers.get("Content-Length", "0"))
            return json.loads(self.rfile.read(length) or b"{}")

        def do_GET(self):                       # noqa: N802 - http.server's name
            if self.path.startswith("/state"):
                self._send(json.dumps(state.get()), "application/json")
            elif self.path.startswith("/config"):
                self._send(json.dumps({
                    "roi_x_min": cfg.roi_x_min, "roi_x_max": cfg.roi_x_max,
                    "roi_y_min": cfg.roi_y_min, "roi_y_max": cfg.roi_y_max,
                    "strip_start": list(cfg.strip_start),
                    "strip_end": list(cfg.strip_end),
                    "strip_points": [list(point) for point in geometry.strip_points(cfg)],
                    "jet_count": cfg.jet_count,
                    "height_max": cfg.height_max,
                }), "application/json")
            elif self.path == "/settings-data":
                self._json({
                    "profile": control.profile(),
                    "default_profile": control.defaults(),
                    "lights_only": control.lights_only,
                    "roi": {"xmin": cfg.roi_x_min, "xmax": cfg.roi_x_max,
                            "ymin": cfg.roi_y_min, "ymax": cfg.roi_y_max},
                })
            elif self.path == "/settings":
                self._send(SETTINGS_PAGE, "text/html; charset=utf-8")
            elif self.path in ("/", "/index.html"):
                self._send(PAGE, "text/html; charset=utf-8")
            else:
                self.send_error(404)

        def do_POST(self):                     # noqa: N802 - http.server's name
            try:
                body = self._body()
                if self.path == "/settings/apply":
                    result = control.apply(body.get("profile"),
                                           bool(body.get("unlock_height_max")))
                    self._json(result)
                elif self.path == "/settings/undo":
                    self._json(control.undo())
                elif self.path == "/settings/reset":
                    self._json(control.reset())
                elif self.path == "/actions/lights-only":
                    self._json({"enabled": control.set_lights_only(body.get("enabled"))})
                elif self.path == "/actions/test-jet":
                    control.test_jet(body.get("jet"))
                    self._json({"sent": True})
                elif self.path == "/actions/all-off":
                    self._json({"all_zero": control.all_off()})
                else:
                    self._json({"error": "unknown action"}, 404)
            except (ValueError, PermissionError, RuntimeError) as exc:
                self._json({"error": str(exc)}, 400)

        def log_message(self, *args):
            pass                                # the tracker owns the console

    return Handler


def serve(state, cfg, control=None):
    """Start the viewer on a daemon thread and return the server."""
    server = ThreadingHTTPServer((cfg.viewer_host, cfg.viewer_port),
                                 make_handler(state, cfg, control))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"viewer: http://water-jets.local:{cfg.viewer_port}/")
    return server
