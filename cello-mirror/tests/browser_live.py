from playwright.sync_api import sync_playwright
import json
URL='file://'+__import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','index.html'))+''
STUB='''
export const FilesetResolver={forVisionTasks:async()=>({})};
let n=0;
const hand=(ox)=>Array.from({length:21},(_,i)=>({x:ox+0.01*(i%5),y:0.5-0.02*Math.floor(i/5)+0.002*Math.sin(n/5),z:0}));
export class HandLandmarker{static async createFromOptions(){return new HandLandmarker()}detectForVideo(){n++;return{landmarks:[hand(0.2),hand(0.7)]}}close(){}}
export class PoseLandmarker{static async createFromOptions(){return new PoseLandmarker()}close(){}
detectForVideo(){n++;const L=Array.from({length:33},()=>({x:.5,y:.5,z:0,visibility:1}));
L[11]={x:.6,y:.35,z:0,visibility:1};L[12]={x:.4,y:.35,z:0,visibility:1};
L[14]={x:.33,y:.55+0.004*Math.sin(n/6),z:0,visibility:1};L[16]={x:.2,y:.6,z:0,visibility:1};L[13]={x:.67,y:.55,z:0,visibility:1};L[15]={x:.75,y:.5,z:0,visibility:1};
return{landmarks:[L]}}}
'''
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream','--allow-file-access-from-files'])
    ctx=b.new_context(permissions=['camera','microphone']); pg=ctx.new_page(); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/vision_bundle.mjs',lambda r:r.fulfill(body=STUB,content_type='text/javascript',headers={'access-control-allow-origin':'*'}))
    pg.route('**/*.task',lambda r:r.fulfill(body=b'x',headers={'access-control-allow-origin':'*'}))
    pg.goto(URL); pg.click('#camBtn')
    pg.wait_for_function("document.getElementById('badge').textContent!=='Loading models...' && document.getElementById('badge').textContent!=='Camera off'",timeout=20000)
    print('badge after start:',pg.inner_text('#badge'))
    pg.click('#baseBtn'); pg.wait_for_function("document.getElementById('liveMsg').textContent.startsWith('Baseline saved')",timeout=10000)
    print(pg.inner_text('#liveMsg'))
    pg.check('#ghostOn'); pg.click('#micBtn'); pg.wait_for_timeout(6500)
    pg.screenshot(path='/tmp/cm/live.png')
    print('stats:',{k:pg.inner_text('#'+k) for k in ['stTime','stGreen','stDrops','stHands','stCurve','stFps','mNote','mTune','mPos']})
    print('badge now:',pg.inner_text('#badge'))
    pg.click('#saveSess'); print('save:',pg.inner_text('#liveMsg'))
    pg.click('button[data-tab=history]'); print('history rows:',pg.locator('#hRows tr').count(),'|',pg.inner_text('#hRows tr').replace('\t',' | ')[:160])
    pg.click('button[data-tab=live]'); print('camera still running after history tab?', pg.inner_text('#camBtn'))
    # a tolerance break: move elbow far -> amber
    print('errors:',errs); b.close()
