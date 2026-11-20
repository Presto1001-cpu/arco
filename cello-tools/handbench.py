#!/usr/bin/env python3
"""
handbench.py - measure how well hand-tracking models cope with a cellist's left hand.

Same metrics as the "Video test" tab of the web prototype, so results are comparable:
  * Frames are ranked by how much the PICTURE moves (independent of the model) and split
    into thirds: Slow / Medium / Fast.
  * Per third: % of frames where a hand was found, % "unstable" frames (finger length jumped
    sharply versus the previous frame = the model probably guessed), mean confidence.

Backends
  mediapipe  MediaPipe Hands (legacy solutions API, models are bundled in the pip wheel,
             so it works offline). Needs: pip install "mediapipe==0.10.14" "numpy<2" opencv-python-headless
  rtmlib     RTMPose/RTMW whole-body models through rtmlib (downloads models on first use, so it
             needs internet access to download.openmmlab.com). Needs a visible person: it finds
             the body first, so a close-up of only a hand may not be detected. Untested here.

Usage
  python handbench.py clip1.mp4 clip2.mp4 --fps 30 --backend mediapipe --out results
  python handbench.py clip.mp4 --mode static      # every frame detected from scratch (no tracking)
  python handbench.py clip.mp4 --annotate         # also writes an annotated video
"""
import argparse, csv, json, math, os, sys
import numpy as np

# ---------------------------------------------------------------- pure metrics (unit tested)

def motion_energy(a, b):
    """Mean absolute pixel difference between two small RGB/BGR frames (0..255)."""
    return float(np.mean(np.abs(a.astype(np.int16) - b.astype(np.int16))))


def hand_shape(lm, aspect):
    """lm: (21,2) normalised landmarks. Returns (palm_size, index_finger/palm ratio)."""
    def d(i, j):
        return math.hypot((lm[i][0] - lm[j][0]) * aspect, lm[i][1] - lm[j][1])
    palm = d(0, 9) or 1e-6
    return palm, d(5, 8) / palm


def is_jump(prev, cur):
    """True when finger length or palm size changed implausibly fast between frames."""
    if prev is None or cur is None:
        return False
    a = cur[1] / prev[1] if prev[1] else 1.0
    b = cur[0] / prev[0]
    return a > 1.3 or a < 1 / 1.3 or b > 1.35 or b < 1 / 1.35


