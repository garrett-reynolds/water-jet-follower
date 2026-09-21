"""A web scan viewer, because Raspberry Pi OS Lite has no window to plot in.

Serves one page from the Pi. Open it on a laptop:

    http://water-jets.local:8080/

Standard library only - no Flask, no numpy. The page polls /state and draws a
top-down view: the room, the strip, the raw scan, and the tracks.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from tracker import geometry, system
from tracker.config import Config
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
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>water-jet tracker</title>
<style>
  body { margin:0; background:#111; color:#ddd; font:13px/1.4 monospace; }
  #hud { position:fixed; top:8px; left:8px; background:#000a; padding:8px 10px;
         border:1px solid #333; white-space:pre; }
  #position { position:fixed; top:8px; right:8px; background:#000e; color:#fff;
              padding:10px 16px; border:2px solid #0f6; font:bold 48px/1.15 monospace;
              white-space:pre; text-align:right; }
  /* The big readout is the thing people read from across the room, so a dead
     link must look dead. Stale numbers would pass for live ones. */
  #position.stale { color:#666; border-color:#f44; }
  canvas { display:block; }
  nav { position:fixed; right:12px; bottom:12px; display:flex; gap:8px; }
  nav a { color:#fff; background:#126b72; padding:10px 14px; text-decoration:none;
          border-radius:4px; }
  nav a:focus-visible { outline:3px solid #f3b61f; outline-offset:2px; }
  @media (max-width:600px) {
    #position { font-size:32px; }
    #hud { top:148px; max-width:calc(100vw - 16px); overflow:hidden; text-overflow:ellipsis; }
  }
</style></head><body>
<div id="hud">connecting...</div>
<div id="position">x=--\ny=--\njet=--</div>
<nav><a href="/test">Test jets</a><a id="settings-link" href="/settings">Settings</a><a href="/system">System</a></nav>
<canvas id="c"></canvas>
<script>
let CFG = null, FRAME = null, polls = 0;

function fit() {
  const c = document.getElementById('c');
  c.width = window.innerWidth; c.height = window.innerHeight;
}
window.addEventListener('resize', () => { fit(); draw(); });

function transform(c) {
  const pad = 0.25;   // a little room around the active area, so its edge is visible
  const x0 = CFG.roi_x_min - pad, y0 = CFG.roi_y_min - pad;
  const w = CFG.roi_x_max - CFG.roi_x_min + pad * 2, h = CFG.roi_y_max - CFG.roi_y_min + pad * 2;
  const scale = Math.min(c.width / w, c.height / h) * 0.92;
  // +x right, +y up
  return {
    scale: scale,
    sx: (x) => (x - x0) * scale + (c.width - w * scale) / 2,
    sy: (y) => c.height - ((y - y0) * scale + (c.height - h * scale) / 2)
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
  // the active area: nothing outside it can put water up
  ctx.strokeStyle = '#555'; ctx.lineWidth = 1; ctx.setLineDash([6, 4]);
  ctx.strokeRect(t.sx(CFG.roi_x_min), t.sy(CFG.roi_y_max),
                 (CFG.roi_x_max - CFG.roi_x_min) * t.scale,
                 (CFG.roi_y_max - CFG.roi_y_min) * t.scale);
  ctx.setLineDash([]);

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
      ctx.fillStyle = '#9ef'; ctx.font = '10px monospace';
      ctx.fillText(h, t.sx(x) - 6, t.sy(y) - 14);
    }
  }
  const peak = H.length ? Math.max.apply(null, H) : 0;

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
    // 0.762 cm per DMX unit, measured; see config.py
    'tallest jet ' + peak + ' / ' + CFG.height_max
      + '  (' + (peak * 0.762).toFixed(1) + ' cm)',
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
  const position = document.getElementById('position');
  position.className = '';
  position.textContent = person
    ? 'x=' + person.x.toFixed(2) + '\\ny=' + person.y.toFixed(2)
      + '\\njet=' + person.jet
    : 'x=--\\ny=--\\njet=--';
}

async function poll() {
  try {
    // Settings edits go live without a restart, so the config is re-read about once a second.
    if (!CFG || polls++ % 15 === 0) CFG = await (await fetch('/config')).json();
    const r = await fetch('/state');
    if (!r.ok) throw Error((await r.json()).error || r.statusText);
    FRAME = await r.json();
    draw();
  } catch (e) {
    document.getElementById('hud').textContent = 'lost the Pi: ' + e;
    const position = document.getElementById('position');
    position.className = 'stale';
    position.textContent = 'x=--\\ny=--\\njet=--';
  }
  setTimeout(poll, 66);
}
fit(); poll();
</script></body></html>
"""


# The settings and test pages share one look. Keep the shared rules here so the
# two pages cannot drift apart.
SHARED_CSS = r"""
:root { --ink:#16353a; --paper:#edf5f3; --panel:#fff; --water:#087e8b;
  --light:#d9fff5; --danger:#b9382f; --line:#b7cbc8; --muted:#587276;
  --warn:#fff3d6; --warn-line:#e6c77a; --bad:#ffe4df; --bad-ink:#7d211b; }
* { box-sizing:border-box; }
html { scrollbar-color:#789b9c var(--paper); }
body { margin:0; color:var(--ink); background:var(--paper);
  font:15px/1.35 "Segoe UI", Arial, sans-serif; }
::selection { background:var(--water); color:white; }
header { display:flex; align-items:center; justify-content:space-between; gap:16px;
  padding:12px 22px; min-height:62px; background:var(--ink); color:white; }
h1 { margin:0; font-size:22px; font-weight:650; }
header nav { display:flex; gap:6px; white-space:nowrap; }
header nav a { color:var(--light); text-decoration:none; padding:8px 12px;
  border:1px solid #3e686c; border-radius:4px; }
header nav a:hover { background:#123f45; }
section { background:var(--panel); border:1px solid var(--line); margin:0 0 14px;
  padding:16px; border-radius:6px; }
h2 { font-size:17px; margin:0 0 12px; }
.grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px 14px; }
label { display:grid; gap:4px; color:var(--muted); font-size:13px; }
input, button, select { font:inherit; }
select { padding:8px; border:1px solid var(--line); border-radius:4px; background:white; color:var(--ink); }
label.slider { grid-column:1 / -1; }
label.slider > span:first-child { display:flex; justify-content:space-between; gap:12px; color:var(--ink); font-size:14px; }
label.slider output { font-weight:650; font-variant-numeric:tabular-nums; white-space:nowrap; }
label.slider output small { font-weight:400; font-size:13px; color:var(--muted); }
input[type=range] { width:100%; height:44px; margin:0; accent-color:var(--water); touch-action:pan-y; }
input[type=checkbox] { width:20px; height:20px; margin:0 6px 0 0; accent-color:var(--water); vertical-align:-5px; }
button, .file { border:1px solid #789b9c; background:white; color:var(--ink);
  border-radius:4px; padding:8px 11px; min-height:40px; cursor:pointer; }
.file { display:inline-flex; align-items:center; font-size:15px; }
button:hover, .file:hover { background:#f2f8f7; }
button.primary { background:var(--water); border-color:var(--water); color:white; font-weight:650; }
button.primary:hover { background:#06707c; }
button.danger { background:var(--danger); border-color:var(--danger); color:white; font-weight:650; }
button.danger:hover { background:#9e2f27; }
button:focus-visible, input:focus-visible, select:focus-visible, a:focus-visible { outline:3px solid #f3b61f; outline-offset:2px; }
.actions { display:flex; flex-wrap:wrap; gap:8px; }
.note { color:var(--muted); font-size:13px; }
.warn { color:var(--ink); background:var(--warn); border:1px solid var(--warn-line); border-radius:4px; padding:10px 12px; }
.status { min-height:40px; padding:10px; background:#dce9e6; border-radius:4px; }
.status.bad { background:var(--bad); color:var(--bad-ink); }
"""

