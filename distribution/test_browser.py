"""End-to-end login and sync in disposable Chromium sessions, without personal profiles."""
import json,os,socket,subprocess,tempfile,threading,time,urllib.request
from pathlib import Path
from wsgiref.simple_server import make_server,WSGIRequestHandler
from distribution.server import App

class Quiet(WSGIRequestHandler):
    def log_message(self,*args):pass

def port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def main():
    web_port,driver_port=port(),port();origin=f'http://127.0.0.1:{web_port}'
    with tempfile.TemporaryDirectory() as tmp:
        app=App(Path(tmp)/'qa.sqlite3',origin,development=True)
        web=make_server('127.0.0.1',web_port,app,handler_class=Quiet)
        thread=threading.Thread(target=web.serve_forever,daemon=True);thread.start()
        driver=subprocess.Popen(['chromedriver',f'--port={driver_port}','--allowed-ips=127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        sessions=[]
        def request(method,path,body=None):
            r=urllib.request.Request(f'http://127.0.0.1:{driver_port}'+path,data=json.dumps(body).encode() if body is not None else None,method=method,headers={'Content-Type':'application/json'})
            value=json.load(urllib.request.urlopen(r,timeout=20))['value']
            if isinstance(value,dict) and value.get('error'):raise AssertionError(value)
            return value
        def create():
            sid=request('POST','/session',{'capabilities':{'alwaysMatch':{'browserName':'chrome','goog:chromeOptions':{'binary':'/usr/bin/chromium','args':['--headless=new','--no-sandbox','--disable-dev-shm-usage']},'goog:loggingPrefs':{'browser':'ALL'}}}})['sessionId'];sessions.append(sid);return sid
        def js(sid,code):return request('POST',f'/session/{sid}/execute/sync',{'script':code,'args':[]})
        def wait(sid,code,label):
            for _ in range(80):
                if js(sid,'return Boolean('+code+')'):print('PASS',label);return
                time.sleep(.1)
            raise AssertionError(label)
        def enter(sid,name,action):
            request('POST',f'/session/{sid}/url',{'url':origin+'/login'})
            js(sid,"document.getElementById('username').value="+json.dumps(name)+";document.getElementById('password').value='browser test password 123';document.querySelector('button[value="+action+"]').click()")
            wait(sid,"location.pathname==='/' && document.getElementById('cloudStatus')",action+' abre aplicación')
        try:
            for _ in range(80):
                try:request('GET','/status');break
                except OSError:time.sleep(.1)
            a=create();enter(a,'student1','register')
            js(a,"startSingle('P35');document.getElementById('answerEditor').value='respuesta privada de A';document.getElementById('answerEditor').dispatchEvent(new Event('input',{bubbles:true}))")
            wait(a,"document.getElementById('cloudStatus').textContent==='Progreso guardado en tu cuenta'",'respuesta sincronizada')
            b=create();enter(b,'student1','login')
            wait(b,"document.getElementById('answerEditor').value==='respuesta privada de A'",'otro dispositivo recupera respuesta y sesión')
            request('DELETE',f'/session/{b}');sessions.remove(b)
            c=create();enter(c,'student2','register')
            wait(c,"Object.keys(data.answers).length===0",'otra cuenta sin respuestas ajenas')
            request('DELETE',f'/session/{c}');sessions.remove(c)
            b=create();enter(b,'student1','login')
            js(b,"document.getElementById('answerEditor').value='cambio desde B';persistDraft()")
            wait(b,"document.getElementById('cloudStatus').textContent==='Progreso guardado en tu cuenta'",'segundo dispositivo guarda revisión')
            js(a,"document.getElementById('answerEditor').value='cambio obsoleto desde A';persistDraft()")
            wait(a,"document.getElementById('cloudStatus').textContent.includes('Conflicto')",'conflicto visible sin sobrescritura')
            js(b,"window.onbeforeunload=null;location.reload()")
            wait(b,"document.getElementById('answerEditor').value==='cambio desde B'",'servidor conserva revisión correcta')
            request('POST',f'/session/{b}/window/rect',{'width':390,'height':844})
            wait(b,"document.documentElement.scrollWidth<=innerWidth+1",'cuenta y aplicación sin desbordamiento móvil')
            js(b,"[...document.querySelectorAll('button')].find(x=>x.textContent==='Cerrar sesión').click()")
            wait(b,"location.pathname==='/login'",'cerrar sesión tras guardar')
            request('POST',f'/session/{b}/url',{'url':origin+'/'})
            wait(b,"!document.getElementById('answerEditor') && document.body.textContent.includes('Inicia sesión')",'salir retira acceso a respuestas')
            for sid in sessions:
                errors=[x for x in request('POST',f'/session/{sid}/log',{'type':'browser'}) if x.get('level')=='SEVERE' and 'favicon' not in x.get('message','') and not (x.get('source')=='network' and (('/api/progress' in x.get('message','') and '409 (Conflict)' in x.get('message','')) or (x.get('message','').startswith(origin+'/ - ') and '401 (Unauthorized)' in x.get('message',''))))]
                assert not errors,errors
            print('PASS sin errores JavaScript ni bloqueos CSP')
        finally:
            for sid in sessions:
                try:request('DELETE',f'/session/{sid}')
                except OSError:pass
            driver.terminate();driver.wait(timeout=5);web.shutdown();web.server_close();thread.join(timeout=5)

if __name__=='__main__':main()
