'use strict';
// Pure, versioned learning rules. Independent of the DOM and legacy progress.
const StudyEngine=(()=>{
 const MODES=Object.freeze(['THEORY','QUIZ','DEVELOPMENT','EXTERNAL_TOOL','MIXED']);
 const courses=Object.freeze({program:'DEVELOPMENT',ml:'MIXED',models:'MIXED',systems:'MIXED',applied:'MIXED'});
 // Explicit case mapping audited against each case, never inferred from teacher/title.
 const groups={DEVELOPMENT:['P01','P02','P03','P04','P05','P06','P07','P08','P09','P10','P11','P12','P13','P14','P15','P16','P17','P18','P19','P20','P21','P22','P23','P24','P25','P26','P27','P28','P29','P30','P31','P32','P33','P34','P35','P36','P37','P38','S08','A06','A07','A12'],THEORY:['E01','E02','E03','E04','E05','E06','E07','E08','E09','E10','E11','M07','M08','M11','S01','S02','S09','S11','S12','A03','A05','A08','A10','A11'],EXTERNAL_TOOL:['M01','M02','M03','M04','M05','M06','M09','M10','S03','S04','S05','S06','S07','S10','A01','A02','A04','A09']};
 const cases=Object.freeze(Object.fromEntries(Object.entries(groups).flatMap(([mode,ids])=>ids.map(id=>[id,mode]))));
 const normalize=v=>String(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim().toLowerCase().replace(/\s+/g,' ');
 function grade(q,value){
  if(q.type==='open')return {correct:null,review:true,criteria:q.criteria};
  if(q.type==='term')return {correct:q.answer.some(a=>normalize(a)===normalize(value))};
  if(['multiple','match','order'].includes(q.type)){
   if(!Array.isArray(value))return {correct:false};
   const actual=q.type==='multiple'?[...new Set(value)].sort((a,b)=>a-b):value;
   const expected=q.type==='multiple'?[...q.answer].sort((a,b)=>a-b):q.answer;
   return {correct:JSON.stringify(actual)===JSON.stringify(expected)};
  }
  return {correct:value===q.answer};
 }
 function migrate(state){
  // Keep all legacy keys, drafts, session, ratings and history byte-for-byte in meaning.
  return {...state,learning:{version:1,attempts:[],cards:{},...(state.learning||{})}};
 }
 function validLearning(v){
  const record=x=>x&&typeof x==='object'&&!Array.isArray(x);
  const quiz=q=>q===undefined||(record(q)&&typeof q.id==='string'&&typeof q.course==='string'&&typeof q.contentVersion==='string'&&['practice','exam'].includes(q.mode)&&typeof q.submitted==='boolean'&&typeof q.immediate==='boolean'&&(q.deadline===null||Number.isFinite(q.deadline))&&Array.isArray(q.ids)&&q.ids.length<=1000&&q.ids.every(id=>typeof id==='string')&&new Set(q.ids).size===q.ids.length&&record(q.answers)&&Object.values(q.answers).every(a=>a===null||['string','number','boolean'].includes(typeof a)||Array.isArray(a)&&a.every(x=>x===null||Number.isInteger(x)))&&record(q.recorded)&&Object.values(q.recorded).every(x=>typeof x==='boolean'));
  return v===undefined||(record(v)&&v.version===1&&quiz(v.quiz)&&Array.isArray(v.attempts)&&v.attempts.length<=10000&&v.attempts.every(a=>record(a)&&typeof a.id==='string'&&typeof a.date==='string'&&Number.isFinite(Date.parse(a.date))&&[true,false,null].includes(a.correct)&&Number.isInteger(a.version))&&record(v.cards)&&Object.values(v.cards).every(c=>record(c)&&[0,1,2].includes(c.rating)&&Number.isFinite(c.due)&&Number.isInteger(c.streak)&&c.streak>=0));
 }
 function schedule(previous,rating,now=Date.now()){
  const streak=rating===2?(previous?.streak||0)+1:0;
  const days=rating===0?0:rating===1?1:Math.min(30,2**streak);
  return {rating,streak,due:now+(rating===0?10*60*1000:days*86400000)};
 }
 function lastAttempts(attempts){const last=new Map();for(const a of attempts)last.set(a.id,a);return last;}
 function select(pool,count,seed,failedOnly=false,attempts=[]){
  const versions=new Map(pool.map(q=>[q.id,q.version]));const last=lastAttempts(attempts.filter(a=>a.version===versions.get(a.id)));let items=pool.filter(q=>!failedOnly||last.get(q.id)?.correct===false);
  // Stable IDs sorted before seeded shuffle: reproducible across reloads of same content version.
  items=items.slice().sort((a,b)=>a.id.localeCompare(b.id));let x=(Number(seed)||1)>>>0;
  for(let i=items.length-1;i>0;i--){x=(Math.imul(1664525,x)+1013904223)>>>0;const j=x%(i+1);[items[i],items[j]]=[items[j],items[i]];}
  return items.slice(0,count==='all'?items.length:Math.max(0,Number(count)||5));
 }
 function summary(questions,attempts){
  const versions=new Map(questions.map(q=>[q.id,q.version]));const current=attempts.filter(a=>a.version===versions.get(a.id));const latest=[...lastAttempts(current).values()];const scored=current.filter(a=>a.correct!==null);
  return {attempts:current.length,percent:scored.length?Math.round(100*scored.filter(a=>a.correct).length/scored.length):null,mastered:latest.filter(a=>a.correct===true).length,pending:questions.length-latest.filter(a=>a.correct===true).length,failed:latest.filter(a=>a.correct===false).map(a=>a.id)};
 }
 return {MODES,courses,cases,grade,migrate,validLearning,schedule,select,summary};
})();
if(typeof module!=='undefined')module.exports=StudyEngine;
