'use strict';
let materialReaderPromise=null,materialReaderData=null,materialReaderCurrent=null,materialReaderReturnFocus=null;
async function loadMaterialReader(){
 if(materialReaderData)return materialReaderData;
 if(!materialReaderPromise)materialReaderPromise=(async()=>{
  if(typeof DecompressionStream==='undefined')throw Error('Este navegador no admite el lector comprimido. Usa una versión actual de Firefox, Chrome, Edge o Safari.');
  const bytes=Uint8Array.from(atob(MATERIAL_READER_BUNDLE.data),x=>x.charCodeAt(0));
  const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
  const body=JSON.parse(await new Response(stream).text());
  if(body.catalogFingerprint!==MATERIALS.fingerprint)throw Error('La copia del temario y el catálogo no coinciden. Regenera la biblioteca antes de publicarla.');
  materialReaderData=body;return body;
 })().catch(e=>{materialReaderPromise=null;throw e;});
 return materialReaderPromise;
}
function materialFromURL(url){
 try{const u=new URL(url,location.href);if(u.hostname!=='github.com')return null;const match=u.pathname.match(/^\/Niistal\/Big_Data\/(?:blob|tree)\/(?:main|[a-f0-9]{40})\/(.+)$/);if(!match)return null;const path=decodeURIComponent(match[1]).replace(/\/$/,'');return MATERIALS.resources.find(r=>r.path===path)||MATERIALS.resources.find(r=>r.path.startsWith(path+'/')&&r.extension==='.md');}catch{return null;}
}
function materialAssetURL(id,download=false){return typeof MATERIAL_ASSET_BASE!=='undefined'?MATERIAL_ASSET_BASE+encodeURIComponent(id)+(download?'?download=1':''):null;}
function materialBodyText(id){return materialReaderData?.documents[id]?.text||'';}
async function openMaterialReader(id){
 const resource=MATERIALS.resources.find(r=>r.id===id);if(!resource)return;
 const dialog=$('materialReader');materialReaderReturnFocus=document.activeElement;materialReaderCurrent=id;
 $('readerTitle').textContent=resource.title;$('readerPath').textContent=resource.path;$('readerBody').textContent='Preparando la lectura…';$('readerTOC').innerHTML='';$('readerNotice').textContent='';
 if(!dialog.open)dialog.showModal();$('readerTitle').focus();
 try{
  const library=await loadMaterialReader();if(materialReaderCurrent!==id)return;
  const document=library.documents[id];if(!document)throw Error('Este recurso no está en la copia del temario.');
  $('readerRevision').textContent=`Copia del repositorio · ${library.source.commit.slice(0,8)} · ${resource.type}`;
  $('readerNotice').textContent=document.notices.join(' ');
  $('readerBody').innerHTML=document.html||'<p>Este recurso se consulta en su formato original usando el botón «Ver original».</p>';
  $('readerTOC').innerHTML=document.toc.map(h=>`<button type="button" data-reader-section="${h.id}" class="toc-level-${h.level}">${esc(h.title)}</button>`).join('');
  $('readerTOC').classList.toggle('hidden',!document.toc.length);
  const url=document.originalAvailable?materialAssetURL(id):null;
  $('readerOriginal').disabled=!url;$('readerDownload').classList.toggle('hidden',!url);
  if(url){$('readerDownload').href=materialAssetURL(id,true);$('readerDownload').download=resource.path.split('/').pop();}
  if(!url)$('readerNotice').textContent+=(document.originalAvailable?' Los archivos originales requieren el paquete de materiales instalado en el servidor; la lectura de los apuntes está incluida.':' El original no se distribuye porque se han detectado valores con formato de credenciales.');
  $('readerBody').querySelectorAll('[data-material-image]').forEach(img=>{const source=materialAssetURL(img.dataset.materialImage);if(source)img.src=source;else{img.alt=(img.alt||'Figura')+' · disponible con el paquete de materiales';}});
  $('readerTOC').querySelectorAll('[data-reader-section]').forEach(b=>b.onclick=()=>$('readerBody').querySelector('#'+b.dataset.readerSection)?.scrollIntoView({behavior:'smooth',block:'start'}));
  $('readerOriginal').onclick=()=>showMaterialOriginal(resource,url);
  $('readerText').onclick=()=>{const blob=new Blob([document.text],{type:'text/plain;charset=utf-8'});const u=URL.createObjectURL(blob),a=window.document.createElement('a');a.href=u;a.download=resource.path.split('/').pop()+'.lectura.txt';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);};
  $('readerText').disabled=!document.text;
  const index=MATERIALS.resources.filter(r=>r.course===resource.course&&['.md','.pdf','.ipynb','.docx','.pptx','.txt','.odt','.odp'].includes(r.extension));const position=index.findIndex(r=>r.id===id);
  $('readerPrev').disabled=position<=0;$('readerNext').disabled=position<0||position===index.length-1;
  $('readerPrev').onclick=()=>openMaterialReader(index[position-1].id);$('readerNext').onclick=()=>openMaterialReader(index[position+1].id);
 }catch(e){$('readerBody').textContent=e.message;$('readerOriginal').disabled=true;$('readerText').disabled=true;$('readerDownload').classList.add('hidden');}
}
function showMaterialOriginal(resource,url){
 if(!url)return;
 const body=$('readerBody');body.replaceChildren();
 if(resource.extension==='.pdf'){const frame=document.createElement('iframe');frame.src=url;frame.title=resource.title;frame.className='reader-pdf';body.append(frame);}
 else if(['.m4a','.mp4'].includes(resource.extension)){const media=document.createElement(resource.extension==='.mp4'?'video':'audio');media.controls=true;media.preload='metadata';media.src=url;body.append(media);}
 else if(resource.extension==='.png'){const image=document.createElement('img');image.src=url;image.alt=resource.title;body.append(image);}
 else{const a=document.createElement('a');a.href=materialAssetURL(resource.id,true);a.textContent='Descargar el archivo original desde esta web';a.className='btn btn-primary';body.append(a);}
 const back=document.createElement('button');back.className='btn btn-outline';back.textContent='Volver a la lectura';back.onclick=()=>openMaterialReader(resource.id);body.prepend(back);
}
function bootMaterialReader(){
 const dialog=$('materialReader');$('readerClose').onclick=()=>dialog.close();dialog.addEventListener('close',()=>{if(dialog.open)return;materialReaderCurrent=null;$('readerBody').replaceChildren();materialReaderReturnFocus?.focus?.();});
 document.addEventListener('click',e=>{
  const button=e.target.closest('[data-read-material]');if(button){e.preventDefault();openMaterialReader(button.dataset.readMaterial);return;}
  const link=e.target.closest('a[href]');if(link){const resource=materialFromURL(link.href);if(resource){e.preventDefault();openMaterialReader(resource.id);return;}}
  const anchor=e.target.closest('[data-reader-anchor]');if(anchor){e.preventDefault();const needle=anchor.dataset.readerAnchor.toLowerCase();const headers=[...$('readerBody').querySelectorAll('h1,h2,h3,h4,h5,h6')];const target=headers.find(h=>h.textContent.toLowerCase().replace(/[^\p{L}\p{N}\s-]/gu,'').replace(/\s/g,'-')===needle);target?.scrollIntoView({behavior:'smooth'});}
 });
 $('materialSnapshotLink').classList.add('hidden');
 // Decode only when the user opens resources, not during Python startup.
 $('materialView').addEventListener('click',()=>loadMaterialReader().then(()=>{if(studyView==='materials')renderMaterials();}).catch(e=>toast(e.message)));
}
