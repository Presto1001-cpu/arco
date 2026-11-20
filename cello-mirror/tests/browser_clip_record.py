"""Record a clip in the Video test tab: start, stop, preview, save, and load it for analysis."""
import os, subprocess, sys, time
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..'); CHROME = '/usr/bin/google-chrome'
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8767', '--bind', '127.0.0.1', '-d', ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox', '--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'])
        pg = b.new_context(permissions=['camera', 'microphone'], accept_downloads=True, viewport={'width': 420, 'height': 900}).new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto('http://127.0.0.1:8767/index.html'); pg.wait_for_timeout(500)
        pg.evaluate("document.querySelector('[data-tab=test], button[data-t=test]') && document.querySelector('[data-tab=test], button[data-t=test]').click()")
        if not pg.is_visible('#clipBtn'):
            for t in pg.locator('nav button, .tabs button, [role=tab]').all():
                if 'video' in (t.inner_text() or '').lower(): t.click(); break
        assert pg.is_visible('#clipBtn'), 'recorder panel not visible'
        assert pg.inner_text('#clipBtn') == 'Start recording'
        pg.click('#clipBtn'); pg.wait_for_timeout(3500); assert pg.inner_text('#clipBtn') == 'Stop recording', pg.inner_text('#clipMsg')
        assert pg.inner_text('#clipTime').startswith('●'); pg.screenshot(path='/tmp/cm/clip_recording.png')
        pg.click('#clipBtn'); pg.wait_for_selector('#clipAct:not([hidden])', timeout=8000)
        print('message:', pg.inner_text('#clipMsg')); assert 'Recorded' in pg.inner_text('#clipMsg')
        with pg.expect_download() as d: pg.click('#clipSave')
        print('saved as', d.value.suggested_filename); assert d.value.suggested_filename.startswith('cello-')
        pg.click('#clipAnalyse'); pg.wait_for_timeout(300)
        assert not pg.is_disabled('#runBtn'), 'run button should be enabled'; print('file loaded:', pg.inner_text('#testMsg'))
        pg.screenshot(path='/tmp/cm/clip_done.png'); assert not errs, errs; print('clip recorder OK'); b.close()
finally: srv.terminate()
