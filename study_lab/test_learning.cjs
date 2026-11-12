// Regressions for learning coverage, rendered copy and progress safety. No dependencies.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const elements={};let raw=null,failWrites=false;
const element=id=>elements[id]??=( {innerHTML:'',textContent:'',classList:{add(){},remove(){},toggle(){}},querySelectorAll:()=>[]} );
const context={console,document:{getElementById:element},localStorage:{getItem:()=>raw,setItem:(_,value)=>{if(failWrites)throw Error('quota');raw=value;}},setTimeout:()=>0,clearTimeout(){}};
context.assert=(value,message)=>{if(!value)throw Error(message);console.log('PASS',message);};
let source=fs.readFileSync(path.join(__dirname,'app.js'),'utf8').replace(/\ninit\(\);\s*$/,'');
source+=`
for(const c of COURSES){
 courseId=c.id;
 assert(STUDY_LESSONS[c.id].length===STUDY_ROUTES[c.id].length,'Teoría para cada bloque: '+c.id);
 renderStudyRoute();
 const html=$('studyRoute').innerHTML;
 assert(!html.includes('$'+'{'),'Sin código de plantilla visible: '+c.id);
 assert(html.includes(STUDY_METHODS[c.id]),'Método real de la materia: '+c.id);
 assert(STUDY_LESSONS[c.id].every(x=>x.concept&&x.example&&x.recall&&x.trap),'Lecciones completas: '+c.id);
}
for(const id of ['P06','P12','P20','M08','E02','E03','E06','A11'])assert(BANK.find(q=>q.id===id).references.length>0,'Referencia facilitada: '+id);
assert(!BANK.find(q=>q.id==='M08').prompt.includes('a mano o'),'Métricas sin fórmula memorizada');
data=emptyState();data.ratings={P01:0,P02:1,P03:2};data.history=[{id:'P03',rating:2,date:'2026-11-01T00:00:00Z'}];
assert(reviewCandidates(Date.parse('2026-11-12T00:00:00Z')).slice(0,3).map(q=>q.id).join(',')==='P01,P02,P03','Repaso ordenado y recuperación espaciada');
assert(nextStudyId('program')==='P04','Siguiente caso del recorrido, sin nivel artificial');
assert(validState(data),'Compatibilidad con respaldo V1');
assert(!validState({ratings:{P01:3},answers:{},history:[]})&&!validState({ratings:{},answers:{P01:null},history:[]}), 'Rechazo de datos inválidos');
data=emptyState();assert(save(),'Primer guardado');
const original=localStorage.getItem(STATE_KEY);
localStorage.setItem(STATE_KEY,JSON.stringify({ratings:{P01:2},answers:{},history:[]}));
assert(!save()&&storageConflict,'Detecta escritura de otra pestaña');
assert(localStorage.getItem(STATE_KEY)!==original,'No sobrescribe progreso ajeno');
allowExplicitReplace();data=emptyState();assert(save(),'Recuperación explícita tras conflicto');
`;
vm.runInNewContext(source,context);
failWrites=true;
vm.runInNewContext(`assert(!save()&&!storageOkay,'Cuota llena deja estado sin guardar visible');`,context);
failWrites=false;
raw='{contenido roto';
vm.runInNewContext(`readState();assert(storageConflict&&invalidStored!==null,'Progreso dañado activa recuperación');assert(!save(),'No sobrescribe datos dañados');`,context);
console.log('PASS integridad del aprendizaje y persistencia');
