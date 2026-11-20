# Tests

Run from this folder (needs Node 18+, Python with `playwright`, and Chrome):

    python3 extract.py ../index.html /tmp/app.mjs && APP_MJS=/tmp/app.mjs node unit.mjs
    python3 -I browser_live.py       # live tab with a stand-in for MediaPipe, fake camera and microphone
    python3 -I browser_pairing.py    # two pages pair as computer and phone and video arrives
    python3 -I browser_history.py    # sessions, levels, persistence
    python3 -I browser_features.py   # fingerboard tab, teacher link, exercise mode on a recorded scale, offline install

`unit.mjs` covers the elbow metric, pitch detection, string positions, model arm, sessions, hand signals, pairing codes, fingerboard geometry, exercises, teacher links and bow path.
`fixture_d_major_scale.wav` is a synthetic D major scale with the fourth note (G3) 30 cents sharp, used to test exercise mode.
The browser tests do not test MediaPipe accuracy. That needs real footage (see ../../cello-tools).
Edit the Chrome path (`/usr/bin/google-chrome`) in the browser tests if yours differs.

- `browser_videotest.py`: Video test tab with "compare with the sound" on, using `fixture_scale_video.webm` (a recorded scale) and a fake MediaPipe.
- `browser_record.py`: record a model arm from steady fake strokes, replay, save to file, reload, open the file, reject a bad file.
- `cello_geometry.mjs`: outline widths and length equal the spec, nothing overshoots, string length = neck + stop, every value is inside its published range. Run with `node tests/cello_geometry.mjs`.
- `browser_cello_sound.py` and `sound_roundtrip.mjs`: the cello page. Tapping the fingerboard plays a note and puts the finger marker where the string maths says; the microphone (fed the recorded D major scale) moves the marker through D, E, F#, G, A, B, C#, D.
- `browser_clip_record.py`: the recorder in the Video test tab (fake camera and microphone): start, red stop with timer, preview, save to device, load for analysis.
