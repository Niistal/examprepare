"""QA real con Chromium/ChromeDriver; solo biblioteca estándar. Servidor en :8080, driver :9515."""
import json, os, urllib.request
BASE=os.environ.get('NIIS_DRIVER_URL','http://127.0.0.1:9515')
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
    # Legacy assertions exercise the preserved Spanish edition; Euskara has its own suite.
    js("document.cookie='study_language=es-ES; Path=/';location.reload()")
    check("calendarEvents.length===8 && new Set(calendarEvents.map(e=>e.id)).size===8",'ocho eventos únicos')
    check("NOVEMBER_EVENTS.filter(e=>e.type==='exam').length===5 && NOVEMBER_EVENTS[5].date==='2026-11-23' && NOVEMBER_EVENTS[5].time==='10:00'",'cinco exámenes y BDA corregido')
    check("NOVEMBER_EVENTS.filter(e=>!e.time).length===3 && !NOVEMBER_EVENTS[4].course",'huelga sin asignatura ni convocatoria inventada y horas desconocidas')
    check("examCountdown(NOVEMBER_EVENTS[0],Date.parse('2026-11-16T08:00:00+01:00'))==='Faltan 0 d · 1 h · 0 min' && examCountdown(NOVEMBER_EVENTS[4])===''",'cuenta atrás en horario de Madrid y aplazado sin cuenta atrás')
    js("window.qaProgress=localStorage.getItem(STATE_KEY);loadCalendar();loadCalendar()")
    check("JSON.parse(localStorage.getItem(CALENDAR_STORAGE_KEY)).length===8 && localStorage.getItem(STATE_KEY)===window.qaProgress",'persistencia idempotente conserva progreso')
    js("localStorage.setItem(CALENDAR_STORAGE_KEY,JSON.stringify([...calendarEvents,{id:'qa-extra',date:'2026-11-26',time:null,title:'Actividad guardada',type:'activity'}]));location.reload()")
    check("calendarEvents.length===9 && calendarEvents.some(e=>e.id==='qa-extra')",'recarga conserva eventos existentes')
    js("localStorage.setItem(CALENDAR_STORAGE_KEY,JSON.stringify(calendarEvents.filter(e=>e.id!=='qa-extra')));location.reload()")
    for width in [1440,390,320]:
        cmd('POST','/window/rect',{'width':width,'height':900})
        js("document.getElementById('calendarPanel').scrollIntoView({behavior:'instant'})")
        check("document.documentElement.scrollWidth<=innerWidth+1",str(width)+' px sin desbordamiento')
        check("document.querySelectorAll('.calendar-table tbody tr').length===8 && document.querySelectorAll('.calendar-week').length===2",'tabla y dos semanas completas')
        if width==390:
            check("getComputedStyle(document.querySelector('.calendar-table td')).display==='grid'",'tabla adaptada al móvil')
        import base64
        Path=__import__('pathlib').Path
        Path('/tmp/calendar-'+str(width)+'.png').write_bytes(base64.b64decode(cmd('GET','/screenshot')))
    js("localStorage.setItem(CALENDAR_STORAGE_KEY,'{invalid');location.reload()")
    check("localStorage.getItem(CALENDAR_STORAGE_KEY)==='{invalid' && calendarEvents.length===8 && !!document.querySelector('#calendarPanel [role=status]')",'datos dañados conservados y aviso visible')
    js("localStorage.removeItem(CALENDAR_STORAGE_KEY)")
finally:
    cmd('DELETE','')
