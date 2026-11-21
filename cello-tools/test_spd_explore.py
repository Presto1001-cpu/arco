"""Checks the in-browser SPD explorer on a small synthetic zip (names, json keys, npy shape, text)."""
import os, subprocess, sys, time
from playwright.sync_api import sync_playwright
HERE=os.path.dirname(os.path.abspath(__file__)); Z=sys.argv[1] if len(sys.argv)>1 else '/tmp/cm/test_spd.zip'
srv=subprocess.Popen([sys.executable,'-m','http.server','8769','--bind','127.0.0.1','-d',HERE],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
try:
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox']); pg=b.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto('http://127.0.0.1:8769/spd-explore.html'); pg.set_input_files('#f',Z); pg.wait_for_selector('#copy:not([hidden])',timeout=15000)
        t=pg.inner_text('#out'); print(t)
        for need in ['entries 4','.npy','(120, 21, 3)','fps:number','joints:list[50]','hello dataset notes','videos 1']: assert need in t, need
        assert not errs, errs; print('spd explorer OK'); b.close()
finally: srv.terminate()
