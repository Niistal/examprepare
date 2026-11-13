"""Real Chromium checks for contextual modes. Uses temporary ChromeDriver profile."""
import json,os,urllib.request,urllib.error
from pathlib import Path
BASE=os.environ.get('NIIS_DRIVER_URL','http://127.0.0.1:9515')
def request(method,path,data=None):
    req=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,method=method,headers={'Content-Type':'application/json'})
    try: result=json.load(urllib.request.urlopen(req,timeout=30))['value']
    except urllib.error.HTTPError as e: raise RuntimeError(e.read().decode()) from e
    if isinstance(result,dict) and result.get('error'):raise RuntimeError(result)
    return result
session=request('POST','/session',{'capabilities':{'alwaysMatch':{'browserName':'chrome','goog:chromeOptions':{'binary':'/usr/bin/chromium','args':['--headless=new','--no-sandbox','--disable-dev-shm-usage','--window-size=1440,1000']},'goog:loggingPrefs':{'browser':'ALL'}}}})['sessionId']
def cmd(method,path,data=None):return request(method,'/session/'+session+path,data)
def js(script):return cmd('POST','/execute/sync',{'script':script,'args':[]})
def check(script,label):
    assert js('return Boolean('+script+')'),label
    print('PASS',label)
try:
    cmd('POST','/url',{'url':os.environ.get('NIIS_TEST_URL','http://127.0.0.1:8086')})
    # Legacy assertions exercise the preserved Spanish edition; Euskara has its own suite.
    js("document.cookie='study_language=es-ES; Path=/';location.reload()")
    js("localStorage.clear();location.reload()")
    js("selectCourse('models')")
    check("document.querySelectorAll('.topic-overview-row').length===9",'nueve temas reales de Xabat con acceso directo')
    js("document.querySelector('[data-learn-topic]').click()")
    check("document.querySelectorAll('.learning-lesson').length===1",'tema seleccionado muestra explicación y práctica')
    check("!document.getElementById('modalStudy').classList.contains('hidden')&&document.getElementById('studyRoute').classList.contains('hidden')",'experiencia de teoría contextual')
    js("startSingle('E03');revealHint();revealHint();revealSolution()")
    check("getComputedStyle(document.getElementById('answerEditor')).display==='none'&&getComputedStyle(document.getElementById('runAnswer').closest('.editor-toolbar')).display==='none'",'teoría sin editor Python ni ejecución')
    check("document.getElementById('conceptAnswer')&&!pythonCase(currentQuestion())",'razonamiento teórico y bloqueo de ejecución')
    js("document.getElementById('conceptAnswer').value='FNR: positivos no detectados';document.getElementById('conceptAnswer').dispatchEvent(new Event('input'));location.reload()")
    check("document.getElementById('conceptAnswer').value==='FNR: positivos no detectados'",'borrador teórico conservado tras recarga')
    js("startSingle('P28')")
    check("getComputedStyle(document.getElementById('answerEditor')).display!=='none'&&pythonCase(currentQuestion())",'Programazioa conserva editor y ejecución')
    js("selectCourse('models');learningTopic='fuzzy';learningTab='Test';startLearningQuiz('all','practice',1,false,true);renderModalStudy()")
    js("window.testQ=quizQuestions(learningState().quiz).find(q=>q.type==='choice');let input=document.querySelector('[data-q=\"'+testQ.id+'\"][data-value=\"'+((testQ.answer+1)%4)+'\"]');input.checked=true;input.dispatchEvent(new Event('change'));document.querySelector('[data-check-q=\"'+testQ.id+'\"]').click()")
    check("document.querySelector('.quiz-feedback.incorrect')&&learningState().attempts.at(-1).correct===false",'feedback incorrecto y registro de intento')
    js("finishLearningQuiz()")
    check("document.querySelector('.quiz-feedback.manual')&&document.getElementById('learningBody').textContent.includes('No se ha asignado nota automática')",'respuestas abiertas con rúbrica sin nota ficticia')
    js("delete learningState().quiz;learningTopic='all';learningTab='Simulacro';startLearningQuiz(10,'exam',17,false,false);renderModalStudy()")
    check("!document.querySelector('.quiz-feedback')&&!document.querySelector('[data-check-q]')&&document.getElementById('learningClock')",'examen sin soluciones ni corrección anticipada, con reloj')
    js("location.reload()")
    js("selectCourse('models');learningTab='Simulacro';renderModalStudy()")
    check("learningState().quiz.ids.join(',')===StudyEngine.select(LEARNING_CONTENT.questions.filter(q=>q.course==='models'),10,17).map(q=>q.id).join(',')",'simulacro guardado y reproducible')
    js("finishLearningQuiz();learningTab='Repasar';renderModalStudy()")
    check("document.getElementById('learningBody').textContent.includes('errores pendientes')",'repaso de fallos y estadísticas por tema')
    js("learningState().cards['models::fuzzy']=StudyEngine.schedule(null,1);data.answers['legacy-qa']='conservar';window.backup=JSON.stringify({schema:1,data});window.confirm=()=>true")
    cmd('POST','/execute/async',{'script':"const done=arguments[arguments.length-1];importState(new File([window.backup],'qa.json')).then(()=>done(true));",'args':[]})
    check("data.learning.cards['models::fuzzy'].rating===1&&data.answers['legacy-qa']==='conservar'",'importación conserva progreso nuevo y antiguo')
    js("startSingle('M04')")
    check("document.querySelector('[data-launch-orange]')&&document.querySelector('[data-resource=ows]')&&getComputedStyle(document.getElementById('answerEditor')).display==='none'",'Orange con apertura, descargas y sin Python obligatorio')
    cmd('POST','/execute/async',{'script':"const done=arguments[arguments.length-1];localTools().then(v=>done(v.orange.available)).catch(e=>done({error:e.message}));",'args':[]})
    js("startSingle('S04');document.getElementById('jsonAnswer').value='{invalid';document.getElementById('validateDSL').click()")
    check("document.getElementById('dslStatus').textContent.includes('no válido')",'editor JSON detecta sintaxis incorrecta')
    js("document.getElementById('jsonAnswer').value='{}';document.getElementById('validateDSL').click()")
    check("document.getElementById('dslStatus').textContent.includes('pendientes de comprobar')",'validación JSON no simula ejecución Elasticsearch')
    for width in [320,390,768,1440]:
        cmd('POST','/window/rect',{'width':width,'height':950})
        js("selectCourse('models');learningTab='Aprender';renderModalStudy()")
        check('document.documentElement.scrollWidth<=window.innerWidth+1',f'teoría responsive {width}px')
    cmd('POST','/url',{'url':Path(__file__).with_name('index.html').resolve().as_uri()})
    check("typeof LOCAL_TOOL_TOKEN==='undefined'",'standalone y alojado sin credencial de ejecución local')
    result=cmd('POST','/execute/async',{'script':"const done=arguments[arguments.length-1];localTools(true).then(()=>done('unexpected')).catch(e=>done(e.message));",'args':[]})
    assert 'Puente local no activo' in result
    print('PASS ausencia de bridge: error comprensible, sin fingir apertura local')
    errors=[e for e in cmd('POST','/log',{'type':'browser'}) if e['level']=='SEVERE']
    assert not errors,errors
    print('PASS cero errores JS')
finally:cmd('DELETE','')
