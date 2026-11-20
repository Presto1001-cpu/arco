# Cello tools

`handbench.py` measures how reliably a hand-tracking model finds a cellist's left hand, split by
how fast the picture is moving (slow / medium / fast thirds of the clip). It uses the same metrics
as the "Video test" tab of the web prototype, so the two give comparable numbers.

    ./setup.sh
    .venv/bin/python handbench.py clip.mp4 --fps 30 --annotate
    .venv/bin/python handbench.py clip.mp4 --mode static     # no tracking: detect every frame from scratch
    .venv/bin/python test_handbench.py                       # self-test

Outputs per clip: a CSV (one row per frame), a JSON, and with `--annotate` a video with the
hand skeleton drawn on it. Film the left hand from the side at the highest frame rate you can.

Backends: `mediapipe` (default, works offline) and `rtmlib` (RTMPose whole-body; needs internet to
download its models, and needs a person in view, so it is untested here).
