"""Real Chromium checks for shared course reading; no GitHub session or personal profile."""
import base64,json,os,urllib.request,urllib.error
from pathlib import Path
BASE=os.environ.get('NIIS_DRIVER_URL','http://127.0.0.1:9515')
def request(method,path,body=None):
    r=urllib.request.Request(BASE+path,method=method,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
    try:value=json.load(urllib.request.urlopen(r,timeout=60))['value']
    except urllib.error.HTTPError as e:raise AssertionError(e.read().decode()) from e
    if isinstance(value,dict) and value.get('error'):raise AssertionError(value)
    return value
session=request('POST','/session',{'capabilities':{'alwaysMatch':{'browserName':'chrome','goog:chromeOptions':{'binary':'/usr/bin/chromium','args':['--headless=new','--no-sandbox','--disable-dev-shm-usage','--window-size=1440,1000']},'goog:loggingPrefs':{'browser':'ALL'}}}})['sessionId']
def cmd(method,path,body=None):return request(method,'/session/'+session+path,body)
def js(text):return cmd('POST','/execute/sync',{'script':text,'args':[]})
def asyncjs(text):return cmd('POST','/execute/async',{'script':text,'args':[]})
def check(expr,label):assert js('return Boolean('+expr+')'),label;print('PASS',label)
try:
    cmd('POST','/url',{'url':os.environ.get('NIIS_TEST_URL','http://127.0.0.1:8097')})
    # Legacy assertions exercise the preserved Spanish edition; Euskara has its own suite.
    js("document.cookie='study_language=es-ES; Path=/';location.reload()")
    js("selectCourse('models');setStudyView('materials')")
    check("document.querySelector('[data-read-material]')&&!document.querySelector('#materialList a[href*=github]')",'temario tiene lectura interna, sin enviar a GitHub')
    asyncjs("const done=arguments[arguments.length-1];loadMaterialReader().then(()=>done(true)).catch(e=>done(e.message));")
    for course in ['program','ml','models','systems','applied']:
        asyncjs("const done=arguments[arguments.length-1];const r=MATERIALS.resources.find(r=>r.course==='"+course+"'&&r.extension==='.md'&&materialReaderData.documents[r.id].text.length>100&&materialReaderData.documents[r.id].toc.length);openMaterialReader(r.id).then(()=>done(true));")
        check("document.getElementById('materialReader').open&&document.getElementById('readerBody').textContent.length>100&&document.querySelector('#readerBody h1,#readerBody h2,#readerBody h3,#readerBody h4')",'Markdown real visible: '+course)
        js("document.getElementById('materialReader').close()")
    asyncjs("const done=arguments[arguments.length-1];const id=Object.keys(materialReaderData.documents).find(id=>materialReaderData.documents[id].html.includes('<table>')&&materialReaderData.documents[id].html.includes('<math '));openMaterialReader(id).then(()=>done(true));")
    check("document.querySelector('#readerBody table')&&document.querySelector('#readerBody math')",'tablas y fórmulas MathML nativas visibles')
    js("document.getElementById('materialReader').close();startSingle('E03');document.getElementById('sourceLink').click()")
    check("document.getElementById('materialReader').open&&!location.hostname.includes('github')",'fuentes de ejercicios también se leen dentro de la web')
    js("document.getElementById('materialReader').close()")
    asyncjs("const done=arguments[arguments.length-1];const id=Object.keys(materialReaderData.documents).find(id=>materialReaderData.documents[id].format==='.md'&&materialReaderData.documents[id].html.includes('data-read-material'));openMaterialReader(id).then(()=>done(true));")
    check("document.querySelector('#readerBody [data-read-material]')",'enlaces relativos de Markdown enlazan recursos internos')
    js("window.oldReader=materialReaderCurrent;document.querySelector('#readerBody [data-read-material]').click()")
    check("materialReaderCurrent!==window.oldReader",'navegación entre apuntes sin GitHub')
    js("document.getElementById('materialReader').close()")
    if js("return typeof MATERIAL_ASSET_BASE!=='undefined'"):
        result=asyncjs("const done=arguments[arguments.length-1];window.pdf=MATERIALS.resources.find(r=>r.extension==='.pdf'&&materialReaderData.documents[r.id].originalAvailable);fetch(materialAssetURL(pdf.id),{headers:{Range:'bytes=0-3'}}).then(async r=>done({status:r.status,bytes:await r.text()}));")
        assert result=={'status':206,'bytes':'%PDF'},result
        print('PASS PDF original servido desde la aplicación con Range real')
        asyncjs("const done=arguments[arguments.length-1];openMaterialReader(pdf.id).then(()=>done(true));")
        js("document.getElementById('readerOriginal').click()")
        check("document.querySelector('#readerBody iframe').src.startsWith(location.origin+'/api/materials/')",'visor del PDF original usa el mismo servidor')
        js("document.getElementById('materialReader').close()")
    else:
        print('SKIP originales nativos: paquete binario no instalado; lectura completa verificada')
    asyncjs("const done=arguments[arguments.length-1];const r=MATERIALS.resources.find(r=>r.course==='models'&&r.extension==='.md'&&materialReaderData.documents[r.id].text.length>100&&materialReaderData.documents[r.id].toc.length);openMaterialReader(r.id).then(()=>done(true));")
    for width in [320,390,768,1440]:
        cmd('POST','/window/rect',{'width':width,'height':950})
        check("document.documentElement.scrollWidth<=innerWidth+1&&document.getElementById('materialReader').scrollWidth<=document.getElementById('materialReader').clientWidth+1",'lector responsive '+str(width))
    screenshot=cmd('GET','/screenshot');folder=Path(__file__).with_name('qa-artifacts');folder.mkdir(exist_ok=True);(folder/'material-reader.png').write_bytes(base64.b64decode(screenshot))
    js("document.getElementById('materialReader').close();startSingle('P28')")
    check("!document.getElementById('answerEditor').classList.contains('hidden')&&pythonCase(currentQuestion())",'Programazioa conserva el editor y ejecución tras leer')
    errors=[x for x in cmd('POST','/log',{'type':'browser'}) if x['level']=='SEVERE'];assert not errors,errors
    print('PASS sin errores JS, sin sesión de GitHub')
finally:cmd('DELETE','')