SETTINGS_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Water jet settings</title>
<style>""" + SHARED_CSS + r"""
main { display:grid; grid-template-columns:minmax(360px,1.35fr) minmax(340px,1fr);
  min-height:calc(100vh - 62px); }
.map { position:sticky; top:0; height:calc(100vh - 62px); background:#092f35; }
#path { width:100%; height:100%; display:block; touch-action:none; }
.map-tools { position:absolute; left:16px; bottom:16px; display:flex; gap:8px; flex-wrap:wrap; }
.map-hint { align-self:center; padding:6px 8px; border:1px solid #3e686c; border-radius:5px;
  background:#08272ccc; color:#d7efeb; font-size:13px; }
.map-view { position:absolute; right:16px; top:16px; display:flex; gap:6px; align-items:center;
  padding:6px; border:1px solid #3e686c; border-radius:5px; background:#08272ccc; color:#d7efeb; }
.map-view button { min-width:38px; background:#123f45; border-color:#47777b; color:white; }
#live-state { padding:0 5px; font-size:13px; }
.controls { padding:18px 18px 0; display:flex; flex-direction:column; }
/* The unlock is the one control that can raise water above the cap. It gets its
   own 40 px row, not a corner of the slider label, so wet hands can hit it. */
.lock { grid-column:1 / -1; display:grid; gap:4px; background:#fff6f4; border:1px solid #e9c2bd; border-radius:4px; padding:10px 12px; }
.lock .unlock { display:flex; align-items:center; min-height:40px; color:var(--ink); font-size:14px; cursor:pointer; }
.colour-control { display:grid; grid-template-columns:180px minmax(0,1fr); gap:12px 16px; align-items:center; }
#colour_wheel { width:180px; height:180px; display:block; touch-action:none; cursor:crosshair; }
.colour-sliders { display:grid; gap:4px; }
#swatch { height:36px; border:1px solid var(--line); border-radius:4px; }
.jets { display:grid; grid-template-columns:repeat(auto-fill,minmax(96px,1fr)); gap:6px; }
.jet label { display:flex; align-items:center; gap:4px; min-height:44px; padding:9px 10px;
  border:1px solid var(--line); border-radius:4px; color:var(--ink); font-size:14px; cursor:pointer; }
.jet label:has(input:checked) { background:var(--light); border-color:var(--water); }
/* The stop button and the apply button never leave the screen. A stop you have
   to scroll to is not a stop. */
.bar { position:sticky; bottom:0; margin-top:auto; padding:10px 0 14px; display:grid; gap:8px;
  background:var(--paper); border-top:1px solid var(--line); }
.bar .row { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.bar .status { flex:1 1 120px; min-width:0; }
.bar .row button { flex:0 0 auto; }
.bar.pending #apply { outline:3px solid #f3b61f; outline-offset:2px; }
#test-banner { display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
#test-banner[hidden] { display:none; }
/* On a phone the page is for the sliders and the stop. The map is the laptop's job. */
@media (max-width:850px) {
  main { grid-template-columns:1fr; }
  .map { position:relative; height:38vh; }
  .bar .status { flex-basis:100%; }
  .colour-control { grid-template-columns:1fr; justify-items:center; }
  .colour-sliders { width:100%; }
}
</style></head><body>
<header><h1>Water and light control</h1><nav><a href="/test">Test jets</a><a href="/system">System</a><a href="/">Live viewer</a></nav></header>
<main>
  <div class="map"><canvas id="path"></canvas><div class="map-view">
    <span id="live-state">LiDAR waiting</span><button id="zoom-out" aria-label="Zoom out">−</button>
    <button id="zoom-fit">Fit</button><button id="zoom-in" aria-label="Zoom in">+</button>
  </div><div class="map-tools">
    <button id="add-point">Add point</button><button id="remove-point">Remove point</button>
    <span class="map-hint">Dashed box: the active area. Drag its corners. Only people inside it put water up.</span>
  </div></div>
  <div class="controls">
    <section><h2>Water shape</h2><div class="grid">
      <label class="slider"><span>Jet count <output id="jet_count_out"></output></span><input id="jet_count" type="range" min="1" max="20" step="1"></label>
      <label class="slider"><span>Minimum active height <output id="height_min_out"></output></span><input id="height_min" type="range" min="1" max="255" step="1"></label>
      <label class="slider"><span>Normal hill height <output id="hill_peak_out"></output></span><input id="hill_peak" type="range" min="1" max="255" step="1"></label>
      <div class="lock"><label class="slider"><span>Hard maximum height <output id="height_max_out"></output></span><input id="height_max" type="range" min="1" max="255" step="1" disabled></label>
        <label for="unlock" class="unlock"><input id="unlock" type="checkbox"> Unlock this safety limit</label></div>
      <label class="slider"><span>Hill width in jets <output id="hill_jets_out"></output></span><input id="hill_jets" type="range" min="1" max="20" step="1"></label>
      <label class="slider"><span>Lead time in seconds <output id="lead_seconds_out"></output></span><input id="lead_seconds" type="range" min="0" max="2" step="0.01"></label>
      <label class="slider"><span>Follow response in seconds <output id="follow_response_out"></output></span><input id="follow_response" type="range" min="0" max="5" step="0.01"></label>
      <label><span><input id="reverse_jets" type="checkbox"> Reverse jet order</span></label>
    </div></section>
    <section><h2>Colours</h2>
      <label>Set colour for<select id="colour_mode"><option value="base_colour">Base</option><option value="slow_colour">Slow person</option><option value="fast_colour">Fast person</option><option value="idle_colour">Idle animation</option></select></label>
      <div class="colour-control"><canvas id="colour_wheel" width="180" height="180" aria-label="Colour wheel"></canvas>
        <div class="colour-sliders">
          <label class="slider"><span>Colour level <output id="colour_value_out"></output></span><input id="colour_value" type="range" min="0" max="255" value="255"></label>
          <label class="slider"><span>White level <output id="white_level_out"></output></span><input id="white_level" type="range" min="0" max="255" value="0"></label>
          <div id="swatch" role="img" aria-label="The colour as chosen"></div>
        </div>
      </div>
      <div class="grid" style="margin-top:10px">
        <label class="slider"><span>Slow speed in m/s <output id="slow_speed_out"></output></span><input id="slow_speed" type="range" min="0" max="4" step="0.05"></label>
        <label class="slider"><span>Fast speed in m/s <output id="fast_speed_out"></output></span><input id="fast_speed" type="range" min="0" max="4" step="0.05"></label>
      </div></section>
    <section><h2>Idle animations</h2><div class="grid">
      <label>Water<select id="idle_water_animation"><option value="off">Off</option><option value="roll">Roll</option><option value="ripple">Ripple</option><option value="pulse">Pulse</option></select></label>
      <label>Colour<select id="idle_colour_animation"><option value="off">Off</option><option value="chase">Chase</option><option value="fade">Fade</option><option value="breathe">Breathe</option></select></label>
      <label class="slider"><span>Idle brightness <output id="idle_brightness_out"></output></span><input id="idle_brightness" type="range" min="0" max="255" step="1"></label>
      <label class="slider"><span>Cycle time in seconds <output id="idle_seconds_out"></output></span><input id="idle_seconds" type="range" min="0.5" max="120" step="0.5"></label>
      <label class="slider"><span>Idle water height <output id="idle_height_out"></output></span><input id="idle_height" type="range" min="1" max="255" step="1"></label>
    </div></section>
    <section><h2>Jet enable</h2><div class="jets" id="jets"></div></section>
    <section><h2>Profile</h2><p class="note">Edits go live as you make them. The hard maximum, Load JSON, and Reset defaults wait for Apply profile. Reboot and shut down are on the <a href="/system">System</a> page.</p>
      <div class="actions"><button id="undo">Undo applied</button><button id="reset">Reset defaults</button>
      <button id="save">Save JSON</button><label class="file">Load JSON<input id="load" type="file" accept="application/json" hidden></label></div>
    </section>
    <div class="bar" id="bar">
      <div id="test-banner" class="warn" hidden>Test mode is on. The live show is not sending. <button id="resume-live">Resume live show</button></div>
      <div class="row"><div id="status" class="status" aria-live="polite">Loading settings.</div>
        <button id="lights">Lights only: off</button>
        <button id="apply" class="primary">Apply profile</button>
        <button id="all-off" class="danger">ALL OFF</button></div>
    </div>
  </div>
</main>
<script>
let profile, original, defaultProfile, roi, liveFrame=null, selected=0, dragging=false, dragCorner=null, lightsOnly=false, colourMode='base_colour';
let zoom=1, viewCentre=null;
const $=id=>document.getElementById(id);
const fields=['jet_count','height_min','hill_peak','height_max','hill_jets','lead_seconds','follow_response','slow_speed','fast_speed','idle_brightness','idle_seconds','idle_height'];
const heights=['height_min','hill_peak','height_max','idle_height'];
function cm(dmx){return (dmx*0.762).toFixed(1)} // 0.762 cm per DMX unit, measured; see config.py
function status(text,bad=false){$('status').textContent=text;$('status').className=bad?'status bad':'status';}
function copy(v){return JSON.parse(JSON.stringify(v));}
// Amber on Apply when something waits for it: a previewed profile, or a hard maximum that is not yet live.
function markPending(){$('bar').classList.toggle('pending',pending||Number($('height_max').value)!==original.settings.height_max);}
async function api(path,body){const r=await fetch(path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});const data=await r.json();if(!r.ok)throw Error(data.error||r.statusText);return data;}
let wheelHue=0,wheelSat=0,wheelDrag=false;
function hsvToRgb(h,s,v){const i=Math.floor(h*6),f=h*6-i,p=v*(1-s),q=v*(1-f*s),t=v*(1-(1-f)*s);const a=[[v,t,p],[q,v,p],[p,v,t],[p,q,v],[t,p,v],[v,p,q]][i%6];return a.map(x=>Math.round(x*255));}
function rgbToHsv(c){const r=c[0]/255,g=c[1]/255,b=c[2]/255,m=Math.max(r,g,b),n=Math.min(r,g,b),d=m-n;let h=0;if(d){if(m===r)h=((g-b)/d)%6;else if(m===g)h=(b-r)/d+2;else h=(r-g)/d+4;h=(h/6+1)%1}return [h,m?d/m:0,m];}
function drawColourWheel(){const c=$('colour_wheel'),x=c.getContext('2d'),r=c.width/2,img=x.createImageData(c.width,c.height);for(let py=0;py<c.height;py++)for(let px=0;px<c.width;px++){const dx=px-r,dy=py-r,d=Math.hypot(dx,dy),i=(py*c.width+px)*4;if(d<=r){const rgb=hsvToRgb((Math.atan2(dy,dx)/(2*Math.PI)+1)%1,d/r,1);img.data.set([...rgb,255],i)}}x.putImageData(img,0,0);const a=wheelHue*2*Math.PI,rr=wheelSat*r;x.strokeStyle='white';x.lineWidth=3;x.beginPath();x.arc(r+Math.cos(a)*rr,r+Math.sin(a)*rr,6,0,2*Math.PI);x.stroke();x.strokeStyle='#092f35';x.lineWidth=1;x.stroke();}
function swatch(){const rgb=hsvToRgb(wheelHue,wheelSat,Number($('colour_value').value)/255),w=Number($('white_level').value)/255;$('swatch').style.background='rgb('+rgb.map(x=>Math.round(x+(255-x)*w)).join(',')+')';}
function setWheel(e){const c=$('colour_wheel'),b=c.getBoundingClientRect(),r=c.width/2,dx=(e.clientX-b.left)*c.width/b.width-r,dy=(e.clientY-b.top)*c.height/b.height-r;wheelHue=(Math.atan2(dy,dx)/(2*Math.PI)+1)%1;wheelSat=Math.min(1,Math.hypot(dx,dy)/r);drawColourWheel();dirty();}
function saveColour(){const rgb=hsvToRgb(wheelHue,wheelSat,Number($('colour_value').value)/255);profile.settings[colourMode]=[...rgb,Number($('white_level').value)];}
function fillColour(){const c=profile.settings[colourMode],hsv=rgbToHsv(c);wheelHue=hsv[0];wheelSat=hsv[1];$('colour_mode').value=colourMode;$('colour_value').value=Math.round(hsv[2]*255);$('white_level').value=c[3];drawColourWheel();readouts();}
function readForm(){const s=copy(profile.settings);saveColour();for(const n of fields)s[n]=Number($(n).value);s[colourMode]=profile.settings[colourMode];s.idle_water_animation=$('idle_water_animation').value;s.idle_colour_animation=$('idle_colour_animation').value;s.reverse_jets=$('reverse_jets').checked;s.jet_enabled=[...document.querySelectorAll('.jet input')].map(x=>x.checked);profile.settings=s;return profile;}
function readouts(){for(const n of fields){const o=$(n+'_out'),v=$(n).value;if(!o)continue;o.textContent=v;if(heights.includes(n))o.insertAdjacentHTML('beforeend',' <small>'+cm(v)+' cm</small>');}$('colour_value_out').textContent=$('colour_value').value;$('white_level_out').textContent=$('white_level').value;swatch();}
function fill(){const s=profile.settings;for(const n of fields)$(n).value=s[n];$('idle_water_animation').value=s.idle_water_animation;$('idle_colour_animation').value=s.idle_colour_animation;$('reverse_jets').checked=s.reverse_jets;$('height_max').disabled=!$('unlock').checked;$('idle_height').min=s.height_min;$('idle_height').max=s.height_max;$('height_min').max=s.height_max;$('hill_peak').min=s.height_min;$('hill_peak').max=s.height_max;fillColour();buildJets();markPending();draw();status('Edits apply as you make them.');}
function buildJets(){const count=Number($('jet_count').value)||profile.settings.jet_count;let e=profile.settings.jet_enabled||[];while(e.length<count)e.push(true);e=e.slice(0,count);profile.settings.jet_enabled=e;const box=$('jets');box.innerHTML='';e.forEach((on,i)=>box.insertAdjacentHTML('beforeend','<div class="jet"><label><input type="checkbox" '+(on?'checked':'')+'><span>Jet '+(i+1)+'</span></label></div>'));}
function size(){const c=$('path'),r=c.getBoundingClientRect();c.width=r.width*devicePixelRatio;c.height=r.height*devicePixelRatio;draw();}
function bounds(){const cx=viewCentre?viewCentre[0]:(roi.xmin+roi.xmax)/2,cy=viewCentre?viewCentre[1]:(roi.ymin+roi.ymax)/2,hw=(roi.xmax-roi.xmin)/zoom/2,hh=(roi.ymax-roi.ymin)/zoom/2;return {xmin:cx-hw,xmax:cx+hw,ymin:cy-hh,ymax:cy+hh};}
function xy(p){const c=$('path'),v=bounds(),pad=45,w=c.width/devicePixelRatio-pad*2,h=c.height/devicePixelRatio-pad*2;return [pad+(p[0]-v.xmin)/(v.xmax-v.xmin)*w,pad+h-(p[1]-v.ymin)/(v.ymax-v.ymin)*h];}
function world(x,y){const c=$('path'),v=bounds(),pad=45,w=c.width/devicePixelRatio-pad*2,h=c.height/devicePixelRatio-pad*2;return [v.xmin+(x-pad)/w*(v.xmax-v.xmin),v.ymin+(pad+h-y)/h*(v.ymax-v.ymin)];}
function scanDot(ctx,p,r,colour){const q=xy(p);ctx.fillStyle=colour;ctx.beginPath();ctx.arc(q[0],q[1],r,0,Math.PI*2);ctx.fill();}
function jetPoints(points,count){if(count===points.length)return points;const lengths=points.slice(1).map((p,i)=>Math.hypot(p[0]-points[i][0],p[1]-points[i][1])),total=lengths.reduce((a,b)=>a+b,0);if(count<=1||!total)return [points[0]];let segment=0,before=0;return Array.from({length:count},(_,i)=>{const target=total*i/(count-1);while(segment<lengths.length-1&&before+lengths[segment]<target){before+=lengths[segment++]}const a=points[segment],b=points[segment+1],t=lengths[segment]?(target-before)/lengths[segment]:0;return [a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])]});}
function draw(){if(!profile||!roi)return;const c=$('path'),ctx=c.getContext('2d');ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);ctx.fillStyle='#092f35';ctx.fillRect(0,0,c.width,c.height);const v=bounds();ctx.strokeStyle='#17474d';ctx.lineWidth=1;for(let x=Math.ceil(v.xmin*2)/2;x<=v.xmax;x+=.5){const a=xy([x,v.ymin]),b=xy([x,v.ymax]);ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke()}for(let y=Math.ceil(v.ymin*2)/2;y<=v.ymax;y+=.5){const a=xy([v.xmin,y]),b=xy([v.xmax,y]);ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke()}drawArea(ctx);if(liveFrame){for(const p of liveFrame.bg||[])scanDot(ctx,p,1.3,'#527277');for(const p of liveFrame.fg||[])scanDot(ctx,p,2.2,'#45dce7');for(const t of liveFrame.tracks||[])scanDot(ctx,[t.x,t.y],t.confirmed?7:5,t.confirmed?(t.seen?'#0f6':'#f44'):'#888')}scanDot(ctx,[0,0],6,'#fff06a');const pts=profile.settings.strip_points;ctx.strokeStyle='#54d6c1';ctx.lineWidth=3;ctx.beginPath();pts.forEach((p,i)=>{const q=xy(p);i?ctx.lineTo(...q):ctx.moveTo(...q)});ctx.stroke();jetPoints(profile.settings.strip_points,profile.settings.jet_count).forEach((p,i)=>{const q=xy(p);ctx.fillStyle='#45dce7';ctx.beginPath();ctx.arc(...q,4,0,Math.PI*2);ctx.fill();ctx.fillStyle='#fff';ctx.fillText(String(i+1),q[0]+6,q[1]-6)});pts.forEach((p,i)=>{const q=xy(p);ctx.strokeStyle=i===selected?'#f3b61f':'#e9fffa';ctx.lineWidth=2;ctx.strokeRect(q[0]-6,q[1]-6,12,12)});}
function area(){const s=profile.settings;return {xmin:s.roi_x_min,xmax:s.roi_x_max,ymin:s.roi_y_min,ymax:s.roi_y_max};}
function corners(){const a=area();return [[a.xmin,a.ymin],[a.xmax,a.ymin],[a.xmax,a.ymax],[a.xmin,a.ymax]];}
// Outside the active area is ignored, so it is drawn dark. The corners are handles.
function drawArea(ctx){const a=area(),c=$('path'),W=c.width/devicePixelRatio,H=c.height/devicePixelRatio,p=xy([a.xmin,a.ymax]),q=xy([a.xmax,a.ymin]);ctx.fillStyle='rgba(0,0,0,.4)';ctx.fillRect(0,0,W,p[1]);ctx.fillRect(0,q[1],W,H-q[1]);ctx.fillRect(0,p[1],p[0],q[1]-p[1]);ctx.fillRect(q[0],p[1],W-q[0],q[1]-p[1]);ctx.strokeStyle=dragCorner===null?'#e9fffa':'#f3b61f';ctx.lineWidth=2;ctx.setLineDash([8,6]);ctx.strokeRect(p[0],p[1],q[0]-p[0],q[1]-p[1]);ctx.setLineDash([]);corners().forEach((k,i)=>{const r=xy(k);ctx.fillStyle='#092f35';ctx.strokeStyle=i===dragCorner?'#f3b61f':'#e9fffa';ctx.beginPath();ctx.arc(r[0],r[1],7,0,Math.PI*2);ctx.fill();ctx.stroke()});ctx.fillStyle='#e9fffa';ctx.font='13px "Segoe UI",Arial,sans-serif';ctx.fillText('Active area '+(a.xmax-a.xmin).toFixed(2)+' m x '+(a.ymax-a.ymin).toFixed(2)+' m',p[0]+12,p[1]+18);}
function nearestCorner(x,y){let best=null,dist=Infinity;corners().forEach((k,i)=>{const q=xy(k),d=(q[0]-x)**2+(q[1]-y)**2;if(d<dist){dist=d;best=i}});return dist<400?best:null;}
// A corner cannot cross a path point or its opposite edge; the server refuses both, and a refusal every 250 ms mid-drag would be noise.
function moveCorner(i,w){const s=profile.settings,xs=s.strip_points.map(p=>p[0]),ys=s.strip_points.map(p=>p[1]),r=v=>Math.round(v*100)/100;if(i===0||i===3)s.roi_x_min=r(Math.min(w[0],...xs,s.roi_x_max-0.1));else s.roi_x_max=r(Math.max(w[0],...xs,s.roi_x_min+0.1));if(i===0||i===1)s.roi_y_min=r(Math.min(w[1],...ys,s.roi_y_max-0.1));else s.roi_y_max=r(Math.max(w[1],...ys,s.roi_y_min+0.1));}
function clampToArea(p){const a=area();return [Math.min(a.xmax,Math.max(a.xmin,p[0])),Math.min(a.ymax,Math.max(a.ymin,p[1]))];}
function nearest(x,y){let best=0,dist=Infinity;profile.settings.strip_points.forEach((p,i)=>{const q=xy(p),d=(q[0]-x)**2+(q[1]-y)**2;if(d<dist){dist=d;best=i}});return dist<900?best:null;}
let applyTimer=null,pending=false;
function dirty(){readForm();readouts();draw();if(pending){status('Preview only. Press Apply profile to make it live.');return}clearTimeout(applyTimer);applyTimer=setTimeout(autoApply,250);}
async function autoApply(){const p=copy(readForm());p.settings.height_max=original.settings.height_max;try{const r=await api('/settings/apply',{profile:p,unlock_height_max:false});original=copy(r);markPending();status(Number($('height_max').value)!==original.settings.height_max?'Applied. The hard maximum still needs Apply profile.':$('test-banner').hidden?'Applied.':'Applied. Test mode is on, so nothing is sent yet.')}catch(e){status(e.message+' Nothing changed.',true)}}
async function apply(){clearTimeout(applyTimer);try{readForm();profile=await api('/settings/apply',{profile,unlock_height_max:$('unlock').checked});original=copy(profile);$('unlock').checked=false;pending=false;fill();status('Profile applied.');}catch(e){status(e.message,true)}}
function showTestMode(on){$('test-banner').hidden=!on;}
async function init(){try{const data=await api('/settings-data');profile=data.profile;original=copy(profile);defaultProfile=data.default_profile;roi=data.roi;lightsOnly=data.lights_only;fill();$('lights').textContent='Lights only: '+(lightsOnly?'on':'off');showTestMode(data.test_mode);size();}catch(e){status(e.message,true)}}
let linkDown=false;
// Dead looks dead: when the poll fails the scan and the tracks are wiped, not left painted under a small pill.
async function pollState(){try{liveFrame=await api('/state');const count=(liveFrame.fg||[]).length+(liveFrame.bg||[]).length;$('live-state').textContent='LiDAR live · '+count+' points';if(linkDown){linkDown=false;status('LiDAR is back.')}if(typeof liveFrame.test_mode==='boolean')showTestMode(liveFrame.test_mode);draw()}catch(e){$('live-state').textContent='LiDAR not available';if(!linkDown){linkDown=true;liveFrame=null;draw();status('LiDAR not available.',true)}}setTimeout(pollState,100)}
function setZoom(value){zoom=Math.max(1,Math.min(8,value));if(zoom===1)viewCentre=null;else if(profile)viewCentre=profile.settings.strip_points[selected];draw()}
$('unlock').onchange=()=>{$('height_max').disabled=!$('unlock').checked};
$('jet_count').oninput=()=>{const count=Number($('jet_count').value);profile.settings.strip_points=jetPoints(profile.settings.strip_points,count);selected=Math.min(selected,count-1);readForm();buildJets();dirty()};
$('colour_mode').onchange=()=>{saveColour();colourMode=$('colour_mode').value;fillColour();dirty()};
$('colour_value').oninput=dirty;$('white_level').oninput=dirty;
const wheel=$('colour_wheel');wheel.onpointerdown=e=>{wheelDrag=true;wheel.setPointerCapture(e.pointerId);setWheel(e)};wheel.onpointermove=e=>{if(wheelDrag)setWheel(e)};wheel.onpointerup=()=>wheelDrag=false;
document.querySelector('.controls').addEventListener('input',e=>{if(e.target.matches('input[type=range]')){readouts();if(!['jet_count','colour_value','white_level'].includes(e.target.id))dirty()}});
document.querySelector('.controls').addEventListener('change',e=>{if(e.target.matches('input[type=range]'))return;if(e.target.matches('input,select')&&!['load','jet_count','unlock','colour_mode','idle_water_animation','idle_colour_animation'].includes(e.target.id))dirty()});
$('idle_water_animation').onchange=dirty;$('idle_colour_animation').onchange=dirty;
$('apply').onclick=apply;
$('save').onclick=()=>{readForm();const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(profile,null,2)],{type:'application/json'}));a.download='water-jet-profile.json';a.click();URL.revokeObjectURL(a.href)};
$('load').onchange=async e=>{try{profile=JSON.parse(await e.target.files[0].text());pending=true;fill();status('Loaded profile previewed. Press Apply profile to make it live.')}catch(err){status('Could not read that JSON file.',true)}};
$('undo').onclick=async()=>{clearTimeout(applyTimer);try{profile=await api('/settings/undo',{});original=copy(profile);pending=false;fill();status('Last applied profile restored.')}catch(e){status(e.message,true)}};
$('reset').onclick=()=>{profile=copy(defaultProfile);pending=true;fill();status('Default profile previewed. Press Apply profile to make it live.');};
$('lights').onclick=async()=>{try{const d=await api('/actions/lights-only',{enabled:!lightsOnly});lightsOnly=d.enabled;$('lights').textContent='Lights only: '+(lightsOnly?'on':'off');}catch(e){status(e.message,true)}};
$('all-off').onclick=async()=>{try{const d=await api('/actions/all-off',{});showTestMode(true);status(d.all_zero?'ALL OFF verified. All 512 slots are zero. The live show is halted; press Resume live show to continue.':'ALL OFF could not be verified. Cut the 24 V.',!d.all_zero)}catch(e){status(e.message,true)}};
$('resume-live').onclick=async()=>{try{const d=await api('/actions/test-mode',{enabled:false});showTestMode(false);status(d.all_zero===false?'Zero could not be verified. Cut the 24 V.':'Live show resumed.',d.all_zero===false)}catch(e){status(e.message,true)}};
$('zoom-in').onclick=()=>setZoom(zoom*1.5);$('zoom-out').onclick=()=>setZoom(zoom/1.5);$('zoom-fit').onclick=()=>setZoom(1);
$('add-point').onclick=()=>{readForm();const p=profile.settings.strip_points, a=p[Math.max(0,p.length-2)], b=p[p.length-1];p.splice(p.length-1,0,[(a[0]+b[0])/2,(a[1]+b[1])/2]);selected=p.length-2;dirty()};
$('remove-point').onclick=()=>{readForm();if(profile.settings.strip_points.length<=2)return status('The path needs at least two points.',true);profile.settings.strip_points.splice(selected,1);selected=Math.max(0,selected-1);dirty()};
const canvas=$('path');canvas.onwheel=e=>{e.preventDefault();setZoom(e.deltaY<0?zoom*1.2:zoom/1.2)};canvas.onpointerdown=e=>{const r=canvas.getBoundingClientRect();const k=nearestCorner(e.clientX-r.left,e.clientY-r.top);if(k!==null){dragCorner=k;canvas.setPointerCapture(e.pointerId);draw();return}const n=nearest(e.clientX-r.left,e.clientY-r.top);if(n!==null){selected=n;if(zoom>1)viewCentre=profile.settings.strip_points[selected];dragging=true;canvas.setPointerCapture(e.pointerId);draw()}};
canvas.onpointermove=e=>{const r=canvas.getBoundingClientRect();if(dragCorner!==null){moveCorner(dragCorner,world(e.clientX-r.left,e.clientY-r.top));dirty();return}if(!dragging)return;profile.settings.strip_points[selected]=clampToArea(world(e.clientX-r.left,e.clientY-r.top));dirty()};
canvas.onpointerup=()=>{dragging=false;if(dragCorner!==null){dragCorner=null;draw()}};window.onresize=size;init();pollState();
</script></body></html>"""

TEST_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Water jet test</title>
<style>""" + SHARED_CSS + r"""
main { max-width:640px; margin:0 auto; padding:18px 18px 0; min-height:calc(100vh - 62px);
  display:flex; flex-direction:column; }
label.slider output { font-size:20px; }
button { padding:12px 14px; min-height:48px; }
#mode { padding:12px; border-radius:4px; font-weight:650; margin:0 0 14px;
  display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
#mode.on { background:var(--warn); border:1px solid var(--warn-line); }
#mode.off { background:var(--bad); color:var(--bad-ink); border:1px solid #e9b8b0; }
#seen .track.lost { color:var(--muted); font-weight:400; }
#mode .text { flex:1 1 200px; }
#resume[hidden] { display:none; }
/* The stop button and the status line never leave the screen, same as the
   settings bar. A stop you have to scroll to is not a stop. */
.bar { position:sticky; bottom:0; margin-top:auto; padding:10px 0 14px; display:flex; gap:8px;
  align-items:center; flex-wrap:wrap; background:var(--paper); border-top:1px solid var(--line); }
.bar .status { flex:1 1 120px; min-width:0; }
.bar button { flex:0 0 auto; }
#seen { font-size:22px; font-weight:650; }
.warn { margin:0 0 12px; }
</style></head><body>
<header><h1>Water jet test</h1><nav><a href="/settings">Settings</a><a href="/system">System</a><a href="/">Live viewer</a></nav></header>
<main>
  <div id="mode" class="off"><span id="mode-text" class="text">Entering test mode.</span><button id="resume" hidden>Resume live show</button></div>
  <section><h2>Where the tracker sees you</h2>
    <div id="seen">Nobody tracked.</div>
    <p class="note">Jet numbers count from 1, the same as the settings map. Stand on a jet and check the number matches. Tracking stays on in test mode; only the water and lights are off.</p>
  </section>
  <section><h2>Hold one jet</h2>
    <p class="warn">Holds one jet until you press Stop. Keep your hand on the 24 V switch.</p>
    <div class="grid">
      <label class="slider"><span>Jet number <output id="jet_out">1</output></span><input id="jet" type="range" min="1" max="20" step="1" value="1"></label>
      <label class="slider"><span>Height (DMX) <output id="height_out">5</output></span><input id="height" type="range" min="1" max="40" step="1" value="5"></label>
    </div>
    <div class="actions" style="margin-top:12px">
      <button id="start" class="primary">Start test</button>
    </div>
  </section>
  <div class="bar" id="bar">
    <div id="status" class="status" aria-live="polite">Loading.</div>
    <button id="stop" class="danger">Stop test</button>
  </div>
</main>
<script>
const $=id=>document.getElementById(id);
function status(text,bad=false){$('status').textContent=text;$('status').className=bad?'status bad':'status';}
async function api(path,body){const r=await fetch(path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});const data=await r.json();if(!r.ok)throw Error(data.error||r.statusText);return data;}
// One writer for the mode box. `held` is the server's {jet,height} or null; a
// held jet must be readable from across the room, not buried in one status line.
let held=null;
function showMode(on){held=on?held:null;$('mode').className=on?'on':'off';$('mode-text').textContent=on?(held?'TEST MODE. Holding jet '+(held.jet+1)+' at '+held.height+' ('+(held.height*0.762).toFixed(1)+' cm). Stop test to drop it.':'TEST MODE. The live show is not sending.'):'LIVE. The show is sending. Water can move.';$('resume').hidden=!on;}
// 0.762 cm per DMX unit, measured; see config.py
function showHeight(){const v=$('height').value;$('height_out').textContent=v;$('height_out').insertAdjacentHTML('beforeend',' <small>'+(v*0.762).toFixed(1)+' cm</small>');}
async function enter(){try{const d=await api('/actions/test-mode',{enabled:true});showMode(true);status(d.all_zero===false?'Test mode is on but zero could not be verified. Cut the 24 V.':'Test mode is on. All 512 slots are zero.',d.all_zero===false)}catch(e){status(e.message,true)}}
async function start(){const jet=Number($('jet').value)-1,height=Number($('height').value);try{const d=await api('/actions/test-jet',{jet,height});held=d.held;showMode(true);status('Holding jet '+(jet+1)+' at height '+height+'. Press Stop test.')}catch(e){status(e.message,true)}}
async function stop(){try{const d=await api('/actions/all-off',{});held=null;showMode(true);status(d.all_zero?'Stopped. All 512 slots are zero.':'Stop could not be verified. Cut the 24 V.',!d.all_zero)}catch(e){status(e.message,true)}}
async function resume(){try{const d=await api('/actions/test-mode',{enabled:false});showMode(false);status(d.all_zero===false?'Zero could not be verified. Cut the 24 V.':'Live show resumed. Water can move.',d.all_zero===false)}catch(e){status(e.message,true)}}
// jet_position, not the clamped jet: someone past the end of the strip must not
// read as the last jet. See run.py's console line for the same rule.
function jetLabel(x){const p=x.jet_position,n=Number($('jet').max)||1;return p<-0.5||p>n-0.5?'Past the end':'Jet '+(Math.round(p)+1);}
// A track the LiDAR did not see this scan is coasting on its last velocity. It
// renders muted with "(lost)" so a stale position never passes for a live one.
function trackHtml(x){const lost=!x.seen;return '<span class="track'+(lost?' lost':'')+'">'+jetLabel(x)+' (s='+x.s.toFixed(2)+' m)'+(lost?' (lost)':'')+'</span>';}
async function poll(){try{const f=await api('/state');const t=(f.tracks||[]).filter(t=>t.confirmed);$('seen').innerHTML=t.length?t.map(trackHtml).join(' · '):'Nobody tracked.';if(typeof f.test_mode==='boolean'){held=f.held||null;showMode(f.test_mode);}}catch(e){$('seen').textContent='LiDAR not available.'}setTimeout(poll,200)}
$('jet').oninput=()=>$('jet_out').textContent=$('jet').value;$('height').oninput=showHeight;
async function limits(){try{const s=(await api('/settings-data')).profile.settings;$('jet').max=s.jet_count;$('height').min=s.height_min;$('height').max=s.height_max;if(Number($('height').value)<s.height_min)$('height').value=s.height_min;showHeight()}catch(e){}}
$('start').onclick=start;$('stop').onclick=stop;$('resume').onclick=resume;
enter();limits();showHeight();poll();
</script></body></html>
"""


