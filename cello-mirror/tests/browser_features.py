"""Fingerboard tab, teacher link, exercise mode (fed a synthetic recording of a D major scale), and offline install."""
import os, subprocess, sys, time, json
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..')
CHROME = '/usr/bin/google-chrome'
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8765', '--bind', '127.0.0.1', '-d', ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox', '--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream',
                              '--use-file-for-fake-audio-capture=' + os.path.join(HERE, 'fixture_d_major_scale.wav') + '%noloop'])
        ctx = b.new_context(permissions=['camera', 'microphone']); pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        # teacher link round trip
        pg.goto('http://127.0.0.1:8765/index.html'); pg.click('button[data-tab=teacher]')
        pg.select_option('#tLevel', 'advanced'); pg.select_option('#tFocus', 'bow'); pg.select_option('#tSize', '3/4'); pg.select_option('#tArm', 'left'); pg.select_option('#tEx', 'd1')
        pg.click('#tMake'); link = pg.input_value('#tLink'); print('link:', link)
        pg2 = ctx.new_page(); pg2.on('pageerror', lambda e: errs.append('p2 ' + str(e))); pg2.goto(link)
        print('student sees:', pg2.inner_text('#tBanner'))
        assert pg2.input_value('#levelSel') == 'advanced' and pg2.input_value('#sizeSel') == '3/4' and pg2.input_value('#armSel') == 'left' and pg2.input_value('#exSel') == 'd1'
        assert pg2.input_value('#tol') == '15' and pg2.input_value('#micTol') == '10'
        pg2.close()
        # fingerboard table
        pg.click('button[data-tab=board]'); pg.select_option('#fbSize', '4/4')
        rows = pg.locator('#fbRows tr'); assert rows.count() == 12
        first = [c.strip() for c in rows.nth(1).inner_text().split('\t')]; print('1st position row:', first)
        assert first[0] == '1st' and first[3] == '7.5' and first[5] == '34.5', first
        pg.select_option('#fbSize', '1/8'); assert pg.locator('#fbRows tr').nth(6).inner_text().split('\t')[6].strip() == '51', pg.locator('#fbRows tr').nth(6).inner_text()
        assert pg.locator('#dsRows tr').count() == 9
        # exercise mode with the recorded scale
        pg.click('button[data-tab=live]'); pg.select_option('#levelSel', 'beginner'); pg.select_option('#exSel', 'd1'); pg.click('#exStart')
        pg.wait_for_function("document.getElementById('exMsg').textContent.startsWith('Finished')", timeout=30000)
        msg = pg.inner_text('#exMsg'); print('exercise:', msg); print('notes:', pg.inner_text('#exNotes').replace('\n', ' | '))
        assert '7 of 8' in msg or '8 of 8' in msg, msg
        assert 'ok' in pg.eval_on_selector('#exNotes span:nth-child(1)', 'e=>e.className')
        assert 'off' in pg.eval_on_selector('#exNotes span:nth-child(4)', 'e=>e.className'), 'the sharp G3 should be flagged'
        print('position readout:', pg.inner_text('#mPos')[:140])
        pg.click('#saveSess'); print('saved:', pg.inner_text('#liveMsg'))
        # offline install
        pg.goto('http://127.0.0.1:8765/index.html'); pg.wait_for_timeout(1500)
        print('service worker:', pg.evaluate("navigator.serviceWorker.getRegistration().then(r=>!!r&&!!(r.active||r.installing||r.waiting))"))
        pg.wait_for_function("navigator.serviceWorker.controller||true"); pg.reload(); pg.wait_for_timeout(800)
        ctx.set_offline(True); pg.reload(); pg.wait_for_timeout(800)
        print('offline title:', pg.title()); assert 'Cello Mirror' in pg.title()
        mf = json.loads(pg.evaluate("fetch('manifest.webmanifest').then(r=>r.text())")); print('manifest:', mf['name'], mf['display'])
        print('errors:', errs); assert not errs
        b.close()
finally:
    srv.terminate()
