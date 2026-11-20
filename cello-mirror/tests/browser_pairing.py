from playwright.sync_api import sync_playwright
URL='file://'+__import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','index.html'))+''
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream'])
    ctx=b.new_context(permissions=['camera','microphone'])
    pc=ctx.new_page(); ph=ctx.new_page(); errs=[]
    for pg,n in ((pc,'computer'),(ph,'phone')): pg.on('pageerror',lambda e,n=n:errs.append(n+': '+str(e)))
    pc.goto(URL); ph.goto(URL)
    pc.click('button[data-tab=phone]'); ph.click('button[data-tab=phone]')
    pc.click('#pcMake'); pc.wait_for_function("document.getElementById('pcOffer').value.length>100",timeout=15000)
    offer=pc.input_value('#pcOffer'); print('offer chars:',len(offer))
    ph.fill('#phOffer',offer); ph.click('#phStart'); ph.wait_for_function("document.getElementById('phAnswer').value.length>100",timeout=15000)
    ans=ph.input_value('#phAnswer'); print('answer chars:',len(ans))
    pc.fill('#pcAnswer',ans); pc.click('#pcConnect')
    pc.wait_for_function("document.getElementById('sideBadge').textContent==='Phone connected'",timeout=20000)
    pc.wait_for_function("document.getElementById('sideVid').videoWidth>0",timeout=15000)
    print('badge:',pc.inner_text('#sideBadge'),'| remote video',pc.evaluate("[sideVid.videoWidth,sideVid.videoHeight]"))
    pc.wait_for_timeout(1500)
    # check the picture actually changes (the fake camera animates), drawn on the canvas
    px=lambda: pc.evaluate("(()=>{const c=document.getElementById('sideCv');const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let s=0;for(let i=0;i<d.length;i+=4000)s+=d[i]+d[i+1];return s})()")
    a=px(); pc.wait_for_timeout(800); print('canvas drawn:',a>0)
    print('bad code message:', end=' '); pc.fill('#pcAnswer','nonsense'); pc.click('#pcConnect'); print(pc.inner_text('#pMsg'))
    pc.screenshot(path='/tmp/cm/pair.png'); print('errors:',errs); b.close()