SYSTEM_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Water jet system</title>
<style>""" + SHARED_CSS + r"""
main { max-width:640px; margin:0 auto; padding:18px 18px 0; min-height:calc(100vh - 62px);
  display:flex; flex-direction:column; }
button { padding:12px 14px; min-height:48px; }
/* Readouts: label on the left in Muted, value on the right in Ink, one row each. */
dl { display:grid; grid-template-columns:minmax(120px,auto) 1fr; gap:6px 14px; margin:0; }
dt { color:var(--muted); }
dd { margin:0; font-weight:650; overflow-wrap:anywhere; }
dd.bad { color:var(--bad-ink); }
main.dead dd { color:var(--muted); font-weight:400; }
.bar { position:sticky; bottom:0; margin-top:auto; padding:10px 0 14px; display:flex; gap:8px;
  align-items:center; flex-wrap:wrap; background:var(--paper); border-top:1px solid var(--line); }
.bar .status { flex:1 1 120px; min-width:0; }
.bar button { flex:0 0 auto; }
.warn { margin:0 0 12px; }
</style></head><body>
<header><h1>Water jet system</h1><nav><a href="/settings">Settings</a><a href="/test">Test jets</a><a href="/">Live viewer</a></nav></header>
<main id="main">
  <div id="test-banner" class="warn" hidden>Test mode is on. The live show is not sending. <button id="resume-live">Resume live show</button></div>
  <section><h2>Raspberry Pi</h2><dl id="pi"></dl></section>
  <section><h2>Health</h2><dl id="health"></dl></section>
  <section><h2>Show</h2><dl id="show"></dl></section>
  <section><h2>Power</h2>
    <p class="note">Both zero every slot first and refuse if that cannot be verified. Nothing on the pages is saved, so the profile comes back at its defaults. After a reboot the show does not start on its own.</p>
    <div class="actions"><button id="reboot">Reboot Pi</button><button id="shutdown">Shut down Pi</button></div>
  </section>
  <div class="bar" id="bar">
    <div id="status" class="status" aria-live="polite">Loading.</div>
    <button id="all-off" class="danger">ALL OFF</button>
  </div>
