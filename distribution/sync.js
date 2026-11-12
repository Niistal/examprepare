// Per-page memory only. Server sessions select the account; clients cannot select a user ID.
const cloudStorage=(()=>{
 let value=JSON.stringify(CLOUD_BOOTSTRAP.state),revision=CLOUD_BOOTSTRAP.revision;
 let saved=value,running=false,conflict=false,timer=null,inflight=null;
 function status(message){const el=document.getElementById('cloudStatus');if(el)el.textContent=message;}
 async function perform(){
  if(running||conflict)return false;
  if(value===saved)return true;
  running=true;status('Guardando en tu cuenta…');
  try{
   while(value!==saved){
    const snapshot=value;
    const r=await fetch('/api/progress',{method:'PUT',headers:{'Content-Type':'application/json','X-CSRF-Token':CLOUD_BOOTSTRAP.csrf},body:JSON.stringify({revision,state:JSON.parse(snapshot)})});
    if(r.status===409){
     // A lost response may have committed our exact snapshot. Reconcile without overwriting.
     const current=await fetch('/api/progress');if(!current.ok)throw Error('No se pudo comprobar el progreso');
     const remote=await current.json();
     if(JSON.stringify(remote.state)!==snapshot){conflict=true;throw Error('Conflicto entre dispositivos. Exporta tus respuestas y recarga para ver la otra versión.');}
     revision=remote.revision;saved=snapshot;
    }else{if(!r.ok)throw Error(r.status===401?'Sesión caducada. Exporta tus respuestas antes de entrar de nuevo.':'No se pudo guardar. Reintenta o exporta tus respuestas.');revision=(await r.json()).revision;saved=snapshot;}
   }
   status('Progreso guardado en tu cuenta');return true;
  }catch(e){status(e.message);return false;}finally{running=false;}
 }
 function flush(){if(inflight)return inflight;inflight=perform().finally(()=>{inflight=null;});return inflight;}
 window.addEventListener('beforeunload',e=>{if(value!==saved){e.preventDefault();e.returnValue='';}});
 window.addEventListener('online',()=>flush());
 window.addEventListener('DOMContentLoaded',()=>{
  const bar=document.createElement('section');bar.style.cssText='padding:12px;background:#163628;color:white;position:sticky;top:0;z-index:100';bar.setAttribute('aria-label','Tu cuenta');
  const name=document.createElement('b');name.textContent=CLOUD_BOOTSTRAP.username+' · ';
  const label=document.createElement('span');label.id='cloudStatus';label.role='status';label.textContent='Progreso guardado en tu cuenta';
  const retry=document.createElement('button');retry.textContent='Reintentar guardado';retry.onclick=()=>flush();
  const logout=document.createElement('button');logout.textContent='Cerrar sesión';logout.onclick=async()=>{if(!await flush())return;const r=await fetch('/api/logout',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':CLOUD_BOOTSTRAP.csrf},body:'{}'});if(r.ok)location.assign('/login');else status('No se pudo cerrar sesión; reintenta.');};
  const recovery=document.createElement('button');recovery.textContent='Código de recuperación';
  recovery.onclick=()=>{
   const dialog=document.createElement('dialog'),form=document.createElement('form'),heading=document.createElement('h2'),input=document.createElement('input'),generate=document.createElement('button'),close=document.createElement('button'),output=document.createElement('p');
   heading.textContent='Guardar o renovar tu código';input.type='password';input.autocomplete='current-password';input.required=true;input.minLength=12;input.maxLength=256;input.placeholder='Contraseña actual';input.setAttribute('aria-label','Contraseña actual');generate.textContent='Generar código';close.textContent='Cerrar';close.type='button';close.onclick=()=>dialog.close();output.setAttribute('role','status');output.style.overflowWrap='anywhere';
   form.onsubmit=async e=>{e.preventDefault();generate.disabled=true;try{const r=await fetch('/api/recovery-code',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':CLOUD_BOOTSTRAP.csrf},body:JSON.stringify({password:input.value})});input.value='';const result=await r.json();output.textContent=r.ok?'Guárdalo en un lugar privado. Sustituye al anterior: '+result.recovery_code:result.error;}catch{output.textContent='No se pudo conectar; reintenta.';}finally{generate.disabled=false;}};
   form.append(heading,input,generate,close,output);dialog.append(form);dialog.addEventListener('close',()=>dialog.remove());document.body.append(dialog);dialog.showModal();input.focus();
  };
  bar.append(name,label,' ',retry,' ',recovery,' ',logout);document.body.prepend(bar);
 });
 return {getItem:()=>value,setItem:(_,next)=>{value=next;status('Pendiente de sincronizar…');clearTimeout(timer);timer=setTimeout(flush,400);},flush};
})();
