const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const E=require('./learning-engine.js'),content=JSON.parse(fs.readFileSync(__dirname+'/learning-content.json'));
const bank=JSON.parse(require('node:child_process').execFileSync('node',[__dirname+'/scripts/export_bank.cjs']));
assert(bank.every(q=>E.MODES.includes(E.cases[q.id])));
assert(bank.filter(q=>q.c==='program').every(q=>E.cases[q.id]==='DEVELOPMENT'));
assert(bank.filter(q=>q.c==='models').every(q=>E.cases[q.id]==='THEORY'));
assert(['M01','M02','M03','M04','M05','M06','M09','M10'].every(id=>E.cases[id]==='EXTERNAL_TOOL'));
const old={ratings:{P01:2,E03:1},answers:{'single-P01::P01':'print(42)'},history:[{id:'P01',rating:2,date:'2026-11-01'}],activeSession:{id:'legacy'}};
const migrated=E.migrate(old);assert.deepEqual(E.migrate(migrated),migrated);for(const key of Object.keys(old))assert.deepEqual(migrated[key],old[key]);
assert(E.validLearning(migrated.learning));assert(!E.validLearning({...migrated.learning,quiz:{}}));assert(!E.validLearning({version:9,attempts:[],cards:{}}));
for(const q of content.questions){assert(q.id&&q.source.commit&&q.source.path&&q.version&&q.explanation);if(q.type!=='open')assert(E.grade(q,q.answer instanceof Array&&q.type==='term'?q.answer[0]:q.answer).correct,q.id);else assert.equal(E.grade(q,'respuesta cualquiera').correct,null);}
assert.equal(new Set(content.questions.map(q=>q.id)).size,content.questions.length);
assert(E.grade({type:'term',answer:['Defuzzificación','desdifusión']},' DE FUZZ ').correct===false);
assert(E.grade({type:'term',answer:['Defuzzificación','desdifusión']},'defuzzificacion').correct);
assert(E.grade({type:'multiple',answer:[1,3]},[3,1]).correct);
assert(!E.grade({type:'multiple',answer:[1,3]},[1]).correct);
assert(!E.grade({type:'boolean',answer:false},undefined).correct);
const now=1000;assert(E.schedule(null,0,now).due===now+600000);assert(E.schedule(null,1,now).due===now+86400000);assert(E.schedule({streak:2},2,now).due===now+8*86400000);
const pool=content.questions.filter(q=>q.course==='models');for(const n of [5,10,20,30,'all']){const a=E.select(pool,n,23),b=E.select(pool,n,23);assert.deepEqual(a,b);assert.equal(new Set(a.map(q=>q.id)).size,a.length);}
const attempts=[{id:pool[0].id,correct:false,version:1},{id:pool[1].id,correct:false,version:1},{id:pool[0].id,correct:true,version:1}];assert.deepEqual(E.select(pool,5,1,true,attempts).map(q=>q.id),[pool[1].id]);
assert(E.validLearning(JSON.parse(JSON.stringify(migrated)).learning));
const js=fs.readFileSync(__dirname+'/learning-ui.js','utf8');assert(js.includes('result.correct===false'));assert(js.includes("typeof LOCAL_TOOL_TOKEN==='undefined'"));
console.log('PASS modalidades, 106 preguntas, respuestas múltiples, rúbricas, migración, persistencia, repaso y simulacros reproducibles');