</main>
<script>
const $=id=>document.getElementById(id);
function status(text,bad=false){$('status').textContent=text;$('status').className=bad?'status bad':'status';}
async function api(path,body){const r=await fetch(path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});const data=await r.json();if(!r.ok)throw Error(data.error||r.statusText);return data;}
function showTestMode(on){$('test-banner').hidden=!on;}
function span(s){if(s==null)return '—';const d=Math.floor(s/86400),h=Math.floor(s%86400/3600),m=Math.floor(s%3600/60);return (d?d+' d ':'')+(d||h?h+' h ':'')+m+' min';}
// Each row is [label, value, bad?]. A null value reads as a dash: the laptop has no /proc/device-tree.
function rows(id,list){$(id).innerHTML=list.map(([k,v,bad])=>'<dt>'+k+'</dt><dd'+(bad?' class="bad"':'')+'>'+(v==null?'—':v)+'</dd>').join('');}
function render(d){const p=d.pi,h=d.health,s=d.show,t=h.throttled,mem=h.memory,disk=h.disk;
  rows('pi',[['Hostname',p.hostname],['Model',p.model],['OS',p.os+' · '+p.kernel],['Addresses',p.addresses.join(', ')||null],['Clock',p.clock],['Up for',span(p.uptime_seconds)]]);
  rows('health',[['CPU temperature',h.cpu_temp_c==null?null:h.cpu_temp_c+' °C',h.cpu_temp_c>=80],
    ['Power supply',t==null?null:t.under_voltage_now?'UNDER-VOLTAGE NOW':t.under_voltage_ever?'ok now, under-voltage since boot':'ok',t&&(t.under_voltage_now||t.under_voltage_ever)],
    ['Throttling',t==null?null:t.throttled_now?'THROTTLED NOW':t.throttled_ever?'ok now, throttled since boot':'none',t&&(t.throttled_now||t.throttled_ever)],
    ['Load (1, 5, 15 min)',h.load?h.load.map(v=>v.toFixed(2)).join('  '):null,h.load&&h.load[0]>3],
    ['Memory',mem?mem.used_mib+' of '+mem.total_mib+' MiB used':null],
    ['Disk',disk?disk.used_gib+' of '+disk.total_gib+' GiB used':null,disk&&disk.total_gib-disk.used_gib<1]]);
  rows('show',[['Mode',s.test_mode?'TEST MODE, not sending':s.lights_only?'Live, lights only':'LIVE, water can move'],['LiDAR',s.lidar_ok?'ok, '+s.scan_hz+' Hz':'NOT AVAILABLE',!s.lidar_ok],['OLA (olad)',s.olad_active==null?null:s.olad_active?'running':'NOT RUNNING',s.olad_active===false],['Source',s.source],['Show running for',span(s.running_seconds)],['Process',s.pid+' · Python '+s.python],['Power control',s.power_available?'available':'not in this run mode']]);
  showTestMode(s.test_mode);}
