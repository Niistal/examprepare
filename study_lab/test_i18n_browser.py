"""Bilingual default, persistence and progress checks in disposable Chromium profiles.
No external Python packages, real accounts, or personal browser profiles required.
"""
import json, os, socket, subprocess, sys, tempfile, threading, time, urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from wsgiref.simple_server import make_server, WSGIRequestHandler
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from distribution.server import App

class Static(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
class Quiet(WSGIRequestHandler):
    def log_message(self, *args): pass

def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]

def main():
    local = ThreadingHTTPServer(('127.0.0.1', 0), partial(Static, directory=str(ROOT/'study_lab')))
    with tempfile.TemporaryDirectory(prefix='study-i18n-') as tmp:
        hosted = make_server('127.0.0.1', 0, lambda e,s: [], handler_class=Quiet)
        origin = f'http://127.0.0.1:{hosted.server_port}'
        hosted.set_app(App(Path(tmp)/'qa.sqlite3', origin, development=True))
        for server in [local, hosted]: threading.Thread(target=server.serve_forever, daemon=True).start()
        driver_port = free_port()
        driver = subprocess.Popen(['chromedriver', f'--port={driver_port}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sessions = []
        def request(method, path, value=None):
            req = urllib.request.Request(f'http://127.0.0.1:{driver_port}'+path, method=method,
                data=json.dumps(value).encode() if value is not None else None, headers={'Content-Type':'application/json'})
            result = json.load(urllib.request.urlopen(req, timeout=60))['value']
            if isinstance(result, dict) and result.get('error'): raise AssertionError(result)
            return result
        def create():
            sid = request('POST','/session',{'capabilities':{'alwaysMatch':{'browserName':'chrome','goog:chromeOptions':{'binary':'/usr/bin/chromium','args':['--headless=new','--no-sandbox','--disable-dev-shm-usage','--window-size=1440,1000']},'goog:loggingPrefs':{'browser':'ALL'}}}})['sessionId']
            sessions.append(sid)
            return sid
        def js(sid, script): return request('POST',f'/session/{sid}/execute/sync',{'script':script,'args':[]})
        def wait(sid, expression, label):
            for _ in range(100):
                try:
                    if js(sid, 'return Boolean('+expression+')'):
                        print('PASS', label, flush=True)
                        return
                except Exception: pass
                time.sleep(.05)
            raise AssertionError(label)
        def change(sid, language):
            js(sid,"document.getElementById('languageSelect').value="+json.dumps(language)+";document.getElementById('languageSelect').dispatchEvent(new Event('change'))")
            wait(sid,'document.documentElement.lang==='+json.dumps(language)+' && typeof APP_LOCALE!==\'undefined\' && APP_LOCALE==='+json.dumps(language), 'selector '+language)
        try:
            for _ in range(100):
                try: request('GET','/status'); break
                except OSError: time.sleep(.05)
            sid=create()
            request('POST',f'/session/{sid}/url',{'url':f'http://127.0.0.1:{local.server_port}'})
            wait(sid,"APP_LOCALE==='eu' && document.documentElement.lang==='eu' && document.getElementById('languageSelect').value==='eu'",'euskera predeterminado')
            assert js(sid,"return document.getElementById('searchInput').getAttribute('placeholder')===translateText('pandas, kafka, JSON…')")
            js(sid,"startSingle('P01')")
            wait(sid,"document.getElementById('answerEditor').getAttribute('aria-label')===translateText('Tu solución o razonamiento') && document.getElementById('answerEditor').getAttribute('aria-label')!=='Tu solución o razonamiento'",'etiquetas accesibles en euskera')
            original_bank=json.loads(subprocess.check_output(['node',str(ROOT/'study_lab/scripts/export_bank.cjs')]))
            original_prompt=json.dumps(original_bank[0]['prompt'])
            wait(sid,"BANK[0].prompt===EUSKARA_CASES["+original_prompt+"] && document.getElementById('homeTitle').textContent!=='Tu plan de estudio, examen a examen.'",'interfaz y contenido localizados')
            js(sid,"startSingle('P01');document.getElementById('answerEditor').value='Mi respuesta sin traducir: print(42)';persistDraft();data.ratings.P01=2;save()")
            before=js(sid,"return JSON.stringify({answers:data.answers,ratings:data.ratings,history:data.history,ids:session.ids})")
            change(sid,'es-ES')
            assert js(sid,"return document.getElementById('answerEditor').value")=='Mi respuesta sin traducir: print(42)'
            assert js(sid,"return JSON.stringify({answers:data.answers,ratings:data.ratings,history:data.history,ids:session.ids})")==before
            assert js(sid,"return BANK[0].title")=='Validador de NIF con funciones'
            assert js(sid,"return document.getElementById('homeTitle').textContent")=='Tu plan de estudio, examen a examen.'
            change(sid,'eu')
            assert js(sid,"return JSON.stringify({answers:data.answers,ratings:data.ratings,history:data.history,ids:session.ids})")==before
            js(sid,"selectCourse('models');learningTab='Test';startLearningQuiz('all','practice',1,false,true);renderModalStudy();window.qaTerm=LEARNING_CONTENT.questions.find(q=>q.type==='term'&&q.answer.some(a=>/[áéíóúñ]/i.test(a)));const q=LEARNING_CONTENT.questions.find(q=>q.type==='choice');window.qaQuizId=learningState().quiz.id;learningState().quiz.answers[q.id]=q.answer;save()")
            quiz=js(sid,"return JSON.stringify(learningState().quiz)")
            change(sid,'es-ES')
            assert js(sid,"return JSON.stringify(learningState().quiz)")==quiz
            assert js(sid,"return LEARNING_CONTENT.questions.filter(q=>q.type==='term').every(q=>EUSKARA_LEARNING.questions.find(e=>e.id===q.id).answer.every(a=>StudyEngine.grade(q,a).correct))")
            change(sid,'eu')
            js(sid,"navigate('dashboard')")
            for width in [1440,390,320]:
                request('POST',f'/session/{sid}/window/rect',{'width':width,'height':950})
                assert js(sid,'return document.documentElement.scrollWidth<=innerWidth+1'),width
            print('PASS progreso, borrador, test y corrección bilingüe; responsive 1440/390/320',flush=True)
            # A fresh browser must still default to Euskara, regardless of another profile's preference.
            account=create()
            request('POST',f'/session/{account}/url',{'url':origin+'/login'})
            wait(account,"document.documentElement.lang==='eu' && document.querySelector('h1').textContent!=='Tu espacio de estudio'",'acceso en euskera')
            js(account,"document.getElementById('username').value='euskara-test';document.getElementById('password').value='bilingual-test-password-123';document.querySelector('button[value=register]').click()")
            wait(account,"!document.getElementById('codePanel').classList.contains('hidden')",'registro conserva código de recuperación')
            js(account,"document.getElementById('continue').click()")
            wait(account,"typeof APP_LOCALE!=='undefined' && APP_LOCALE==='eu' && document.getElementById('cloudStatus')",'cuenta en euskera')
            js(account,"startSingle('P01');document.getElementById('answerEditor').value='kontuko erantzuna';persistDraft()")
            change(account,'es-ES')
            assert js(account,"return document.getElementById('answerEditor').value")=='kontuko erantzuna'
            assert js(account,"return !document.querySelector('#calendarPanel [role=status]')")
            change(account,'eu')
            assert js(account,"return document.getElementById('answerEditor').value")=='kontuko erantzuna'
            for width in [320,390,768,1440]:
                request('POST',f'/session/{account}/window/rect',{'width':width,'height':950})
                js(account,"navigate('dashboard')")
                assert js(account,'return document.documentElement.scrollWidth<=innerWidth+1'),('hosted',width)
            offline=create()
            request('POST',f'/session/{offline}/url',{'url':(ROOT/'study_lab/index.html').as_uri()})
            wait(offline,"APP_LOCALE==='eu'",'archivo autónomo en euskera')
            change(offline,'es-ES')
            assert js(offline,"return BANK[0].title")=='Validador de NIF con funciones'
            change(offline,'eu')
            for session in sessions:
                errors=[x for x in request('POST',f'/session/{session}/log',{'type':'browser'}) if x['level']=='SEVERE' and 'favicon.ico' not in x['message']]
                assert not errors,errors
            print('PASS cuenta sincronizada antes de cambiar idioma; sin errores JS',flush=True)
        finally:
            for sid in sessions:
                try: request('DELETE',f'/session/{sid}')
                except Exception: pass
            driver.terminate();driver.wait(timeout=10)
            for server in [local,hosted]: server.shutdown();server.server_close()
if __name__=='__main__':main()
