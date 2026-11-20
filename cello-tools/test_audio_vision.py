import math, random, numpy as np, audio_vision as av

sr = 44100
def tone(f, sec):
    t = np.arange(int(sr * sec)) / sr; return (0.5 * np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)).astype(np.float32)

# 1) pitch: 146.8 Hz and 220 Hz and 440 Hz found within 1 Hz, silence rejected
for f in (146.832, 220.0, 440.0):
    got = av.pitch_at(tone(f, 1.0), sr, [0.5])[0]; assert got and abs(got - f) < 1.0, (f, got)
assert av.pitch_at(np.zeros(sr, dtype=np.float32), sr, [0.5])[0] is None

# 2) string/position maths agrees with the page
assert abs(av.stop_mm(220.0)) < 1e-6 and abs(av.stop_mm(293.665) - 690 * (1 - 2 ** (-5 / 12))) < 0.5 and av.stop_mm(50) is None

# 3) agreement: fingertip moves with the pitch -> high R2 and beats the control; unrelated movement -> no agreement
random.seed(3); n = 300; frames = []; pitches = []
for i in range(n):
    s = 2 + 8 * (0.5 + 0.5 * math.sin(i / 17)); hz = 220 * 2 ** (s / 12); mm = 690 * (1 - 2 ** (-s / 12))
    def hand(x, y): return [[x, y]] * 21
    frames.append(dict(i=i, t=i / 30, motion=abs(math.sin(i / 9)), hands=[hand(0.2 + 0.001 * mm, 0.5 + 0.1 * math.sin(i / 3))]))
    pitches.append(hz)
bench = dict(size=[1000, 1000], frames=frames)
r = av.agreement(bench, pitches); assert r["enough"] and r["r2"] > 0.95 and r["agrees"], r
for f in frames: f["hands"] = [[[random.random(), random.random()]] * 21]
r = av.agreement(bench, pitches); assert r["enough"] and not r["agrees"], r
assert not av.agreement(bench, [None] * n)["enough"]
print("audio_vision OK")
