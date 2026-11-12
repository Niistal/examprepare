/** Real private publication smoke. Token only via hidden stdin; scoped CDP interception.
 * Own ephemeral browser session; never uses the owner's profile or writes credentials.
 */
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {createInterface} from 'node:readline/promises';
const policy=JSON.parse(readFileSync(new URL('../../deployment/sync-policy.json',import.meta.url),'utf8'));
const expectedMaterials=JSON.parse(readFileSync(new URL('../materials.json',import.meta.url),'utf8')).resources.length;
const expectedBank=JSON.parse(spawnSync(process.execPath,[fileURLToPath(new URL('export_bank.cjs',import.meta.url))],{encoding:'utf8'}).stdout).length;
const origin=policy.site_origin,driver='http://127.0.0.1:9515';
let stage='receive',sid,ws,token,interceptErrors=0,exceptions=0,securityEntries=0;
const rpcPending=new Map();let rpcId=0;
async function http(method,path,value){
 const r=await fetch(driver+path,{method,headers:{'Content-Type':'application/json'},body:value===undefined?undefined:JSON.stringify(value),signal:AbortSignal.timeout(30000)});
 const result=(await r.json()).value;if(result?.error)throw Error('Browser operation failed');return result;
}
function rpc(method,params={}){return new Promise((resolve,reject)=>{const id=++rpcId;const timer=setTimeout(()=>{rpcPending.delete(id);reject(Error('CDP timeout'));},method==='Runtime.evaluate'?180000:15000);rpcPending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params}));});}
async function js(expression){const r=await rpc('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error('Application evaluation failed');return r.result?.value;}
async function check(expression,label){if(!await js('Boolean('+expression+')'))throw Error('Smoke assertion failed');console.log('PASS '+label);}
async function ready(){for(let i=0;i<200;i++){if(await js(`document.readyState==='complete' && typeof BANK!=='undefined' && BANK.length===${expectedBank}`))return;await new Promise(r=>setTimeout(r,100));}throw Error('Application load timeout');}
try{
 if(new URL(origin).protocol!=='https:'||new URL(origin).hostname!=='niis-study-lab.ikernistal77.chatgpt.site')throw Error('Wrong Site');
 if(process.stdin.isTTY&&spawnSync('stty',['-echo'],{stdio:['inherit','ignore','ignore']}).status!==0)throw Error('Cannot hide input');
 console.log('Ready for private smoke JSON on stdin (input hidden).');
 const input=createInterface({input:process.stdin,terminal:false});let data;
 try{data=JSON.parse(await input.question(''));}finally{input.close();if(process.stdin.isTTY)spawnSync('stty',['echo'],{stdio:['inherit','ignore','ignore']});}
 if(data.origin!==origin||typeof data.token!=='string'||data.token.length<20)throw Error('Missing scoped access');token=data.token;data=null;
 stage='browser';const session=await http('POST','/session',{capabilities:{alwaysMatch:{browserName:'chrome','goog:chromeOptions':{args:['--headless=new','--no-sandbox','--disable-dev-shm-usage']}}}});sid=session.sessionId;
 await http('POST',`/session/${sid}/timeouts`,{pageLoad:20000,script:15000});
 const debug=session.capabilities['goog:chromeOptions'].debuggerAddress;
 if(!/^(?:localhost|127\.0\.0\.1):\d+$/.test(debug))throw Error('Nonlocal debugger');
 const protocol=await (await fetch('http://'+debug+'/json/protocol')).json();
 const description=protocol.domains.find(d=>d.domain==='Fetch')?.commands.find(c=>c.name==='continueRequest')?.parameters.find(p=>p.name==='headers')?.description||'';
 stage='redirect_scope';if(!description.replace(/\s+/g,' ').includes('do not extend to subsequent redirect hops'))throw Error('Redirect isolation not confirmed by local CDP protocol');
 stage='debug_target';const targets=await (await fetch('http://'+debug+'/json/list')).json();const target=targets.find(t=>t.type==='page');const socketURL=new URL(target.webSocketDebuggerUrl);
 if(!['localhost','127.0.0.1'].includes(socketURL.hostname)||socketURL.port!==new URL('http://'+debug).port)throw Error('Nonlocal target');
 stage='websocket';ws=new WebSocket(socketURL);await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',()=>reject(Error('CDP unavailable')),{once:true});});
 ws.addEventListener('message',async event=>{
  const m=JSON.parse(event.data);
  if(m.id){const p=rpcPending.get(m.id);if(p){clearTimeout(p.timer);rpcPending.delete(m.id);m.error?p.reject(Error('CDP operation failed')):p.resolve(m.result);}return;}
  if(m.method==='Runtime.exceptionThrown')exceptions++;
  if(m.method==='Log.entryAdded'&&m.params.entry.source==='security')securityEntries++;
  if(m.method==='Fetch.requestPaused'){
   try{
    const p=m.params;if(new URL(p.request.url).origin!==origin){await rpc('Fetch.failRequest',{requestId:p.requestId,errorReason:'BlockedByClient'});return;}
    const headers=Object.entries(p.request.headers).filter(([name])=>name.toLowerCase()!=='oai-sites-authorization').map(([name,value])=>({name,value:String(value)}));
    headers.push({name:'OAI-Sites-Authorization',value:'Bearer '+token});
    await rpc('Fetch.continueRequest',{requestId:p.requestId,headers});
   }catch{interceptErrors++;}
  }
 });
 stage='interception';await rpc('Runtime.enable');await rpc('Log.enable');await rpc('Fetch.enable',{patterns:[{urlPattern:origin+'/*',requestStage:'Request'}]});
 stage='published_load';await http('POST',`/session/${sid}/url`,{url:origin+'/'});await ready();
 await check(`BANK.length===${expectedBank} && MATERIALS.resources.length===${expectedMaterials}`,'banco y temario reales publicados');
 await js("startSingle('P20');document.getElementById('answerEditor').value='borrador temporal de QA privada';persistDraft()");
 await check("!document.getElementById('givenReference').classList.contains('hidden')",'referencia dada visible');
 stage='reload';await http('POST',`/session/${sid}/refresh`,{});await ready();
 await check("document.getElementById('answerEditor').value==='borrador temporal de QA privada'",'recarga publicada conserva borrador temporal');
 await js("document.getElementById('examMode').value='exam';document.getElementById('examNumber').value='17';startExam()");
 await check("session.ids.length===5 && document.getElementById('solutionToggle').disabled",'examen publicado bloquea soluciones');
 await js("document.getElementById('answerEditor').value='respuesta temporal';persistDraft();switchQuestion(1);switchQuestion(0)");
 await check("document.getElementById('answerEditor').value==='respuesta temporal'",'navegación publicada conserva respuesta');
 await js("window.confirm=()=>true;finishExam()");
 await check("session.submitted && !document.getElementById('solutionToggle').disabled",'entrega publicada desbloquea corrección');
 for(const id of ['program','ml','models','systems','applied']){
  await js(`selectCourse('${id}');setStudyView('materials');document.getElementById('materialType').value='all';renderMaterials()`);
  await check(`[...document.querySelectorAll('.material-item')].every(e=>e.dataset.course==='${id}')`,'asignación publicada '+id);
 }
 if(process.argv.includes('--runner')){
  stage='python_runner';await js("startSingle('P01');document.getElementById('answerEditor').value=\"print('run privado', 2+3)\";runPython()");
  const result=await js("new Promise(resolve=>{let n=0;const timer=setInterval(()=>{if(!pythonWorker||++n>650){clearInterval(timer);resolve({text:document.getElementById('runOutput').textContent,status:document.getElementById('runStatus').textContent})}},200)})");
  if(!result.text.includes('run privado 5'))throw Error('Published Python run failed');console.log('PASS Python real en Site privado');
 }
 if(interceptErrors||exceptions)throw Error('Runtime/interception error');
 console.log(JSON.stringify({status:'verified',scope:'Sesión de servicio temporal, no login/MFA del propietario',credential_scope:'Solo origen del Site; overrides sin propagación en redirects',app_runtime_exceptions:exceptions,security_console_entries:securityEntries,edge_note:'La detección de Cloudflare permanece sujeta a CSP; no se relaja para la prueba'}));
}catch{console.log(JSON.stringify({status:'not_verified',stage}));process.exitCode=1;}
finally{
 token=null;ws?.close();for(const p of rpcPending.values()){clearTimeout(p.timer);p.reject(Error('Session closed'));}rpcPending.clear();
 if(sid)try{await http('DELETE',`/session/${sid}`);}catch{}
}
