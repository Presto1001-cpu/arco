#!/usr/bin/env bash
# Creates a Python 3.12 environment with everything handbench.py needs.
# MediaPipe 0.10.14 is pinned on purpose: it is the last version that still bundles the hand
# and pose models inside the pip package, so it runs offline.
set -e
python3.12 -m venv .venv 2>/dev/null || python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install "mediapipe==0.10.14" "numpy<2" opencv-python-headless
pip install onnxruntime rtmlib      # optional second backend (downloads its models on first run)
echo "Done. Try:  .venv/bin/python handbench.py your_clip.mp4 --fps 30"
