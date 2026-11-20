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
