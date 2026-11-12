"""QA real con Chromium/ChromeDriver; solo biblioteca estándar. Servidor en :8080, driver :9515."""
import json, os, urllib.request
BASE='http://127.0.0.1:9515'
def request(method,path,data=None):
    req=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,method=method,headers={'Content-Type':'application/json'})
    result=json.load(urllib.request.urlopen(req,timeout=30))['value']
    if isinstance(result,dict) and result.get('error'):raise RuntimeError(result)
    return result
session=request('POST','/session',{'capabilities':{'alwaysMatch':{'browserName':'chrome','goog:chromeOptions':{'binary':'/usr/bin/chromium','args':['--headless=new','--no-sandbox','--disable-dev-shm-usage','--window-size=1440,1000']},'goog:loggingPrefs':{'browser':'ALL'}}}})['sessionId']
def cmd(method,path,data=None):return request(method,'/session/'+session+path,data)
def js(script):return cmd('POST','/execute/sync',{'script':script,'args':[]})
def check(script,label):
    assert js('return Boolean('+script+')'),label
    print('PASS',label)
try:
    cmd('POST','/url',{'url':os.environ.get('NIIS_TEST_URL','http://127.0.0.1:8080')})
    check("document.querySelectorAll('.subject-card').length===5",'cinco materias')
    js("localStorage.clear();location.reload()")
    js("selectCourse('program')")
    check("document.querySelectorAll('.route-step[data-route]').length===27",'recorrido finito de Programazioa')
    js("document.getElementById('searchInput').value='NumPy';renderPractice()")
    check("document.querySelectorAll('#exerciseList article').length>0 && [...document.querySelectorAll('#exerciseList article')].every(x=>x.textContent.toLowerCase().includes('numpy'))",'búsqueda')
    js("document.getElementById('searchInput').value='';document.getElementById('levelFilter').value='1';renderPractice()")
    check("[...document.querySelectorAll('#exerciseList article')].every(x=>x.textContent.includes('BASE'))",'filtro nivel')
    js("startSingle('P01');document.getElementById('answerEditor').value='borrador QA';document.getElementById('answerEditor').dispatchEvent(new Event('input'));revealHint();revealSolution()")
    check("document.getElementById('answerEditor').value==='borrador QA'",'ayudas conservan borrador')
    js("rate(2);location.reload()")
    check("document.getElementById('answerEditor').value==='borrador QA' && data.ratings.P01===2",'recarga recupera sesión, texto y valoración')
    js("document.getElementById('examMode').value='exam';document.getElementById('examNumber').value='17';startExam()")
    check("document.getElementById('solutionToggle').disabled && document.getElementById('hintToggle').disabled",'examen bloquea ayudas')
    js("document.getElementById('answerEditor').value='respuesta examen';persistDraft();switchQuestion(1);switchQuestion(0)")
    check("document.getElementById('answerEditor').value==='respuesta examen'",'navegación conserva respuestas')
    js("startTimer();location.reload()")
    check("session.mode==='exam' && timeInterval!==null && document.getElementById('solutionBlock').classList.contains('hidden')",'reloj y bloqueo tras recarga')
    js("window.confirm=()=>true;finishExam()")
    check("!document.getElementById('solutionToggle').disabled && session.submitted",'entrega desbloquea corrección')
    js("redoExam()")
    check("!session.submitted && session.ids.every(id=>data.answers[session.id+'::'+id]===undefined)",'rehacer limpia solo el simulacro')
    check("!validState({ratings:null,answers:{},history:[]}) && !validState({ratings:{P01:9},answers:{},history:[]})",'rechaza respaldo inválido')
    js("window.__backup=JSON.stringify({schema:1,data});window.__export=URL.createObjectURL;URL.createObjectURL=b=>{window.__blob=b;return window.__export(b)};exportState()")
    check("window.__blob.type==='application/json'",'exportación JSON')
    cmd('POST','/execute/async',{'script':"const done=arguments[arguments.length-1];importState(new File([window.__backup],'qa.json',{type:'application/json'})).then(()=>done(true));",'args':[]})
    check("document.getElementById('progressPage').classList.contains('active')",'importación JSON')
    cmd('POST','/window/rect',{'width':390,'height':844})
    js("selectCourse('program')")
    check("document.documentElement.scrollWidth<=window.innerWidth+1",'móvil sin desbordamiento horizontal')
    check("document.getElementById('answerEditor').getAttribute('aria-label')",'editor etiquetado')
    if os.environ.get('NIIS_TEST_HOSTED'):
        check("document.querySelector('.session-signout').getAttribute('href')==='/signout-with-chatgpt?return_to=%2F'",'salida de sesión gestionada')
        check("document.querySelector('meta[http-equiv=\"Content-Security-Policy\"]').content.includes('sha256-')",'política de scripts por hash')
    logs=cmd('POST','/log',{'type':'browser'})
    assert not [x for x in logs if x['level']=='SEVERE' and 'favicon' not in x['message']],logs
    print('PASS sin errores JS de navegador')
finally:
    cmd('DELETE','')
