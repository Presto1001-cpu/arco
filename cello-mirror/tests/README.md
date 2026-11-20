# Tests

Run from this folder (needs Node 18+, Python with `playwright`, and Chrome):

    python3 extract.py ../index.html /tmp/app.mjs && APP_MJS=/tmp/app.mjs node unit.mjs
    python3 -I browser_live.py       # live tab with a stand-in for MediaPipe, fake camera and microphone
    python3 -I browser_pairing.py    # two pages pair as computer and phone and video arrives
    python3 -I browser_history.py    # sessions, levels, persistence

`unit.mjs` covers the elbow metric, pitch detection, string positions, model arm, sessions, hand signals and pairing codes.
The browser tests do not test MediaPipe accuracy. That needs real footage (see ../../cello-tools).
Edit the Chrome path (`/usr/bin/google-chrome`) in the browser tests if yours differs.