def band_edges(values):
    v = sorted(x for x in values if x is not None and math.isfinite(x))
    if not v:
        return 0.0, 0.0
    return v[len(v) // 3], v[(2 * len(v)) // 3]


def band_of(m, edges):
    return 0 if m < edges[0] else (1 if m < edges[1] else 2)


def summarize(frames):
    frames = [f for f in frames if f["motion"] is not None]
    edges = band_edges([f["motion"] for f in frames])
    acc = [dict(n=0, det=0, pairs=0, jumps=0, conf=0.0) for _ in range(3)]
    for f in frames:
        b = acc[band_of(f["motion"], edges)]
        b["n"] += 1
        if f["det"]:
            b["det"] += 1
            b["conf"] += f["conf"]
            if f["jump"] is not None:
                b["pairs"] += 1
                b["jumps"] += 1 if f["jump"] else 0
    names = ["Slow", "Medium", "Fast"]
    out = []
    for i, b in enumerate(acc):
        out.append(dict(
            name=names[i], frames=b["n"],
            detected_pct=100 * b["det"] / b["n"] if b["n"] else 0.0,
            unstable_pct=100 * b["jumps"] / b["pairs"] if b["pairs"] else 0.0,
            mean_conf=b["conf"] / b["det"] if b["det"] else 0.0))
    total = len(frames)
    return dict(frames=total, edges=edges,
                detected_pct=100 * sum(1 for f in frames if f["det"]) / total if total else 0.0,
                bands=out)


def verdict(pct):
    return "good" if pct >= 90 else "shaky" if pct >= 70 else "poor"


def pick_hand(hands, rule="rightmost", aspect=1.0):
    """Choose one hand from a list of 21x2 landmark lists. rule: rightmost | leftmost | largest | first.
    Used to follow "the hand on the fingerboard" when two hands are in view (the neck hand is the
    rightmost in a typical front view, the leftmost if the camera is mirrored)."""
    if not hands:
        return None
    if rule == "rightmost":
        return max(hands, key=lambda h: h[0][0])
    if rule == "leftmost":
        return min(hands, key=lambda h: h[0][0])
    if rule == "largest":
        return max(hands, key=lambda h: hand_shape(h, aspect)[0])
    return hands[0]

# ---------------------------------------------------------------- backends

class MediaPipeBackend:
    name = "mediapipe"

    def __init__(self, mode="tracking", complexity=1, conf=0.5, **_ignored):
        import mediapipe as mp
        if not hasattr(mp, "solutions"):
            sys.exit('This MediaPipe has no legacy "solutions" API. Install: pip install "mediapipe==0.10.14" "numpy<2"')
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=(mode == "static"), max_num_hands=2, model_complexity=complexity,
            min_detection_confidence=conf, min_tracking_confidence=conf)

    def detect(self, bgr):
        import cv2
        res = self.hands.process(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        hands = []
        if res.multi_hand_landmarks:
            for lm, hd in zip(res.multi_hand_landmarks, res.multi_handedness):
                hands.append((np.array([[p.x, p.y] for p in lm.landmark]), hd.classification[0].score))
        return hands


class RtmlibBackend:
    name = "rtmlib"

    def __init__(self, rtm_mode="balanced", device="cpu", **_):
        from rtmlib import Wholebody       # modes: performance | balanced | lightweight
        self.model = Wholebody(mode=rtm_mode, backend="onnxruntime", device=device, to_openpose=False)

    def detect(self, bgr):
        h, w = bgr.shape[:2]
        kpts, scores = self.model(bgr)
        hands = []
        for k, s in zip(kpts, scores):          # COCO-WholeBody: 91-111 left hand, 112-132 right hand
            for a, b in ((91, 112), (112, 133)):
                sc = float(np.mean(s[a:b]))
                if sc > 0.5:
                    hands.append((np.array([[x / w, y / h] for x, y in k[a:b]]), sc))
        return hands

BACKENDS = {"mediapipe": MediaPipeBackend, "rtmlib": RtmlibBackend}

# ---------------------------------------------------------------- run

HAND_LINKS = [(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),(10,11),(11,12),
              (9,13),(13,14),(14,15),(15,16),(13,17),(17,18),(18,19),(19,20),(0,17)]


def analyse(path, backend, fps, annotate_to=None, max_seconds=None, save_landmarks=False, start_seconds=0.0):
    import cv2
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise SystemExit(f"Cannot open {path}")
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    step = max(1.0, src_fps / fps)               # take every `step`-th source frame
    writer = None
    if annotate_to:
        writer = cv2.VideoWriter(annotate_to, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
    frames, prev_pix, prev_shape, prev_wrist, nxt, i, k = [], None, None, None, 0.0, 0, 0
    if start_seconds:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(start_seconds * src_fps)); i = int(start_seconds * src_fps); nxt = float(i)
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        if i + 1e-9 >= nxt:
            nxt += step
            t = i / src_fps
            if max_seconds and t > max_seconds:
                break
            pix = cv2.resize(bgr, (96, 54), interpolation=cv2.INTER_AREA)
            motion = motion_energy(prev_pix, pix) if prev_pix is not None else None
            prev_pix = pix
            hands = backend.detect(bgr)
            # Follow the SAME hand from frame to frame (nearest wrist), so that two hands in view
            # swapping places in the list is not mistaken for a glitch.
            best, cont = None, False
            if hands and prev_wrist is not None:
                near = min(hands, key=lambda h: math.hypot(h[0][0][0] - prev_wrist[0], h[0][0][1] - prev_wrist[1]))
                if math.hypot(near[0][0][0] - prev_wrist[0], near[0][0][1] - prev_wrist[1]) < 0.12:
                    best, cont = near, True
            if hands and best is None:
                best = max(hands, key=lambda h: h[1])
            jump = None
            if best:
                shape = hand_shape(best[0], W / H)
                jump = is_jump(prev_shape, shape) if (prev_shape and cont) else None
                prev_shape, prev_wrist = shape, (best[0][0][0], best[0][0][1])
            else:
                prev_shape = prev_wrist = None
            rec = dict(i=k, t=round(t, 3), motion=None if motion is None else round(motion, 3),
                       det=best is not None, conf=round(best[1], 3) if best else 0.0,
                       jump=jump, n_hands=len(hands))
            if save_landmarks:
                rec["hands"] = [np.round(h[0], 4).tolist() for h in hands]
            frames.append(rec)
            if writer:
                for lm, _ in hands:
                    pts = [(int(x * W), int(y * H)) for x, y in lm]
                    for a, b in HAND_LINKS:
                        cv2.line(bgr, pts[a], pts[b], (91, 191, 138), 2)
                    for p in pts:
                        cv2.circle(bgr, p, 3, (233, 169, 106), -1)
                writer.write(bgr)
            k += 1
        i += 1
    cap.release()
    if writer:
        writer.release()
    return dict(file=os.path.basename(path), source_fps=src_fps, analysed_fps=fps, size=[W, H],
                backend=backend.name, frames=frames, summary=summarize(frames))


def report(r):
    s = r["summary"]
    print(f"\n{r['file']}  ({r['backend']}, {r['analysed_fps']} fps analysed, source {r['source_fps']:.0f} fps, {s['frames']} frames)")
    print(f"  hand found overall: {s['detected_pct']:.0f}%")
    print(f"  {'band':<8}{'frames':>7}{'found':>8}{'unstable':>10}{'conf':>7}   verdict")
    for b in s["bands"]:
        print(f"  {b['name']:<8}{b['frames']:>7}{b['detected_pct']:>7.0f}%{b['unstable_pct']:>9.0f}%{b['mean_conf']:>7.2f}   {verdict(b['detected_pct'])}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--backend", choices=BACKENDS, default="mediapipe")
    ap.add_argument("--fps", type=float, default=30, help="analysis rate (default 30)")
    ap.add_argument("--mode", choices=["tracking", "static"], default="tracking",
                    help="mediapipe only: tracking = uses previous frame; static = detect every frame from scratch")
    ap.add_argument("--complexity", type=int, choices=[0, 1], default=1, help="mediapipe model: 0 lite, 1 full")
    ap.add_argument("--out", default="handbench_out", help="folder for CSV/JSON results")
    ap.add_argument("--annotate", action="store_true", help="also write an annotated .mp4 per clip")
    ap.add_argument("--rtm-mode", choices=["performance", "balanced", "lightweight"], default="balanced", help="rtmlib model size")
    ap.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="rtmlib device (cuda needs onnxruntime-gpu)")
    ap.add_argument("--max-seconds", type=float, default=None, help="stop at this time in the clip")
    ap.add_argument("--start-seconds", type=float, default=0.0, help="start at this time in the clip")
    ap.add_argument("--save-landmarks", action="store_true", help="store all 21 points per hand in the JSON")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    backend = BACKENDS[a.backend](mode=a.mode, complexity=a.complexity, rtm_mode=a.rtm_mode, device=a.device)
    for v in a.videos:
        stem = os.path.splitext(os.path.basename(v))[0] + f"_{a.backend}_{a.mode}"
        r = analyse(v, backend, a.fps, os.path.join(a.out, stem + "_annotated.mp4") if a.annotate else None, a.max_seconds,
                    a.save_landmarks, a.start_seconds)
        report(r)
        with open(os.path.join(a.out, stem + ".json"), "w") as f:
            json.dump(r, f)
        with open(os.path.join(a.out, stem + ".csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["frame", "time_s", "motion", "hand_found", "confidence", "unstable", "hands"])
            for fr in r["frames"]:
                w.writerow([fr["i"], fr["t"], fr["motion"], int(fr["det"]), fr["conf"],
                            "" if fr["jump"] is None else int(fr["jump"]), fr["n_hands"]])
    print(f"\nResults written to {a.out}/")


if __name__ == "__main__":
    main()
