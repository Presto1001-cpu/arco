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

## Measuring finger accuracy (hand labelling)

"Hand found" is not "hand correct". To measure accuracy you label some frames yourself:

1. `python handbench.py clip.mp4 --fps 30 --save-landmarks --out out`
2. `python make_label_manifest.py out/clip_mediapipe_tracking.json clip.mp4 --hand rightmost -n 99 -o manifest.json`
   (99 frames, a third each from slow, medium and fast moments; `--hand` picks the neck hand when two hands are in view)
3. Open `label.html` (https://presto1001-cpu.github.io/arco/cello-tools/label.html), choose the video and `manifest.json`, click the 7 points on each frame, download `fingertip-labels.json`.
4. `python evaluate_labels.py out/clip_mediapipe_tracking.json fingertip-labels.json --hand rightmost`

Never commit footage to this public repository. Manifests and label files contain only numbers.

## Stronger models in the cloud

`cello_hand_benchmark.ipynb` runs MediaPipe and RTMW side by side in Google Colab:
https://colab.research.google.com/github/Presto1001-cpu/arco/blob/main/cello-tools/cello_hand_benchmark.ipynb

## audio_vision.py: sound against sight
Checks whether the fingertip position seen by the camera agrees with the position the pitch implies.
`python audio_vision.py out/clip_mediapipe_tracking.json clip.wav --hand rightmost` (wav: `ffmpeg -i clip.mov -vn -ac 1 -ar 44100 clip.wav`).
Reports R² against a shifted-sound control, by speed band. It guesses the string from the pitch, so it is a consistency check, not a measurement.
Clip 3 result: about 27% against a control of 3%, similar in slow, medium and fast parts.
The same check is in the app: Video test tab, tick "compare with the sound".
