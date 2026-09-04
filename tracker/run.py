"""Command line for the tracker. Run everything from here.

    python -m tracker.run check
    python -m tracker.run record --seconds 30 --out data/empty-room.jsonl
    python -m tracker.run baseline --scan data/empty-room.jsonl --out data/baseline.json
    python -m tracker.run live --baseline data/baseline.json
    python -m tracker.run replay data/two-walkers.jsonl --baseline data/baseline.json
"""

import argparse
import os
import sys
import time

from tracker import geometry, scanfile, viewer
from tracker.config import Config
from tracker.tracking import Tracker


def _load_config(args):
    cfg = Config.load(args.config) if args.config else Config()
    if getattr(args, "port", None):
        cfg.port = args.port
    if getattr(args, "viewer_port", None):
        cfg.viewer_port = args.viewer_port
    return cfg


def _lidar_source(cfg):
    from tracker.lidar import Lidar
    lidar = Lidar(cfg).connect()
    return lidar, lidar.scans()


# --- subcommands --------------------------------------------------------

def cmd_check(args):
    from tracker.lidar import health_check
    cfg = _load_config(args)
    if args.pwm:
        cfg.motor_pwm = args.pwm
    health_check(cfg, seconds=args.seconds)
    return 0


def cmd_record(args):
    cfg = _load_config(args)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    lidar, source = _lidar_source(cfg)
    try:
        scanfile.record(source, args.out, args.seconds, notes=args.notes)
    finally:
        lidar.close()
    return 0


def cmd_baseline(args):
    cfg = _load_config(args)
    if args.percentile is not None:
        cfg.background_percentile = args.percentile
    baseline = scanfile.build_baseline(args.scan, cfg)
    scanfile.save_baseline(baseline, args.out)
    return 0


def _track_loop(source, cfg, baseline, label):
    state = viewer.State()
    server = viewer.serve(state, cfg)
    tracker = Tracker(cfg)

    scans = 0
    started = None                      # starts on the first scan, not on spin-up
    last_print = time.time()
    try:
        for timestamp, points in source:
            if started is None:
                started = time.time()
            foreground, background = geometry.to_world(points, cfg, baseline)
            frame = tracker.update(timestamp, foreground)
            scans += 1
            elapsed = max(1e-6, time.time() - started)
            frame["fg"] = [[round(x, 4), round(y, 4)] for x, y in foreground]
            frame["bg"] = [[round(x, 4), round(y, 4)] for x, y in background]
            frame["hz"] = scans / elapsed
            frame["source"] = label
            state.set(frame)

            if time.time() - last_print >= 1.0:
                last_print = time.time()
                confirmed = [t for t in frame["tracks"] if t["confirmed"]]
                summary = "  ".join(
                    f"#{t['id']} s={t['s']:.2f} v={t['speed']:.2f}" for t in confirmed)
                print(f"\r{scans / elapsed:5.2f} Hz  fg={len(foreground):4d}  "
                      f"legs={len(frame['legs']):2d}  tracks={len(frame['tracks'])}  "
                      f"{summary}      ", end="", flush=True)
    except KeyboardInterrupt:
        print("\nstopping")
    finally:
        server.shutdown()
    return 0


def cmd_live(args):
    cfg = _load_config(args)
    baseline = scanfile.load_baseline(args.baseline) if args.baseline else None
    if baseline is None:
        print("live: no baseline, so the walls will look like people "
              "(run 'record' then 'baseline' first)", file=sys.stderr)
    lidar, source = _lidar_source(cfg)
    try:
        return _track_loop(source, cfg, baseline, "lidar")
    finally:
        lidar.close()


def cmd_replay(args):
    cfg = _load_config(args)
    baseline = scanfile.load_baseline(args.baseline) if args.baseline else None
    source = scanfile.replay(args.scan, speed=args.speed, loop=args.loop)
    return _track_loop(source, cfg, baseline, os.path.basename(args.scan))


