"""Video test tab with the sound comparison on, using a fake MediaPipe and a short clip that carries a recorded scale."""
import os
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); URL = 'file://' + os.path.abspath(os.path.join(HERE, '..', 'index.html'))
STUB = '''
export const FilesetResolver={forVisionTasks:async()=>({})};
let n=0;
const hand=(ox)=>Array.from({length:21},(_,i)=>({x:ox+0.01*(i%5),y:0.5-0.02*Math.floor(i/5)+0.1*Math.sin(n/4),z:0}));
export class HandLandmarker{static async createFromOptions(){return new HandLandmarker()}detectForVideo(){n++;return{landmarks:[hand(0.2)],handedness:[[{score:0.9}]]}}close(){}}
export class PoseLandmarker{static async createFromOptions(){return new PoseLandmarker()}detectForVideo(){return{landmarks:[]}}close(){}}
'''
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
    pg = b.new_context().new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/vision_bundle.mjs', lambda r: r.fulfill(body=STUB, content_type='text/javascript', headers={'access-control-allow-origin': '*'}))
    pg.route('**/*.task', lambda r: r.fulfill(body=b'x', headers={'access-control-allow-origin': '*'}))
    pg.goto(URL); pg.click('button[data-tab=test]')
    pg.set_input_files('#file', os.path.join(HERE, 'fixture_scale_video.webm')); pg.check('#sndChk'); pg.select_option('#fpsSel', '15'); pg.click('#runBtn')
    pg.wait_for_function("document.getElementById('sndBox') && !document.getElementById('sndBox').hidden && !document.getElementById('sndBox').textContent.startsWith('Reading')", timeout=120000)
    print('verdict:', pg.inner_text('#verdictBox').replace('\n', ' ')[:120]); box = pg.inner_text('#sndBox'); print('sound box:', box[:260])
    assert 'Sound against sight' in box or 'too few' in box, box
    assert 'Could not read audio' not in box
    print('errors:', errs); assert not errs; b.close()
