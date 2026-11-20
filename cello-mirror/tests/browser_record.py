"""Record a model arm from a (fake) player making steady strokes, replay it, save it, reload, and open it again."""
import os, json
from playwright.sync_api import sync_playwright
URL = 'file://' + os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'index.html'))
STUB = '''
export const FilesetResolver={forVisionTasks:async()=>({})};
export class HandLandmarker{static async createFromOptions(){return new HandLandmarker()}detectForVideo(){return{landmarks:[]}}close(){}}
export class PoseLandmarker{static async createFromOptions(){return new PoseLandmarker()}close(){}
detectForVideo(){const t=performance.now(),q=(1-Math.cos(2*Math.PI*t/2000))/2;
const L=Array.from({length:33},()=>({x:.5,y:.5,z:0,visibility:1}));
L[11]={x:.6,y:.35,z:0,visibility:1};L[12]={x:.4,y:.35,z:0,visibility:1};
L[14]={x:.33,y:.55,z:0,visibility:1};L[16]={x:.4-(0.35+0.5*q)*0.2,y:.35+0.9*0.2,z:0,visibility:1};
return{landmarks:[L]}}}
'''
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream', '--allow-file-access-from-files'])
    ctx = b.new_context(permissions=['camera', 'microphone'], accept_downloads=True); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/vision_bundle.mjs', lambda r: r.fulfill(body=STUB, content_type='text/javascript', headers={'access-control-allow-origin': '*'}))
    pg.route('**/*.task', lambda r: r.fulfill(body=b'x', headers={'access-control-allow-origin': '*'}))
    pg.goto(URL); assert pg.is_disabled('#recBtn')
    pg.click('#camBtn'); pg.wait_for_function("!document.getElementById('recBtn').disabled", timeout=20000)
    pg.click('#recBtn'); pg.wait_for_timeout(1500); print('during:', pg.inner_text('#liveMsg'))
    assert 'Recording' in pg.inner_text('#liveMsg')
    pg.wait_for_function("document.getElementById('liveMsg').textContent.startsWith('Model recorded') || document.getElementById('liveMsg').className.includes('err')", timeout=20000)
    msg = pg.inner_text('#liveMsg'); print('after:', msg); assert msg.startswith('Model recorded'), msg
    assert pg.is_checked('#ghostOn')
    pg.click('button[data-tab=model]'); info = pg.inner_text('#mdInfo'); print('info:', info)
    assert 'Recorded model' in info and 'strokes' in info and pg.input_value('#mdSrc') == 'take'
    pg.wait_for_timeout(800); pg.screenshot(path='/tmp/cm/model_take.png')
    with pg.expect_download() as d: pg.click('#mdSave')
    path = '/tmp/cm/cello-model-test.json'; d.value.save_as(path); o = json.load(open(path)); assert o['kind'] == 'take' and len(o['template']) == 64 and o['arm'] == 'right', list(o)
    pg.reload(); pg.click('button[data-tab=model]'); assert pg.input_value('#mdSrc') == 'take' and 'Recorded model' in pg.inner_text('#mdInfo'), 'not restored after reload'
    pg.evaluate("localStorage.removeItem('cm-take')"); pg.reload(); pg.click('button[data-tab=model]'); assert 'No recorded model' in pg.inner_text('#mdInfo')
    pg.set_input_files('#mdOpen', path); pg.wait_for_function("document.getElementById('mdInfo').textContent.startsWith('Recorded model')", timeout=5000)
    open('/tmp/cm/bad.json', 'w').write('{"hello":1}'); pg.set_input_files('#mdOpen', '/tmp/cm/bad.json'); pg.wait_for_timeout(300)
    print('bad file:', pg.inner_text('#mdInfo')); assert 'not a model file' in pg.inner_text('#mdInfo')
    print('errors:', errs); assert not errs; b.close()
print('record OK')