let linkDown=false, powering=null;
// Dead looks dead: when the poll fails every readout goes Muted, and the last numbers do not pass for live ones.
async function poll(){if(powering)return;try{render(await api('/system-data'));$('main').classList.remove('dead');if(linkDown){linkDown=false;status('Pi is back.')}}catch(e){$('main').classList.add('dead');if(!linkDown){linkDown=true;status('Pi not reachable.',true)}}setTimeout(poll,2000)}
const POWER={reboot:{ask:'Reboot the Pi? The show stops, and it does not start again on its own.',done:'Rebooting. Reload this page in about a minute. The show is not running until it is started again.'},
             shutdown:{ask:'Shut down the Pi? The show stops. Cut the power once the green LED is out.',done:'Shutting down. Wait for the green LED to go out, then cut the power.'}};
async function power(action){if(!confirm(POWER[action].ask))return;$('reboot').disabled=$('shutdown').disabled=true;try{await api('/actions/'+action,{});powering=action;showTestMode(true);$('main').classList.add('dead');status(POWER[action].done)}catch(e){$('reboot').disabled=$('shutdown').disabled=false;status(e.message,true)}}
$('reboot').onclick=()=>power('reboot');$('shutdown').onclick=()=>power('shutdown');
$('all-off').onclick=async()=>{try{const d=await api('/actions/all-off',{});showTestMode(true);status(d.all_zero?'ALL OFF verified. All 512 slots are zero. The live show is halted; press Resume live show to continue.':'ALL OFF could not be verified. Cut the 24 V.',!d.all_zero)}catch(e){status(e.message,true)}};
$('resume-live').onclick=async()=>{try{const d=await api('/actions/test-mode',{enabled:false});showTestMode(false);status(d.all_zero===false?'Zero could not be verified. Cut the 24 V.':'Live show resumed.',d.all_zero===false)}catch(e){status(e.message,true)}};
poll();
</script></body></html>
"""


def make_handler(state, cfg, control=None):
    view = Config()
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
                frame = state.get()
                if frame.get("lidar_ok") is False:
                    # Dead looks dead: a failed poll is what every page already
                    # handles, so the loss shows without the last frame lingering.
                    self._json({"error": "LiDAR not available"}, 503)
                else:
                    # The control's truth rides along so a reloaded test page
                    # shows a held jet instead of a calm banner.
                    frame = dict(frame, test_mode=control.test_mode, held=control.held)
                    self._send(json.dumps(frame), "application/json")
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
                    "test_mode": control.test_mode,
                    # The map's view frame. Built from the defaults and padded,
                    # not from the live area: a shrunken active area must still
                    # leave room on the map to drag its corners back out.
                    "roi": {"xmin": view.roi_x_min - 1, "xmax": view.roi_x_max + 1,
                            "ymin": view.roi_y_min - 1, "ymax": view.roi_y_max + 1},
                })
            elif self.path == "/settings":
                self._send(SETTINGS_PAGE, "text/html; charset=utf-8")
            elif self.path == "/test":
                self._send(TEST_PAGE, "text/html; charset=utf-8")
            elif self.path == "/system":
                self._send(SYSTEM_PAGE, "text/html; charset=utf-8")
            elif self.path == "/system-data":
                self._json(system.snapshot(state, control))
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
                elif self.path == "/actions/test-mode":
                    self._json(control.set_test_mode(body.get("enabled")))
                elif self.path == "/actions/test-jet":
                    held = control.test_jet(body.get("jet"), body.get("height"))
                    self._json({"sent": True, "held": held})
                elif self.path == "/actions/all-off":
                    self._json({"all_zero": control.all_off()})
                elif self.path in ("/actions/reboot", "/actions/shutdown"):
                    self._json(control.power(self.path.rsplit("/", 1)[1]))
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
