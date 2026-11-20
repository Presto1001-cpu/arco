#!/usr/bin/env python3
"""
Pick frames to hand-label, balanced across slow / medium / fast moments, and write a manifest for label.html.

  python handbench.py clip.mp4 --fps 30 --save-landmarks --out out
  python make_label_manifest.py out/clip_mediapipe_tracking.json clip.mp4 --hand rightmost -n 99 -o manifest.json

Each chosen frame is a square crop around the hand the model found (so you click on a big, clear picture).
If the model's hand is in the wrong place you simply press S ("no hand here"), which counts as a miss.
"""
import argparse, json, math, os, random
import handbench as hb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bench_json"); ap.add_argument("video")
    ap.add_argument("--hand", default="rightmost", choices=["rightmost", "leftmost", "largest", "first"])
    ap.add_argument("-n", type=int, default=99, help="number of frames (split evenly over 3 speed bands)")
    ap.add_argument("--margin", type=float, default=2.0, help="crop size as a multiple of the hand size")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("-o", "--out", default="manifest.json")
    a = ap.parse_args()
    import cv2
    cap = cv2.VideoCapture(a.video); W, H = int(cap.get(3)), int(cap.get(4)); cap.release()
    r = json.load(open(a.bench_json))
    frames = [f for f in r["frames"] if f["motion"] is not None]
    if not frames or "hands" not in frames[0]:
        raise SystemExit("The bench JSON has no landmarks. Run handbench.py with --save-landmarks.")
    edges = hb.band_edges([f["motion"] for f in frames])
    random.seed(a.seed)
    per = a.n // 3
    chosen = []
    for band in range(3):
        pool = [f for f in frames if hb.band_of(f["motion"], edges) == band and f["hands"]]
        random.shuffle(pool)
        # spread across the clip: sort a sample by time
        chosen += [(band, f) for f in sorted(pool[:per], key=lambda f: f["t"])]
    out = []
    for band, f in chosen:
        h = hb.pick_hand(f["hands"], a.hand, W / H)
        xs = [p[0] * W for p in h]; ys = [p[1] * H for p in h]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        side = max(max(xs) - min(xs), max(ys) - min(ys)) * a.margin
        side = max(side, 0.12 * H); side = min(side, H, W)
        x0 = min(max(0, cx - side / 2), W - side); y0 = min(max(0, cy - side / 2), H - side)
        out.append(dict(idx=len(out), i=f["i"], t=f["t"], band=["slow", "medium", "fast"][band],
                        box=[round(x0 / W, 5), round(y0 / H, 5), round((x0 + side) / W, 5), round((y0 + side) / H, 5)]))
    random.shuffle(out)                       # random order so you do not label all fast frames in a row
    for k, f in enumerate(out):
        f["idx"] = k
    man = dict(id=os.path.basename(a.bench_json) + f"-{a.hand}-{a.n}-{a.seed}", video=os.path.basename(a.video),
               hand_rule=a.hand, size=[W, H], frames=out)
    json.dump(man, open(a.out, "w"))
    print(f"{len(out)} frames written to {a.out} (bands: {[sum(1 for f in out if f['band']==b) for b in ('slow','medium','fast')]})")


if __name__ == "__main__":
    main()
