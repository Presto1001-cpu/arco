#!/usr/bin/env python3
"""
Compare hand labels (from label.html) with what the model found.

  python evaluate_labels.py out/clip_mediapipe_tracking.json fingertip-labels.json --hand rightmost

Error is measured in "palm sizes": the distance between your wrist and middle-knuckle clicks.
PCK@0.2 means "within 0.2 palm sizes of where you clicked" (about 1.5 cm on an adult hand).
"""
import argparse, json, math
from collections import defaultdict
import numpy as np
import handbench as hb

MODEL_INDEX = dict(wrist=0, mcp=9, thumb=4, index=8, middle=12, ring=16, little=20)
TIPS = ["thumb", "index", "middle", "ring", "little"]


def evaluate(bench, labels, rule="rightmost"):
    W, H = bench["size"]; aspect = W / H
    F = {f["i"]: f for f in bench["frames"]}
    names = labels["point_names"]
    errs = defaultdict(list)         # (band, joint) -> list of errors in palm sizes
    counts = defaultdict(lambda: defaultdict(int))
    for L in labels["labels"]:
        band = L["band"]; c = counts[band]; c["frames"] += 1
        f = F.get(L["i"])
        model_hand = hb.pick_hand(f["hands"], rule, aspect) if f else None
        if L["skipped"]:
            c["no_hand"] += 1
            if model_hand is not None:
                c["model_found_hand_but_none_there"] += 1
            continue
        c["labelled"] += 1
        if model_hand is None:
            c["model_missed"] += 1
            continue
        pts = {n: p for n, p in zip(names, L["pts"])}
        if pts.get("wrist") is None or pts.get("mcp") is None:
            c["unusable"] += 1; continue
        palm = math.hypot((pts["wrist"][0] - pts["mcp"][0]) * W, (pts["wrist"][1] - pts["mcp"][1]) * H)
        if palm < 1:
            c["unusable"] += 1; continue
        for n in names:
            if pts.get(n) is None:
                c["hidden_" + n] += 1; continue
            m = model_hand[MODEL_INDEX[n]]
            e = math.hypot((m[0] - pts[n][0]) * W, (m[1] - pts[n][1]) * H) / palm
            errs[(band, n)].append(e)
    return errs, counts


def report(errs, counts):
    bands = ["slow", "medium", "fast"]
    print(f"{'band':<8}{'labelled':>9}{'model missed':>13}{'no hand there':>14}{'(model said hand)':>18}")
    for b in bands:
        c = counts[b]
        print(f"{b:<8}{c['labelled']:>9}{c['model_missed']:>13}{c['no_hand']:>14}{c['model_found_hand_but_none_there']:>18}")
    print("\nFingertip error in palm sizes (lower is better), and share within 0.2 palm sizes")
    print(f"{'band':<8}{'mean':>7}{'median':>8}{'within 0.1':>11}{'within 0.2':>11}{'within 0.3':>11}")
    for b in bands + ["all"]:
        e = [x for n in TIPS for bb in (bands if b == "all" else [b]) for x in errs.get((bb, n), [])]
        if e:
            e = np.array(e)
            print(f"{b:<8}{e.mean():>7.2f}{np.median(e):>8.2f}{100*(e<.1).mean():>10.0f}%{100*(e<.2).mean():>10.0f}%{100*(e<.3).mean():>10.0f}%")
    print("\nPer finger, all speeds")
    for n in ["wrist", "mcp"] + TIPS:
        e = [x for b in bands for x in errs.get((b, n), [])]
        if e:
            print(f"  {n:<7} mean {np.mean(e):.2f}  within 0.2: {100*(np.array(e)<.2).mean():.0f}%  (n={len(e)})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bench_json"); ap.add_argument("labels_json")
    ap.add_argument("--hand", default="rightmost", choices=["rightmost", "leftmost", "largest", "first"])
    a = ap.parse_args()
    report(*evaluate(json.load(open(a.bench_json)), json.load(open(a.labels_json)), a.hand))


if __name__ == "__main__":
    main()
