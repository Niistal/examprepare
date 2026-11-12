"""Real Chromium regression tests. Uses temporary accounts and local servers only.
Run: python study_lab/test_runner_browser.py (pip install playwright; playwright install chromium).
"""
import functools,json,sys,tempfile,threading
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from wsgiref.simple_server import make_server,WSGIRequestHandler
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from distribution.server import App

class QuietStatic(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
class QuietWSGI(WSGIRequestHandler):
    def log_message(self,*args):pass
@contextmanager
def servers():
    with tempfile.TemporaryDirectory(prefix='study-browser-') as tmp:
        static=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietStatic,directory=str(ROOT/'study_lab')))
        hosted=make_server('127.0.0.1',0,lambda e,s:[],handler_class=QuietWSGI)
        origin=f'http://127.0.0.1:{hosted.server_port}'
        hosted.set_app(App(Path(tmp)/'test.sqlite3',origin,development=True))
        threads=[]
        for server in [static,hosted]:
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();threads.append(thread)
        try:yield f'http://127.0.0.1:{static.server_port}',origin
        finally:
            for server in [static,hosted]:server.shutdown();server.server_close()
            for thread in threads:thread.join()

def run_code(page,code):
    page.locator('#answerEditor').fill(code)
    page.locator('#runAnswer').click()
    page.locator('#stopRun').wait_for(state='hidden',timeout=180000)
    status=page.locator('#runStatus').inner_text()
    assert 'Ejecución terminada' in status,(status,page.locator('#runOutput').inner_text())

def check_files(page,names):
    assert sorted(page.locator('#runFiles a').evaluate_all('(links)=>links.map(a=>a.download)'))==sorted(names)
    for image in page.locator('#runFiles img').all():
        image.wait_for(state='visible')
        expect(image).to_have_js_property('complete',True)
        assert image.evaluate('(img)=>img.naturalWidth>0')
    for name in names:
        with page.expect_download() as download:
            page.locator('#runFiles a').filter(has_text='Descargar '+name).click()
        data=Path(download.value.path()).read_bytes()
        assert data,name
        if name.endswith('.png'):assert data.startswith(b'\x89PNG\r\n\x1a\n')
        if name.endswith('.svg'):assert b'<svg' in data
    print('PASS previews and downloads: '+', '.join(names),flush=True)

with servers() as (local,hosted), sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    try:
        page=browser.new_page(accept_downloads=True)
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(local);page.evaluate("startSingle('P10')")
        solution=page.evaluate("BANK.find(q=>q.id==='P10').solution")
        run_code(page,solution);check_files(page,['ventas.png'])
        # A new run clears old files and captures show(), CSV and nested SVG output.
        run_code(page,"import matplotlib.pyplot as plt\nfrom pathlib import Path\nplt.plot([1,2],[3,4])\nplt.show()\nPath('result.csv').write_text('a,b\\n1,2\\n')")
        check_files(page,['figure-1.png','result.csv'])
        page.evaluate("startSingle('P22')")
        assert page.locator('#runFiles a').count()==0
        run_code(page,page.evaluate("BANK.find(q=>q.id==='P22').solution"))
        check_files(page,['grafico.png','grafico.svg'])
        # Import rejects oversized data without replacing the current answers.
        page.evaluate("window.confirm=()=>true;data.answers.keep='preserved'")
        page.evaluate("importState(new File(['x'.repeat(10001025)],'too-large.json'))")
        assert page.evaluate('data.answers.keep')=='preserved'
        page.goto(hosted+'/login')
        response=page.request.post(hosted+'/api/register',headers={'Origin':hosted},data={'username':'browser-test','password':'test-password-12345'})
        assert response.status==200,response.text()
        page.goto(hosted)
        page.evaluate("window.confirm=()=>true")
        page.evaluate("importState(new File([JSON.stringify({schema:1,data:{ratings:{},answers:{large:'x'.repeat(2100000)},history:[]}})],'large.json'))")
        assert page.evaluate('cloudStorage.flush()')
        page.reload();assert page.evaluate('data.answers.large.length')==2100000
        print('PASS 2.1 MB import, account save and reload; oversized import preserves answers',flush=True)
        page.evaluate("startSingle('P10')")
        run_code(page,page.evaluate("BANK.find(q=>q.id==='P10').solution"));check_files(page,['ventas.png'])
        page.evaluate("startSingle('P22')")
        run_code(page,page.evaluate("BANK.find(q=>q.id==='P22').solution"));check_files(page,['grafico.png','grafico.svg'])
        print('PASS authenticated Worker and blob previews with production CSP',flush=True)
        # Recover completed files after a Python error; starting again removes old results.
        page.locator('#answerEditor').fill("from pathlib import Path\nPath('partial.csv').write_text('saved')\nraise ValueError('expected-test-error')")
        page.locator('#runAnswer').click();page.locator('#stopRun').wait_for(state='hidden',timeout=180000)
        assert 'expected-test-error' in page.locator('#runOutput').inner_text()
        check_files(page,['partial.csv'])
        run_code(page,"from pathlib import Path\nPath('large.bin').write_bytes(b'x' * 10000001)\nPath('small.txt').write_text('kept')")
        check_files(page,['small.txt'])
        assert '10 MB' in page.locator('#runOutput').inner_text()
        print('PASS partial files after errors and bounded file exports',flush=True)
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        assert not errors,errors
        print('PASS mobile layout and no JavaScript errors',flush=True)
    finally:browser.close()
