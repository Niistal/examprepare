"""Prueba opcional del reloj real y borrador durante una sesión prolongada.

Usa su propia sesión temporal de ChromeDriver; no toca el perfil del usuario.
No forma parte de la suite rápida. Necesita web y ChromeDriver en loopback.
"""
import argparse,json,math,time,urllib.request
p=argparse.ArgumentParser();p.add_argument('--seconds',type=int,default=905);p.add_argument('--url',default='http://127.0.0.1:8080');p.add_argument('--driver',default='http://127.0.0.1:9515');args=p.parse_args()
if not 5<=args.seconds<=3600:p.error('--seconds debe estar entre 5 y 3600')
def request(method,path,data=None):
    req=urllib.request.Request(args.driver+path,data=json.dumps(data).encode() if data is not None else None,method=method,headers={'Content-Type':'application/json'})
    result=json.load(urllib.request.urlopen(req,timeout=30))['value']
    if isinstance(result,dict) and result.get('error'):raise RuntimeError(result['error'])
    return result
sid=request('POST','/session',{'capabilities':{'alwaysMatch':{'browserName':'chrome','goog:chromeOptions':{'args':['--headless=new','--no-sandbox','--disable-dev-shm-usage']},'goog:loggingPrefs':{'browser':'ALL'}}}})['sessionId'];base='/session/'+sid
def js(script):return request('POST',base+'/execute/sync',{'script':script,'args':[]})
try:
    request('POST',base+'/url',{'url':args.url})
    js("startSingle('P01');document.getElementById('answerEditor').value='borrador de prueba prolongada';persistDraft();startTimer();")
    initial=js('return {remaining:timeRemaining,deadline:timeDeadline}')
    started=time.monotonic();reloaded=False
    while True:
        elapsed=time.monotonic()-started
        if not reloaded and elapsed>=args.seconds/2:
            js('location.reload()');reloaded=True
        state=js("return {remaining:timeRemaining,running:timeInterval!==null,draft:document.getElementById('answerEditor').value,deadline:timeDeadline,stored:JSON.parse(localStorage.getItem(STATE_KEY)).answers['single-P01::P01']}")
        expected=max(0,math.ceil((initial['deadline']-time.time()*1000)/1000))
        assert abs(state['remaining']-expected)<=2,'El reloj deriva respecto a su deadline'
        assert state['draft']==state['stored']=='borrador de prueba prolongada','Borrador alterado'
        if expected==0:assert not state['running'],'El reloj no se detuvo al agotarse'
        print(json.dumps({'elapsed_seconds':round(elapsed),'remaining':state['remaining'],'draft_preserved':True,'reload_verified':reloaded}),flush=True)
        if elapsed>=args.seconds:break
        time.sleep(min(55,args.seconds-elapsed))
    errors=[x for x in request('POST',base+'/log',{'type':'browser'}) if x.get('level')=='SEVERE']
    assert not errors,[(x.get('source'),x.get('message','')[:400]) for x in errors]
    print('PASS sesión prolongada: deadline real, recarga y borrador íntegros',flush=True)
finally:request('DELETE',base)
