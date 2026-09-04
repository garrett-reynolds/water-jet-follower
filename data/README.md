# data

Scan recordings and the baselines built from them.

`*.jsonl` recordings are **not** in git — they are megabytes each and they live on
the Pi under `~/data/`. `*.json` baselines are small and are kept, because they are
what the tracker needs to tell a person from a wall.

## Rebuild a baseline

On the Pi, with nobody in the room and the sensor where it will live:

```
ssh pi@water-jets.local
~/wj-venv/bin/python -m tracker.run record --seconds 30 --out data/empty-room.jsonl --notes "empty room"
~/wj-venv/bin/python -m tracker.run baseline --scan data/empty-room.jsonl --out data/baseline.json
```

Copy it back to the laptop with:

```
scp pi@water-jets.local:~/data/baseline.json "C:/Users/garrett.reynolds/Projects/Personal/Electronics/water-jet-follower/data/"
```

## What is here

| File | From |
|---|---|
| `bench-baseline.json` | 20 s of the still bench, 2026-09-04, PWM 800. 281 of 360 bins filled. |
| `room-baseline.json` | 60 s of the real room with Garrett walking in it, 2026-09-04. 360 of 360 bins filled. Went stale within minutes — see `DECISIONS.md`. |
| `walk-rl-baseline.json` | The right-to-left walk clip, 2026-09-04. 360 of 360 bins. This is the one to score standing clips against. |

On the Pi there are two matching recordings, `~/data/bench-empty.jsonl` and
`~/data/bench-empty-2.jsonl`. The second one exists so the baseline can be scored
against a clip it was not built from. Scoring a baseline against its own recording
proves nothing — every point is background by construction.
