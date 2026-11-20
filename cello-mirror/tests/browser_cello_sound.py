"""Cello page: tap the fingerboard (sound plays, finger marker lands where the maths says), and the microphone (fed a recorded D major scale) moves the marker."""
import os, subprocess, sys, time
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..'); CHROME = '/usr/bin/google-chrome'
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8766', '--bind', '127.0.0.1', '-d', ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox', '--autoplay-policy=no-user-gesture-required', '--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream', '--use-file-for-fake-audio-capture=' + os.path.join(HERE, 'fixture_d_major_scale.wav') + '%noloop'])
        pg = b.new_context(permissions=['microphone'], viewport={'width': 560, 'height': 900}).new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto('http://127.0.0.1:8766/cello-view.html'); pg.wait_for_timeout(500)
        box = pg.locator('#cv').bounding_box()
        # tap a spot on the fingerboard, left of centre string pair, a third of the way down
        pg.mouse.move(box['x'] + box['width'] * 0.5, box['y'] + box['height'] * 0.33); pg.mouse.down(); pg.wait_for_timeout(300)
        st = pg.evaluate('({...window.__cello.state})'); assert st['on'] and st['mm'] > 50 and st['freq'] > 65, st
        pg.screenshot(path='/tmp/cm/cello_tap.png'); pg.mouse.up(); pg.wait_for_timeout(100)
        assert not pg.evaluate('window.__cello.state.on'), 'released'
        # microphone
        pg.click('#micBtn'); seen = set()
        for _ in range(60):
            pg.wait_for_timeout(150); s = pg.evaluate('({...window.__cello.state})')
            if s['on'] and s['src'] == 'mic': seen.add(round(s['freq'] / 5) * 5)
            if len(seen) == 1 and _ == 25: pg.screenshot(path='/tmp/cm/cello_mic.png')
        print('mic frequencies seen (rounded):', sorted(seen)); assert len(seen) >= 4, seen
        assert not errs, errs; print('cello sound OK')
        b.close()
finally: srv.terminate()
