'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const root=__dirname,read=file=>JSON.parse(fs.readFileSync(root+'/'+file,'utf8'));
const es=read('learning-content.json'),eu=read('locales/learning.eu.json'),engine=require('./learning-engine.js');
assert.equal(eu.schema,es.schema);assert.equal(eu.version,es.version);assert.equal(eu.academicCommit,es.academicCommit);
for(const group of ['lessons','questions']){
 assert.equal(eu[group].length,es[group].length);
 eu[group].forEach((entry,i)=>{
  const original=es[group][i];
  for(const field of ['id','course','topic','difficulty','type','modality','version','source','authorship','difficultyEvidence'])assert.deepEqual(entry[field],original[field],entry.id+' '+field);
  if(group==='questions'){
   if(entry.type==='term')assert(original.answer.every(answer=>entry.answer.includes(answer)));
   else assert.deepEqual(entry.answer,original.answer,entry.id+' correction unchanged');
   for(const key of ['options','left','criteria'])if(original[key])assert.equal(entry[key].length,original[key].length);
   assert.equal(engine.grade(entry,entry.type==='term'?entry.answer[0]:entry.answer).correct,entry.type==='open'?null:true);
   assert.notEqual(entry.prompt,original.prompt,entry.id+' prompt translated');
   assert.notEqual(entry.explanation,original.explanation,entry.id+' explanation translated');
  }else for(const field of ['concept','real','comparison','recall'])assert.notEqual(entry[field],original[field],entry.id+' '+field+' translated');
 });
}
const ui=read('locales/ui.eu.json'),cases=read('locales/cases.eu.json');
for(const dict of [ui,cases])for(const [key,value]of Object.entries(dict)){
 assert.equal(typeof value,'string');assert(value.trim(),key);
 assert.deepEqual((key.match(/\{\d+\}/g)||[]).sort(),(value.match(/\{\d+\}/g)||[]).sort(),key+' interpolation unchanged');
}
// Exercise the real content loader without a DOM or browser progress.
const elements=()=>null;
const context={console,document:{getElementById:elements},localStorage:{getItem:()=>null},EUSKARA_UI:ui,EUSKARA_CASES:cases,EUSKARA_LEARNING:eu};
vm.createContext(context);
vm.runInContext(fs.readFileSync(root+'/app.js','utf8').replace(/init\(\);\s*$/,''),context);
const before=vm.runInContext('JSON.parse(JSON.stringify(BANK))',context);
const runtime=fs.readFileSync(root+'/i18n.js','utf8');
vm.runInContext(runtime.slice(runtime.indexOf('function translateContent('),runtime.indexOf('function translateElement(')),context);
vm.runInContext('translateContent(BANK)',context);
const after=vm.runInContext('JSON.parse(JSON.stringify(BANK))',context);
assert.equal(after.length,84);
for(let i=0;i<before.length;i++){
 const a=before[i],b=after[i];
 for(const key of ['id','c','level','kind','starter','dataset','dataset_name','source_path','source_section','source_git_blob','source_sha256'])assert.deepEqual(b[key],a[key],a.id+' '+key);
 for(const key of ['title','prompt','hint','why'])assert.notEqual(b[key],a[key],a.id+' '+key+' translated');
 const technicalChecks=new Set(['mean(axis=0), std(axis=0)','how="left"','FPR = FP/(FP+TN)','FNR = FN/(FN+TP)','docker compose up -d','docker compose ps/logs/down','Faker locale es_ES','Provenance/data lineage']);
 for(let n=0;n<a.checks.length;n++)if(!technicalChecks.has(a.checks[n]))assert.notEqual(b.checks[n],a.checks[n],a.id+' check '+n+' translated');
 if(/\b(import |from \w+ import|def |class |SELECT |GET |POST |docker |print\(|pd\.|np\.)/.test(a.solution))assert.equal(b.solution,a.solution,a.id+' executable solution preserved');
}
console.log('PASS Euskara: 20 lessons, 106 questions, 84 cases; original grading, IDs, source provenance and executable code preserved');

const translationContext={EUSKARA_UI:ui,EUSKARA_CASES:cases,EUSKARA_LEARNING:eu,document:{cookie:''}};
vm.createContext(translationContext);vm.runInContext(fs.readFileSync(root+'/i18n.js','utf8'),translationContext);
const translate=value=>vm.runInContext('translateText('+JSON.stringify(value)+')',translationContext);
assert.equal(translate('Kafka: topics: — % · 0 dominadas · 5 pendientes · Autoevaluación de tema: Sin valorar'),'Kafka: topics: % — · 0 menderatuta · 5 zain · Gaiaren autoebaluazioa: Baloratu gabe');
assert.equal(translate('Sin intentos · 0 dominadas · 5 pendientes'),'Saiakerarik gabe · 0 menderatuta · 5 zain');
assert.equal(translate('Cuenta de Correcto'),'Correcto erabiltzailearen kontua');
for(const value of ['Sin intentos · 0 dominadas · 5 pendientes','Fuente contrastada · path/README.md','0% dominado'])assert.equal(translate(translate(value)),translate(value));
console.log('PASS dynamic labels, titles with punctuation, account identity and translation idempotence');

for(const [spanish,basque] of Object.entries({'LUN 16':'AL. 16','MAR 17':'AR. 17','MIÉ 18':'AZ. 18','JUE 19':'OG. 19','LUN 23':'AL. 23'})){assert.equal(translate(spanish),basque);assert.equal(translate(spanish+' NOV'),basque+' AZA.');}
console.log('PASS weekday abbreviations in Euskara dashboard');
