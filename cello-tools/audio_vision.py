#!/usr/bin/env python3
"""
Does the hand position the camera sees agree with the position the sound says?

  python handbench.py clip.mp4 --fps 30 --save-landmarks --out out
  ffmpeg -i clip.mov -vn -ac 1 -ar 44100 clip.wav
  python audio_vision.py out/clip_mediapipe_tracking.json clip.wav --hand rightmost

For each analysed frame the pitch is found in the sound, turned into a distance along the string, and compared with the
fingertip position in the picture (least squares plane fit). A shifted-sound control shows what chance looks like.
It guesses the string from the pitch (highest open string at or below the note), so it is a consistency check, not a measurement.
"""
import argparse, json, math, wave
import numpy as np
import handbench as hb

STRINGS = [("C", 65.406), ("G", 97.999), ("D", 146.832), ("A", 220.0)]


def yin(buf, sr, fmin=60, fmax=1100, thr=0.12):
    n = len(buf) // 2; tmax = int(sr / fmin); tmin = int(sr / fmax)
    if n < tmax: return None, 1.0
    d = np.zeros(tmax + 1)
    for tau in range(1, tmax + 1):
        diff = buf[:n] - buf[tau:tau + n]; d[tau] = np.dot(diff, diff)
    cm = np.ones_like(d); cm[1:] = d[1:] * np.arange(1, tmax + 1) / np.maximum(np.cumsum(d[1:]), 1e-12)
    tau = None
    for t in range(tmin, tmax):
        if cm[t] < thr:
            while t + 1 < tmax and cm[t + 1] < cm[t]: t += 1
            tau = t; break
    if tau is None: return None, 1.0
    a, b, c = cm[tau - 1], cm[tau], cm[min(tau + 1, tmax)]
    den = a - 2 * b + c
    return sr / (tau + (0.5 * (a - c) / den if den else 0)), float(cm[tau])


def pitch_at(x, sr, times, win=2048):
    out = []; extra = int(sr / 60)
    for t in times:
        a = int(t * sr) - win // 2
        if a < 0 or a + win + extra > len(x): out.append(None); continue
        seg = x[a:a + win + extra]
        if np.sqrt((seg ** 2).mean()) < 0.01: out.append(None); continue
        f, c = yin(seg, sr); out.append(f if f and c < 0.15 else None)
    return out


def stop_mm(freq, L=690.0, a4=440.0):
    pick = None
    for n, f0 in STRINGS:
        f0 = f0 * a4 / 440
        if f0 <= freq * 1.012: pick = (n, f0)
    if pick is None: return None
    s = 12 * math.log2(freq / pick[1]); return L * (1 - 2 ** (-s / 12))


def fit(X, Y):
    X = np.column_stack([X, np.ones(len(X))]); c = np.linalg.lstsq(X, Y, rcond=None)[0]; p = X @ c
    sst = ((Y - Y.mean()) ** 2).sum(); return 1 - ((Y - p) ** 2).sum() / sst, float(np.sqrt(((Y - p) ** 2).mean()))


def agreement(bench, pitches, rule="rightmost", joint=8, L=690.0):
    W, H = bench["size"]; asp = W / H; X = []; Y = []; band = []
    edges = hb.band_edges([f["motion"] for f in bench["frames"] if f["motion"] is not None])
    for f, hz in zip(bench["frames"], pitches):
        if not hz or not f["hands"]: continue
        mm = stop_mm(hz, L)
        if mm is None: continue
        h = hb.pick_hand(f["hands"], rule, asp)
        X.append([h[joint][0] * asp, h[joint][1]]); Y.append(mm)
        band.append(-1 if f["motion"] is None else hb.band_of(f["motion"], edges))
    X = np.array(X); Y = np.array(Y); band = np.array(band)
    if len(Y) < 40: return dict(n=len(Y), enough=False)
    r2, rms = fit(X, Y); n = len(Y)
    control = float(np.mean([fit(X, np.roll(Y, int(n * k)))[0] for k in (.25, .5, .75)]))
    per = {}
    for b, name in enumerate(["slow", "medium", "fast"]):
        m = band == b
        if m.sum() >= 30: per[name] = dict(n=int(m.sum()), r2=fit(X[m], Y[m])[0])
    return dict(n=n, enough=True, r2=r2, rms_mm=rms, control=control, agrees=r2 > control + 0.1, by_speed=per)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("bench_json"); ap.add_argument("wav")
    ap.add_argument("--hand", default="rightmost", choices=["rightmost", "leftmost", "largest", "first"])
    ap.add_argument("--string-mm", type=float, default=690.0, help="vibrating string length for the cello size")
    a = ap.parse_args()
    w = wave.open(a.wav); sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    bench = json.load(open(a.bench_json)); pitches = pitch_at(x, sr, [f["t"] for f in bench["frames"]])
    r = agreement(bench, pitches, a.hand, 8, a.string_mm)
    print(f"voiced frames: {sum(p is not None for p in pitches)} of {len(pitches)}")
    if not r["enough"]: print(f"Only {r['n']} frames have both a pitch and a hand: too few."); return
    print(f"Hand position explains {100*r['r2']:.0f}% of pitch-derived finger position (shifted-sound control {100*r['control']:.0f}%), typical gap {r['rms_mm']:.0f} mm")
    print("agreement:", "yes" if r["agrees"] else "no clear agreement")
    for k, v in r["by_speed"].items(): print(f"  {k:7s} n={v['n']:4d}  R2={100*v['r2']:.0f}%")


if __name__ == "__main__":
    main()
