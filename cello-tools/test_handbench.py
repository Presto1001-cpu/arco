import math, os, sys, tempfile
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
import handbench as hb

# --- metrics (mirror of the JavaScript tests in the web prototype)
lm = np.zeros((21, 2)); lm[9] = (0, .2); lm[5] = (0, .1); lm[8] = (0, .2)
s1 = hb.hand_shape(lm, 1); assert abs(s1[1] - .5) < 1e-9
assert hb.is_jump(s1, (s1[0], .5)) is False and hb.is_jump(s1, (s1[0], .9)) is True
a = np.zeros((54, 96, 3), np.uint8); b = a.copy(); b[:] = 10
assert hb.motion_energy(a, b) == 10
frames = []
for i in range(90):
    mo = 1 if i < 30 else 5 if i < 60 else 20
    frames.append(dict(motion=None if i == 0 else mo + i * 1e-3, det=(mo < 20 or i % 2 == 0), conf=.9, jump=(i % 10 == 0)))
s = hb.summarize(frames)
assert s["bands"][0]["detected_pct"] == 100 and abs(s["bands"][2]["detected_pct"] - 50) < 5
assert (hb.verdict(95), hb.verdict(75), hb.verdict(40)) == ("good", "shaky", "poor")
print("metrics OK", [(b["name"], round(b["detected_pct"])) for b in s["bands"]])

# --- end-to-end smoke test: synthetic clip with no hand in it -> pipeline must run and report ~0%
d = tempfile.mkdtemp(); p = os.path.join(d, "synthetic.mp4")
w = cv2.VideoWriter(p, cv2.VideoWriter_fourcc(*"mp4v"), 60, (640, 360))
rng = np.random.default_rng(0)
for i in range(180):
    f = np.full((360, 640, 3), 40, np.uint8)
    x = int(320 + 250 * math.sin(i / (30 if i < 90 else 6)))          # slow then fast movement
    cv2.rectangle(f, (x - 40, 120), (x + 40, 240), (200, 180, 160), -1)
    w.write(f)
w.release()
be = hb.MediaPipeBackend(mode="tracking")
r = hb.analyse(p, be, 30, os.path.join(d, "ann.mp4"))
hb.report(r)
assert r["summary"]["frames"] >= 80 and os.path.getsize(os.path.join(d, "ann.mp4")) > 0
assert r["summary"]["bands"][2]["frames"] > 0
print("end-to-end OK (no hand in clip, so ~0% found is correct)")
