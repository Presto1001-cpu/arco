from playwright.sync_api import sync_playwright
import json, time
now=int(time.time()*1000)
sess=[dict(at=now-i*86400000//2, seconds=300+i*60, level='beginner', focus='both', arm='right', size='4/4', greenPct=60+i*3, drops=i%3, tunePct=50+i*2, notes=40) for i in range(8)]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':430,'height':900}); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('dialog',lambda d:d.accept())
    pg.goto('file://'+__import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','index.html'))+'')
    pg.evaluate("s=>localStorage.setItem('cm-sessions',s)", json.dumps(sess)); pg.reload(); pg.wait_for_timeout(300)
    pg.click('#saveSess'); print('empty save msg:', pg.inner_text('#liveMsg'))
    pg.select_option('#levelSel','advanced'); print('adv tol:', pg.input_value('#tol'), pg.input_value('#micTol'))
    pg.click('button[data-tab=history]'); pg.wait_for_timeout(300)
    print('rows:', pg.locator('#hRows tr').count(), '| week:', pg.inner_text('#hWeek').replace('\n',' ')[:120])
    pg.screenshot(path='/tmp/cm/hist.png', full_page=True)
    pg.reload(); print('level persisted:', pg.input_value('#levelSel'))
    pg.click('button[data-tab=history]'); pg.click('#hClear'); print('after clear rows:', pg.inner_text('#hRows')[:20])
    print('errors:',errs); b.close()
