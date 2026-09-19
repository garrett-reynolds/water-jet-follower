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
</style></head><body>
<div id="hud">connecting...</div>
<div id="position">x=--\ny=--\njet=--</div>
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


def make_handler(state, cfg):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, body, content_type):
            payload = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

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
            elif self.path in ("/", "/index.html"):
                self._send(PAGE, "text/html; charset=utf-8")
            else:
                self.send_error(404)

        def log_message(self, *args):
            pass                                # the tracker owns the console

    return Handler


def serve(state, cfg):
    """Start the viewer on a daemon thread and return the server."""
    server = ThreadingHTTPServer((cfg.viewer_host, cfg.viewer_port),
                                 make_handler(state, cfg))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"viewer: http://water-jets.local:{cfg.viewer_port}/")
    return server