def cmd_merge(args):
    """Two one-person clips -> one two-person clip. See tracker/merge.py."""
    from tracker import merge as merge_module
    shifts = [0.0, args.shift_b]
    merge_module.merge_files([args.scan_a, args.scan_b], args.out, shifts)
    report = merge_module.crossing_report(args.out, _load_config(args))
    if report:
        print(f"  two tracks held for {report['both']} of {report['scans']} scans, "
              f"most at once {report['most']}")
        if report["closest"] is not None:
            print(f"  they passed within {report['closest']:.2f} m "
                  f"at {report['when']:.1f}s into the clip")
        else:
            print("  they never overlap - try a different --shift-b")
    return 0


def cmd_offline(args):
    """Replay with no viewer and no waiting. Prints a summary. For quick checks."""
    cfg = _load_config(args)
    baseline = scanfile.load_baseline(args.baseline) if args.baseline else None
    tracker = Tracker(cfg)
    scans = 0
    foreground_total = 0
    confirmed_ids = set()
    for timestamp, points in scanfile.read(args.scan):
        foreground, _ = geometry.to_world(points, cfg, baseline)
        frame = tracker.update(timestamp, foreground)
        scans += 1
        foreground_total += len(foreground)
        for track in frame["tracks"]:
            if track["confirmed"]:
                confirmed_ids.add(track["id"])
    per_scan = foreground_total / scans if scans else 0
    print(f"{args.scan}: {scans} scans, "
          f"{len(confirmed_ids)} confirmed tracks {sorted(confirmed_ids)}")
    # The direct measure of whether the baseline swallowed somebody. It does not go
    # through the tracker's confirmation rules, so it cannot be confused by them.
    print(f"  moving points per scan: {per_scan:.1f}")
    return 0


# --- argument parsing ---------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(prog="tracker.run", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", help="JSON file of Config overrides")
    parser.add_argument("--port", help="serial port, default /dev/ttyLIDAR")
    parser.add_argument("--viewer-port", type=int, dest="viewer_port")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="spin up and report the scan rate")
    check.add_argument("--seconds", type=float, default=6.0)
    check.add_argument("--pwm", type=int, help="override motor_pwm for this run")
    check.set_defaults(func=cmd_check)

    record = subparsers.add_parser("record", help="save scans to a file")
    record.add_argument("--seconds", type=float, default=30.0)
    record.add_argument("--out", required=True)
    record.add_argument("--notes", default="")
    record.set_defaults(func=cmd_record)

    baseline = subparsers.add_parser("baseline", help="build the empty-room baseline")
    baseline.add_argument("--scan", required=True)
    baseline.add_argument("--out", required=True)
    baseline.add_argument("--percentile", type=float,
                          help="0.0 is the nearest return and needs a room with "
                               "nobody in it; higher ignores anybody who spends "
                               "less than that share of the clip on one bearing")
    baseline.set_defaults(func=cmd_baseline)

    live = subparsers.add_parser("live", help="track from the LiDAR, with the viewer")
    live.add_argument("--baseline")
    live.set_defaults(func=cmd_live)

    replay = subparsers.add_parser("replay", help="track from a file, with the viewer")
    replay.add_argument("scan")
    replay.add_argument("--baseline")
    replay.add_argument("--speed", type=float, default=1.0)
    replay.add_argument("--loop", action="store_true")
    replay.set_defaults(func=cmd_replay)

    merge = subparsers.add_parser(
        "merge", help="build a two-person clip from two one-person clips")
    merge.add_argument("scan_a")
    merge.add_argument("scan_b")
    merge.add_argument("--shift-b", type=float, default=0.0, dest="shift_b",
                       help="slide clip B by this many seconds; this is what "
                            "decides where the two walkers cross")
    merge.add_argument("--out", required=True)
    merge.set_defaults(func=cmd_merge)

    offline = subparsers.add_parser("offline", help="replay fast, no viewer, summary only")
    offline.add_argument("scan")
    offline.add_argument("--baseline")
    offline.set_defaults(func=cmd_offline)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
